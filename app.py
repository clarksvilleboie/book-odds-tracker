import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [필수] API 키 입력
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="배당 비교 분석기", layout="wide")

# CSS로 표 예쁘게 만들기
st.markdown("""
<style>
    .stDataFrame {font-size: 14px;}
    div[data-testid="stExpander"] details summary p {
        font-weight: bold;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 업체별 배당 비교 (최고 배당 찾기)")

# 1. 설정
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

# 사이드바
sport_type = st.sidebar.radio("종목", list(LEAGUES.keys()))
selected_league_name = st.sidebar.selectbox("리그", list(LEAGUES[sport_type].keys()))
sport_key = LEAGUES[sport_type][selected_league_name]

# 2. 데이터 가져오기 (모든 업체 포함)
def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': api_key,
        'regions': 'us,uk,eu', # 미국, 영국, 유럽 업체 다 가져오기
        'markets': 'h2h', # 승무패 배당 비교
        'oddsFormat': 'decimal',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# 3. 메인 화면
st.subheader(f"{selected_league_name} - 업체별 배당 비교")
st.info("💡 팁: '상세 보기'를 누르면 모든 사이트의 배당을 비교할 수 있습니다.")

if st.button('🔄 배당 비교 데이터 불러오기', type="primary"):
    with st.spinner('전 세계 배당 사이트를 뒤지는 중...'):
        data = get_data(API_KEY, sport_key)
        
        if data:
            now = datetime.now().strftime("%H시 %M분 %S초")
            st.write(f"✅ 업데이트: {now}")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start_time = game['commence_time'][:10] # 날짜만
                
                # 게임 하나를 박스로 묶어서 보여줌 (Expander)
                with st.expander(f"VS | {home} vs {away} ({start_time})"):
                    
                    odds_list = []
                    # 모든 업체의 배당을 수집
                    for bookie in game['bookmakers']:
                        site_name = bookie['title']
                        markets = bookie['markets']
                        
                        # 승무패 찾기
                        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
                        if h2h:
                            outcomes = h2h['outcomes']
                            h_odd = next((x['price'] for x in outcomes if x['name'] == home), 0)
                            a_odd = next((x['price'] for x in outcomes if x['name'] == away), 0)
                            draw_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)
                            
                            row = {
                                '사이트': site_name,
                                f'{home} 승': h_odd,
                                f'{away} 승': a_odd
                            }
                            if draw_odd > 0:
                                row['무승부'] = draw_odd
                                
                            odds_list.append(row)
                    
                    if odds_list:
                        df = pd.DataFrame(odds_list)
                        
                        # 최고 배당 하이라이트 (돈 더 주는 곳 찾기)
                        st.dataframe(
                            df.style.highlight_max(axis=0, color='#fffdc1'), # 가장 높은 숫자에 노란색 칠하기
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("아직 배당이 나온 사이트가 없습니다.")
                        
        else:
            st.error("데이터 불러오기 실패 (키 확인)")
