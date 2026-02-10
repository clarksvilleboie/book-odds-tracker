import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ==========================================
# [필수] 본인의 API 키를 따옴표 안에 넣어주세요
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

# 페이지 설정 (제목 등)
st.set_page_config(page_title="실시간 배당 추적기", layout="wide")
st.title("🏀 NBA 실시간 배당률 흐름 (Live)")

# 설정값
SPORT = 'basketball_nba'
REGIONS = 'us'
MARKETS = 'h2h'

# 데이터가 들어갈 빈 공간을 미리 만듭니다
placeholder = st.empty()

# 과거 배당 정보를 저장할 곳 (세션 상태 사용)
if 'history' not in st.session_state:
    st.session_state['history'] = {}

def get_odds():
    try:
        response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
            params={
                'apiKey': API_KEY,
                'regions': REGIONS,
                'markets': MARKETS,
                'oddsFormat': 'decimal',
            }
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# 메인 루프 (계속 반복)
while True:
    data = get_odds()
    
    with placeholder.container():
        # 현재 시간 표시
        now = datetime.now().strftime("%H시 %M분 %S초")
        st.write(f"🔄 **마지막 업데이트:** {now}")

        if data:
            game_list = []
            for game in data:
                home = game['home_team']
                away = game['away_team']
                
                if game['bookmakers']:
                    # 첫 번째 배당 사이트 기준
                    bookie = game['bookmakers'][0]
                    site = bookie['title']
                    odds = bookie['markets'][0]['outcomes']
                    
                    h_odd = next((x['price'] for x in odds if x['name'] == home), 0)
                    a_odd = next((x['price'] for x in odds if x['name'] == away), 0)
                    
                    # 변동 계산 로직
                    h_change = "-"
                    a_change = "-"
                    
                    # 과거 기록 비교
                    hist = st.session_state['history']
                    
                    if home in hist:
                        diff = h_odd - hist[home]
                        if diff > 0: h_change = f"🔺 +{diff:.2f}"
                        elif diff < 0: h_change = f"🔻 {diff:.2f}"
                    
                    if away in hist:
                        diff = a_odd - hist[away]
                        if diff > 0: a_change = f"🔺 +{diff:.2f}"
                        elif diff < 0: a_change = f"🔻 {diff:.2f}"
                        
                    # 현재 값 저장
                    hist[home] = h_odd
                    hist[away] = a_odd
                    
                    game_list.append({
                        '홈팀': home,
                        '홈팀 배당': h_odd,
                        '홈팀 변동': h_change,
                        '원정팀': away,
                        '원정팀 배당': a_odd,
                        '원정팀 변동': a_change,
                        '사이트': site
                    })
            
            # 표 그리기
            if game_list:
                df = pd.DataFrame(game_list)
                # 중요한 정보만 깔끔하게 보여주기
                st.dataframe(
                    df, 
                    column_config={
                        "홈팀 배당": st.column_config.NumberColumn(format="%.2f"),
                        "원정팀 배당": st.column_config.NumberColumn(format="%.2f"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("현재 예정된 경기가 없거나 데이터가 비어있습니다.")
        else:
            st.error("데이터를 불러오는데 실패했습니다. (API 키 확인 필요)")
            
    # 30초 대기
    time.sleep(30)
