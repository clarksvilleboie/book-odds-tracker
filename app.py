import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키
MY_NICKNAME = "jun lee"
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="Oddsportal Pro", layout="wide")

# 🎨 [UI/UX] 오즈포털 스타일 CSS
st.markdown("""
<style>
    .main { background-color: #ffffff; color: #333333; }
    .header-box {
        background-color: #2c3e50; color: white; padding: 20px;
        text-align: center; border-radius: 0 0 15px 15px; margin-bottom: 25px;
    }
    .table-header {
        background-color: #f1f3f5; border-top: 2px solid #34495e;
        border-bottom: 1px solid #dee2e6; font-weight: bold;
        padding: 12px; font-size: 0.85rem; color: #495057;
    }
    .match-row {
        border-bottom: 1px solid #f0f0f0; padding: 15px 0;
        display: flex; align-items: center;
    }
    .match-row:hover { background-color: #fafafa; }
    .team-logo {
        width: 25px; height: 25px; margin: 0 5px;
        vertical-align: middle; object-fit: contain;
    }
    .odd-box {
        border: 1px solid #e9ecef; border-radius: 3px; padding: 6px 0;
        text-align: center; width: 65px; display: inline-block;
        font-weight: 600; font-size: 0.9rem; background-color: #fcfcfc;
    }
    .best-odd {
        background-color: #fff9c4 !important;
        border-color: #fbc02d !important; color: #000 !important;
    }
    .team-text { font-size: 0.95rem; font-weight: 500; display: flex; align-items: center; }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="header-box"><h1>Oddsportal Pro</h1><p>Developed by {MY_NICKNAME}</p></div>', unsafe_allow_html=True)

# 🖼️ 로고 가져오기
def get_logo(team_name):
    clean_name = team_name.replace(" ", "").lower()
    return f"https://logo.clearbit.com/{clean_name}.com?size=50"

# 리그 설정
LEAGUES = {
    "Football (Soccer)": {
        "EPL (영국)": "soccer_epl",
        "라리가 (스페인)": "soccer_spain_la_liga",
        "분데스리가 (독일)": "soccer_germany_bundesliga",
        "세리에A (이탈리아)": "soccer_italy_serie_a"
    },
    "Basketball": {"NBA": "basketball_nba"}
}

with st.sidebar:
    st.header("🏆 Menu")
    sport_type = st.radio("Sports", list(LEAGUES.keys()))
    league_name = st.selectbox("Select League", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][league_name]

# VIP 업체
VIP_BOOKIES = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pinnacle']

if st.button('🔄 Update Real-time Odds', type="primary", use_container_width=True):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': API_KEY, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        st.markdown("""
        <div class="table-header">
            <div style="display: flex; justify-content: space-between; text-align: center;">
                <div style="width: 10%;">Time</div>
                <div style="width: 45%; text-align: left;">Match</div>
                <div style="width: 15%;">1</div>
                <div style="width: 15%;">X</div>
                <div style="width: 15%;">2</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for game in data:
            home, away = game['home_team'], game['away_team']
            start_time = game['commence_time'][11:16]
            
            # 배당 추출 및 최고값 계산
            best_h, best_d, best_a = 0, 0, 0
            for b in game['bookmakers']:
                if b['key'] in VIP_BOOKIES:
                    h2h = next((m for m in b['markets'] if m['key'] == 'h2h'), None)
                    if h2h:
                        h = next((x['price'] for x in h2h['outcomes'] if x['name'] == home), 0)
                        a = next((x['price'] for x in h2h['outcomes'] if x['name'] == away), 0)
                        d = next((x['price'] for x in h2h['outcomes'] if x['name'] == 'Draw'), 0)
                        best_h = max(best_h, h)
                        best_d = max(best_d, d)
                        best_a = max(best_a, a)

            # 💡 [해결 방법] 에러가 나던 출력값을 미리 문자열로 만듭니다.
            h_val = f"{best_h:.2f}" if best_h > 0 else "-"
            d_val = f"{best_d:.2f}" if best_d > 0 else "-"
            a_val = f"{best_a:.2f}" if best_a > 0 else "-"
            
            # 클래스 지정
            h_class = "best-odd" if best_h > 0 else ""
            d_class = "best-odd" if best_d > 0 else ""
            a_class = "best-odd" if best_a > 0 else ""

            # 로고 경로
            home_logo = get_logo(home)
            away_logo = get_logo(away)
            default_img = "https://cdn-icons-png.flaticon.com/512/53/53254.png"

            st.markdown(f"""
            <div class="match-row">
                <div style="width: 10%; color: #999; font-size: 0.8rem; text-align: center;">{start_time}</div>
                <div style="width: 45%;" class="team-text">
                    <img src="{home_logo}" class="team-logo" onerror="this.src='{default_img}'">
                    {home} - {away}
                    <img src="{away_logo}" class="team-logo" onerror="this.src='{default_img}'">
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {h_class}">{h_val}</span>
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {d_class}">{d_val}</span>
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {a_class}">{a_val}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("API 응답 에러")
