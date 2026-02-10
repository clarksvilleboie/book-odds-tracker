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

# 🎨 [UI/UX] 오즈포털 스타일 최종 정돈
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
        display: flex; align-items: center; justify-content: space-between;
    }
    .team-section { display: flex; align-items: center; width: 45%; font-weight: 500; font-size: 0.95rem; }
    .team-logo {
        width: 24px; height: 24px; margin: 0 8px;
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
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="header-box"><h1>Oddsportal Pro</h1><p>Developed by {MY_NICKNAME}</p></div>', unsafe_allow_html=True)

# 🖼️ [수정] 더 정확한 로고 검색 엔진 사용
def get_logo(team_name):
    # 팀 이름에서 공백을 '-'로 바꾸어 검색 최적화
    search_name = team_name.replace(" ", "-").lower()
    # 1순위: FootyStats 서버 (축구 전용)
    return f"https://api.sofascore.app/api/v1/team/{search_name}/image" 

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
    st.header("🏆 League")
    sport_type = st.radio("Sports", list(LEAGUES.keys()))
    league_name = st.selectbox("Select", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][league_name]

# VIP 업체
VIP_BOOKIES = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pinnacle']

if st.button('🔄 Update Real-time Odds', type="primary", use_container_width=True):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': API_KEY, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    res = requests.get(url, params=params)
    
    if res.status_code == 200:
        data = res.json()
        
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
            
            # 배당 계산
            best_h, best_d, best_a = 0, 0, 0
            for b in game['bookmakers']:
                if b['key'] in VIP_BOOKIES:
                    h2h = next((m for m in b['markets'] if m['key'] == 'h2h'), None)
                    if h2h:
                        h = next((x['price'] for x in h2h['outcomes'] if x['name'] == home), 0)
                        a = next((x['price'] for x in h2h['outcomes'] if x['name'] == away), 0)
                        d = next((x['price'] for x in h2h['outcomes'] if x['name'] == 'Draw'), 0)
                        best_h, best_d, best_a = max(best_h, h), max(best_d, d), max(best_a, a)

            # 출력용 텍스트/클래스
            h_val, d_val, a_val = f"{best_h:.2f}", f"{best_d:.2f}" if best_d > 0 else "-", f"{best_a:.2f}"
            h_cls = "best-odd" if best_h > 0 else ""
            d_cls = "best-odd" if best_d > 0 else ""
            a_cls = "best-odd" if best_a > 0 else ""

            # 로고 예외 처리 (이미지 없으면 빈칸 처리)
            # 💡 [핵심] Google 검색 썸네일 엔진을 활용하여 깨짐 방지
            home_logo = f"https://www.google.com/s2/favicons?domain={home.replace(' ', '')}.com&sz=32"
            away_logo = f"https://www.google.com/s2/favicons?domain={away.replace(' ', '')}.com&sz=32"
            
            # 💡 [백업] 축구 전용 로고 서비스로 교체
            home_logo = f"https://api.dicebear.com/7.x/identicon/svg?seed={home}" # 임시: 깨짐 방지용 유니크 아이콘
            
            # 실제 팀 이름을 이용한 로고 (Wikipedia 등 오픈 데이터 활용)
            st.markdown(f"""
            <div class="match-row">
                <div style="width: 10%; color: #999; font-size: 0.8rem; text-align: center;">{start_time}</div>
                <div class="team-section">
                    <span style="font-size: 1.2rem; margin-right: 5px;">⚽</span>
                    {home} - {away}
                    <span style="font-size: 1.2rem; margin-left: 5px;">⚽</span>
                </div>
                <div style="width: 15%; text-align: center;"><span class="odd-box {h_cls}">{h_val}</span></div>
                <div style="width: 15%; text-align: center;"><span class="odd-box {d_cls}">{d_val}</span></div>
                <div style="width: 15%; text-align: center;"><span class="odd-box {a_cls}">{a_val}</span></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("데이터 로드 실패")
