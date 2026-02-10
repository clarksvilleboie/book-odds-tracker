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

# 🎨 [UI/UX] 오즈포털 스타일 고도화 CSS
st.markdown("""
<style>
    .main { background-color: #ffffff; color: #333333; }
    .header-box {
        background-color: #2c3e50; color: white; padding: 20px;
        text-align: center; border-radius: 0 0 15px 15px; margin-bottom: 25px;
    }
    /* 테이블 헤더 */
    .table-header {
        background-color: #f1f3f5; border-top: 2px solid #34495e;
        border-bottom: 1px solid #dee2e6; font-weight: bold;
        padding: 12px; font-size: 0.85rem; color: #495057;
    }
    /* 경기 행 */
    .match-row {
        border-bottom: 1px solid #f0f0f0; padding: 15px 0;
        display: flex; align-items: center;
    }
    .match-row:hover { background-color: #fafafa; }
    
    /* 로고 이미지 스타일 */
    .team-logo {
        width: 22px; height: 22px; margin-right: 8px;
        vertical-align: middle; object-fit: contain;
    }

    /* 배당 박스 */
    .odd-box {
        border: 1px solid #e9ecef; border-radius: 3px; padding: 6px 0;
        text-align: center; width: 65px; display: inline-block;
        font-weight: 600; font-size: 0.9rem; background-color: #fcfcfc;
    }
    .best-odd {
        background-color: #fff9c4 !important; /* 오즈포털 시그니처 노란색 */
        border-color: #fbc02d !important; color: #000 !important;
    }
    
    /* 텍스트 정렬 */
    .team-text { font-size: 0.95rem; font-weight: 500; display: flex; align-items: center; }
</style>
""", unsafe_allow_html=True)

# 상단 타이틀
st.markdown(f'<div class="header-box"><h1>Oddsportal Style Tracker</h1><p>Professional Betting Interface by {MY_NICKNAME}</p></div>', unsafe_allow_html=True)

# 🖼️ 팀 로고 가져오는 함수 (자동화)
def get_logo(team_name):
    # 팀 이름을 기반으로 로고를 검색해주는 무료 CDN 활용
    # 로고가 없을 경우를 대비해 투명 배경 이미지를 기본값으로 설정
    clean_name = team_name.replace(" ", "").lower()
    return f"https://logo.clearbit.com/{clean_name}.com?size=50"

# 리그 설정
LEAGUES = {
    "Football (Soccer)": {
        "EPL (영국)": "soccer_epl",
        "라리가 (스페인)": "soccer_spain_la_liga",
        "분데스리가 (독일)": "soccer_germany_bundesliga",
        "세리에A (이탈리아)": "soccer_italy_serie_a",
        "챔피언스리그": "soccer_uefa_champs_league"
    },
    "Basketball": {"NBA": "basketball_nba"}
}

with st.sidebar:
    st.header("🏆 League Menu")
    sport_type = st.radio("Sports", list(LEAGUES.keys()))
    league_name = st.selectbox("Select League", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][league_name]

# 데이터 호출 함수
def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': api_key, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        res = requests.get(url, params=params)
        return res.json() if res.status_code == 200 else None
    except: return None

# 실행
if st.button('🔄 Update Real-time Odds', type="primary", use_container_width=True):
    data = get_data(API_KEY, sport_key)
    
    if data:
        # 가로 헤더 구성
        st.markdown("""
        <div class="table-header">
            <div style="display: flex; justify-content: space-between; text-align: center;">
                <div style="width: 10%;">Time</div>
                <div style="width: 45%; text-align: left;">Match</div>
                <div style="width: 15%;">1 (Home)</div>
                <div style="width: 15%;">X (Draw)</div>
                <div style="width: 15%;">2 (Away)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for game in data:
            home, away = game['home_team'], game['away_team']
            start_time = game['commence_time'][11:16]
            
            # 최고 배당 찾기
            best_h, best_d, best_a = 0, 0, 0
            for b in game['bookmakers']:
                h2h = next((m for m in b['markets'] if m['key'] == 'h2h'), None)
                if h2h:
                    h = next((x['price'] for x in h2h['outcomes'] if x['name'] == home), 0)
                    a = next((x['price'] for x in h2h['outcomes'] if x['name'] == away), 0)
                    d = next((x['price'] for x in h2h['outcomes'] if x['name'] == 'Draw'), 0)
                    if h > best_h: best_h = h
                    if d > best_d: best_d = d
                    if a > best_a: best_a = a

            # 로고 URL (축구/농구 범용)
            home_logo = get_logo(home)
            away_logo = get_logo(away)

            # 경기 행 출력 (로고 포함)
            st.markdown(f"""
            <div class="match-row">
                <div style="width: 10%; color: #999; font-size: 0.8rem; text-align: center;">{start_time}</div>
                <div style="width: 45%;" class="team-text">
                    <img src="{home_logo}" class="team-logo" onerror="this.src='https://cdn-icons-png.flaticon.com/512/53/53254.png'">
                    {home} - {away}
                    <img src="{away_logo}" class="team-logo" style="margin-left: 8px;" onerror="this.src='https://cdn-icons-png.flaticon.com/512/53/53254.png'">
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {'best-odd' if best_h > 0 else ''}">{best_h:.2f}</span>
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {'best-odd' if best_d > 0 else ''}">{best_d:.2f if best_d > 0 else '-'}</span>
                </div>
                <div style="width: 15%; text-align: center;">
                    <span class="odd-box {'best-odd' if best_a > 0 else ''}">{best_a:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 상세 업체 (오즈포털 하위 리스트 느낌)
            with st.expander(f"View all 15 bookmakers for {home} vs {away}"):
                st.write("### Market Comparison")
                # ... (업체별 상세 표는 기존 st.table 또는 st.dataframe 유지)
    else:
        st.error("데이터 로드에 실패했습니다. API 키를 확인하세요.")
