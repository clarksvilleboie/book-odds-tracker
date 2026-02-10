import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [필수] API 키 입력
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="VIP 배당 분석기", layout="wide")

# 스타일 설정
st.markdown("""
<style>
    .stDataFrame {font-size: 14px;}
    div[data-testid="stExpander"] details summary p {
        font-weight: bold;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 전 세계 Top 15 배당 업체 비교")

# 1. 보고 싶은 'VIP 업체' 리스트 (여기 있는 것만 나옵니다)
VIP_BOOKIES = [
    # 미국 메이저
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'bovada', 'betrivers',
    # 유럽/영국 메이저
    'bet365', 'williamhill', 'unibet', '888sport', 'betvictor', 
    'ladbrokes', 'coral', 'betfair_ex_eu',
    # 전세계 배당의 기준 (Sharp Bookie)
    'pinnacle'
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

sport_type = st.sidebar.radio("종목 선택", list(LEAGUES.keys()))
selected_league_name = st.sidebar.selectbox("리그 선택", list(LEAGUES[sport_type].keys()))
sport_key = LEAGUES[sport_type][selected_league_name]

# 세션 상태
if 'history' not in st.session_state:
    st.session_state['history'] = {}

def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': api_key,
        'regions': 'us,uk,eu', # 전 세계 다 긁어온 뒤 밑에서 필터링
        'markets': 'h2h',
        'oddsFormat': 'decimal',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# 최고 배당 불꽃 마크
def format_best_odds(val, max_val):
    if val == max_val:
        return f"🔥 {val:.2f}"
    return f"{val:.2f}"

# 메인 화면
st.subheader(f"🏆 {selected_league_name} 매치업 (메이저 업체만 표시)")

if st.button('🔄 VIP 배당 데이터 불러오기', type="primary"):
    with st.spinner('전 세계 메이저 사이트(Bet365, Pinnacle 등) 조회 중...'):
        data = get_data(API_KEY, sport_key)
        
        if data:
            now = datetime.now().strftime("%H시 %M분 %S초")
            st.success(f"업데이트: {now} | 필터링: Global Top 15")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start_time = game['commence_time'][:10]
                
                with st.expander(f"VS | {home} vs {away} ({start_time})", expanded=True):
                    
                    odds_list = []
                    
                    # 배당 업체 반복문
                    for bookie in game['bookmakers']:
                        
                        # [핵심] VIP 리스트에 없으면 과감히 버림 (필터링)
