import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키를 적어주세요
MY_NICKNAME = "Clarksville boy"  # <-- 여기에 본인 닉네임 입력!
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918' # <-- API 키 입력
# ==========================================

st.set_page_config(page_title="Odds Tracker", layout="wide")

# 🎨 [디자인] CSS로 꾸미기 (타이틀, 서명, 표 스타일)
st.markdown("""
<style>
    /* 메인 타이틀 스타일 */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #1E1E1E;
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px #cccccc;
    }
    /* 서브 타이틀 (닉네임) 스타일 */
    .sub-title {
        font-size: 1.2rem;
        color: #555555;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 30px;
        font-style: italic;
    }
    /* 표 스타일 조정 */
    .stDataFrame {font-size: 14px;}
    div[data-testid="stExpander"] details summary p {
        font-weight: bold;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

# 🏆 [화면 구성] 메인 타이틀 출력
st.markdown('<p class="main-title">Sports Bookmaker Odds Tracker</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Developed by {MY_NICKNAME}</p>', unsafe_allow_html=True)

# 구분선
st.markdown("---")

# 1. VIP 업체 리스트
VIP_BOOKIES = [
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'bovada', 'betrivers', # 미국
    'bet365', 'williamhill', 'unibet', '888sport', 'betvictor', # 영국/유럽
    'ladbrokes', 'coral', 'betfair_ex_eu',
    'pinnacle' # 기준점
]

# 2. 리그 설정
LEAGUES = {
    "축구 (Soccer)": {
        "EPL (영국)": "soccer_epl",
        "라리가 (스페인)": "soccer_spain_la_liga",
        "분데스리가 (독일)": "soccer_germany_bundesliga",
        "세리에A (이탈리아)": "soccer_italy_serie_a",
        "챔피언스리그": "soccer_uefa_champs_league"
    },
    "농구 (Basketball)": {
        "NBA (미국)": "basketball_nba"
    },
    "야구 (Baseball)": {
        "MLB (미국)": "baseball_mlb"
    }
}

# 사이드바 메뉴
with st.sidebar:
    st.header("🔍 필터 설정")
    sport_type = st.radio("종목 선택", list(LEAGUES.keys()))
    selected_league_name = st.selectbox("리그 선택", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][selected_league_name]
    st.info(f"현재 선택: **{selected_league_name}**")

# 세션 상태
if 'history' not in st.session_state:
    st.session_state['history'] = {}

def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': api_key,
        'regions': 'us,uk,eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def format_best_odds(val, max_val):
    if val == max_val:
        return f"🔥 {val:.2f}"
    return f"{val:.2f}"

def calculate_change(current_val, unique_id):
    history = st.session_state['history']
    change_text = ""
    if unique_id in history:
        diff = current_val - history[unique_id]
        if diff > 0.001:
            change_text = f"🔺{diff:.2f}"
        elif diff < -0.001:
            change_text = f"🔻{abs(diff):.2f}"
    history[unique_id] = current_val
    return change_text

# 메인 기능 버튼
col1, col2, col3 = st.columns([1, 2, 1]) # 버튼을 중앙에 예쁘게 배치하기 위함
with col2:
    refresh_btn = st.button('🔄 실시간 배당 데이터 가져오기 (Click)', type="primary", use_container_width=True)

if refresh_btn:
    with st.spinner(f'{selected_league_name} 데이터를 분석 중입니다...'):
        data = get_data(API_KEY, sport_key)
        
        if data:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"✅ 업데이트 완료: {now} | Target: Global Top 15 Bookies")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start_time = game['commence_time'][:10]
                
                with st.expander(f"VS | {home} vs {away} ({start_time})", expanded=True):
                    odds_list = []
                    for bookie in game['bookmakers']:
                        if bookie['key'] not in VIP_BOOKIES:
                            continue
                        
                        site_name = bookie['title']
                        markets = bookie['markets']
                        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
                        
                        if h2h:
                            outcomes = h2h['outcomes']
                            h_odd = next((x['price'] for x in outcomes if x['name'] == home), 0)
                            a_odd = next((x['price'] for x in outcomes if x['name'] == away), 0)
                            draw_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)
                            
                            # 변동 계산
                            h_chg = calculate_change(h_odd, f"{site_name}_{home}")
                            a_chg = calculate_change(a_odd, f"{site_name}_{away}")
                            d_chg = calculate_change(draw_odd, f"{site_name}_Draw_{home}")
                            
                            row = {
                                '사이트': site_name,
                                '홈_raw': h_odd,
                                '원정_raw': a_odd,
                                '무_raw': draw_odd,
                                '변동(홈)': h_chg,
                                '변동(원정)': a_chg,
                                '변동(무)': d_chg
                            }
                            odds_list.append(row)
                    
                    if odds_list:
                        df = pd.DataFrame(odds_list)
                        max_home = df['홈_raw'].max()
                        max_away = df['원정_raw'].max()
                        max_draw = df['무_raw'].max() if '무_raw' in df.columns else 0
                        
                        df['홈 승
