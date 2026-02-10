import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [필수] API 키 다시 넣어주세요
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

# 페이지 설정
st.set_page_config(page_title="실시간 배당 추적기", layout="wide")
st.title("🏀 NBA 배당률 조회 (수동 업데이트)")

# 설정값
SPORT = 'basketball_nba'
REGIONS = 'us'
MARKETS = 'h2h'

# 세션 상태 초기화 (과거 기록 저장용)
if 'history' not in st.session_state:
    st.session_state['history'] = {}

# 데이터 가져오는 함수
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

# ==========================================
# [변경점] 버튼을 눌러야만 실행됩니다
if st.button('🔄 최신 배당 불러오기 (클릭)', type="primary"):
    with st.spinner('데이터를 가져오는 중...'):
        data = get_odds()
        
        # 현재 시간
        now = datetime.now().strftime("%H시 %M분 %S초")
        st.write(f"✅ **업데이트 완료:** {now}")

        if data:
            game_list = []
            for game in data:
                home = game['home_team']
                away = game['away_team']
                
                if game['bookmakers']:
                    bookie = game['bookmakers'][0]
                    site = bookie['title']
                    odds = bookie['markets'][0]['outcomes']
                    
                    h_odd = next((x['price'] for x in odds if x['name'] == home), 0)
                    a_odd = next((x['price'] for x in odds if x['name'] == away), 0)
                    
                    # 변동 계산
                    h_change = "-"
                    a_change = "-"
                    hist = st.session_state['history']
                    
                    if home in hist:
                        diff = h_odd - hist[home]
                        if diff > 0: h_change = f"🔺 +{diff:.2f}"
                        elif diff < 0: h_change = f"🔻 {diff:.2f}"
                    
                    if away in hist:
                        diff = a_odd - hist[away]
                        if diff > 0: a_change = f"🔺 +{diff:.2f}"
                        elif diff < 0: a_change = f"🔻 {diff:.2f}"
                        
                    # 저장
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
            
            # 표 출력
            if game_list:
                df = pd.DataFrame(game_list)
                st.dataframe(
                    df, 
                    column_config={
                        "홈팀 배당": st.column_config.NumberColumn(format="%.2f"),
                        "원정팀 배당": st.column_config.NumberColumn(format="%.2f"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 남은 횟수 (대략적인 계산)
                st.info("💡 팁: 버튼을 누를 때마다 무료 횟수가 1회 차감됩니다.")
            else:
                st.info("경기 데이터가 없습니다.")
        else:
            st.error("데이터 가져오기 실패! (키 확인 필요)")
else:
    st.write("👆 위의 버튼을 눌러 데이터를 불러오세요.")
