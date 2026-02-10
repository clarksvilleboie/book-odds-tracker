import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키 (꼭 본인껄로 채우세요!)
MY_NICKNAME = "jun lee" 
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918' 
# ==========================================

st.set_page_config(page_title="Odds Flow Pro", layout="wide")

# 🎨 [UI/UX] 전문가용 다크 네이비 테마 CSS
st.markdown("""
<style>
    .main { background-color: #0E1117; color: #E0E0E0; }
    .main-title {
        font-size: 3rem; font-weight: 900; text-align: center;
        background: linear-gradient(90deg, #00B4D8, #90E0EF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem; text-align: center; color: #8892B0;
        margin-top: -10px; margin-bottom: 30px;
    }
    .stExpander {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] details summary p {
        color: #00B4D8 !important; font-weight: bold;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077B6, #00B4D8);
        color: white; border: none; border-radius: 8px; font-weight: bold;
        height: 3em; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Odds Flow Pro</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Developed by {MY_NICKNAME} | Real-time Analysis</p>', unsafe_allow_html=True)

# 🏀 [NBA 로고 매핑]
NBA_LOGOS = {
    "Atlanta Hawks": "atl", "Boston Celtics": "bos", "Brooklyn Nets": "bkn",
    "Charlotte Hornets": "cha", "Chicago Bulls": "chi", "Cleveland Cavaliers": "cle",
    "Dallas Mavericks": "dal", "Denver Nuggets": "den", "Detroit Pistons": "det",
    "Golden State Warriors": "gsw", "Houston Rockets": "hou", "Indiana Pacers": "ind",
    "Los Angeles Clippers": "lac", "Los Angeles Lakers": "lal", "Memphis Grizzlies": "mem",
    "Miami Heat": "mia", "Milwaukee Bucks": "mil", "Minnesota Timberwolves": "min",
    "New Orleans Pelicans": "nop", "New York Knicks": "nyk", "Oklahoma City Thunder": "okc",
    "Orlando Magic": "orl", "Philadelphia 76ers": "phi", "Phoenix Suns": "phx",
    "Portland Trail Blazers": "por", "Sacramento Kings": "sac", "San Antonio Spurs": "sas",
    "Toronto Raptors": "tor", "Utah Jazz": "uta", "Washington Wizards": "was"
}

def get_team_logo(team_name, sport):
    if "basketball" in sport:
        code = NBA_LOGOS.get(team_name)
        if code: return f"https://a.espncdn.com/i/teamlogos/nba/500/{code}.png"
        return "🏀"
    return "⚽"

# VIP 업체 리스트
VIP_BOOKIES = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pinnacle']

# 리그 설정
LEAGUES = {
    "농구 (Basketball)": {"NBA": "basketball_nba"},
    "축구 (Soccer)": {"EPL": "soccer_epl", "라리가": "soccer_spain_la_liga"}
}

with st.sidebar:
    st.header("🔍 필터 설정")
    sport_type = st.radio("종목 선택", list(LEAGUES.keys()))
    league_name = st.selectbox("리그 선택", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][league_name]

if 'match_logs' not in st.session_state: st.session_state['match_logs'] = {}

def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': api_key, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        res = requests.get(url, params=params)
        return res.json() if res.status_code == 200 else None
    except: return None

# 중앙 버튼
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    refresh = st.button('🔄 실시간 데이터 동기화 시작', type="primary")

if refresh:
    data = get_data(API_KEY, sport_key)
    if data:
        st.toast("성공적으로 데이터를 읽어왔습니다!")
        for game in data:
            home, away = game['home_team'], game['away_team']
            start = game['commence_time'][11:16]
            
            with st.expander(f"📍 {home} vs {away} (시작 {start})", expanded=True):
                # 로고 배치
                c1, c2, c3 = st.columns([1, 0.4, 1])
                with c1:
                    logo = get_team_logo(home, sport_key)
                    if logo.startswith("http"): st.image(logo, width=80)
                    else: st.markdown(f"### {logo}")
                    st.markdown(f"**{home}**")
                with c2: st.markdown("<h2 style='text-align:center; padding-top:20px;'>VS</h2>", unsafe_allow_html=True)
                with c3:
                    logo = get_team_logo(away, sport_key)
                    if logo.startswith("http"): st.image(logo, width=80)
                    else: st.markdown(f"### {logo}")
                    st.markdown(f"**{away}**")
                
                # 배당 데이터 가공
                rows = []
                for bookie in game['bookmakers']:
                    if bookie['key'] in VIP_BOOKIES:
                        h2h = next((m for m in bookie['markets'] if m['key'] == 'h2h'), None)
                        if h2h:
                            outcomes = h2h['outcomes']
                            h_odd = next((x['price'] for x in outcomes if x['name'] == home), 0)
                            a_odd = next((x['price'] for x in outcomes if x['name'] == away), 0)
                            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)
                            rows.append({'사이트': bookie['title'], '홈 승': h_odd, '무': d_odd if d_odd > 0 else "-", '원정 승': a_odd})
                
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("주요 업체의 배당 데이터가 아직 없습니다.")
