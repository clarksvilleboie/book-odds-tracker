import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키를 적어주세요
MY_NICKNAME = "Betting Master"
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="Odds History Tracker", layout="wide")

# 스타일
st.markdown("""
<style>
    .main-title {font-size: 3rem; font-weight: 800; text-align: center; margin-bottom: 0px;}
    .sub-title {font-size: 1.2rem; text-align: center; color: #555; margin-bottom: 20px;}
    /* 변동 내역 스타일 */
    .history-log {
        font-size: 0.9rem;
        color: #333;
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<p class="main-title">Sports Odds History</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Developed by {MY_NICKNAME}</p>', unsafe_allow_html=True)

# VIP 리스트
VIP_BOOKIES = [
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'bovada', 'betrivers',
    'bet365', 'williamhill', 'unibet', '888sport', 'pinnacle'
]

# 리그 설정
LEAGUES = {
    "축구": {"EPL": "soccer_epl", "라리가": "soccer_spain_la_liga", "분데스": "soccer_germany_bundesliga", "세리에A": "soccer_italy_serie_a", "챔스": "soccer_uefa_champs_league"},
    "농구": {"NBA": "basketball_nba"},
    "야구": {"MLB": "baseball_mlb"}
}

# 사이드바
with st.sidebar:
    st.header("🔍 설정")
    sport_type = st.radio("종목", list(LEAGUES.keys()))
    league_name = st.selectbox("리그", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][league_name]
    
    if st.button("🗑️ 모든 기록 초기화"):
        st.session_state['match_logs'] = {}
        st.success("초기화 완료")

# [핵심] 기록장 (세션 상태)
if 'match_logs' not in st.session_state:
    st.session_state['match_logs'] = {}

def get_data(api_key, sport_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': api_key, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def format_change(current, old):
    diff = current - old
    if diff > 0.001: return f"(🔺+{diff:.2f})"
    elif diff < -0.001: return f"(🔻{diff:.2f})"
    return "(-)"

# 메인 버튼
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    refresh = st.button('🔄 실시간 변동 내역 가져오기', type="primary", use_container_width=True)

if refresh:
    with st.spinner('배당 흐름 분석 중...'):
        data = get_data(API_KEY, sport_key)
        
        if data:
            now_str = datetime.now().strftime("%H:%M") # 시:분
            st.success(f"업데이트: {now_str}")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start = game['commence_time'][11:16] # 경기 시간
                match_id = f"{home} vs {away}"
                
                # 기록장 생성
                if match_id not in st.session_state['match_logs']:
                    st.session_state['match_logs'][match_id] = []

                # 최고 배당 찾기
                best_home, best_away = 0, 0
                
                for bookie in game['bookmakers']:
                    if bookie['key'] not in VIP_BOOKIES: continue
                    h2h = next((m for m in bookie['markets'] if m['key'] == 'h2h'), None)
                    if h2h:
                        h = next((x['price'] for x in h2h['outcomes'] if x['name'] == home), 0)
                        a = next((x['price'] for x in h2h['outcomes'] if x['name'] == away), 0)
                        if h > best_home: best_home = h
                        if a > best_away: best_away = a
                
                # 기록 저장 로직 (값이 변했거나, 첫 기록일 때만 저장)
                logs = st.session_state['match_logs'][match_id]
                should_save = False
                
                if not logs: # 첫 기록이면 저장
                    should_save = True
                else:
                    last_log = logs[-1]
                    # 배당이 0.01이라도 변했으면 저장
                    if abs(last_log['home'] - best_home) > 0.001 or abs(last_log['away'] - best_away) > 0.001:
                        should_save = True
                
                if should_save and best_home > 0:
                    logs.append({'time': now_str, 'home': best_home, 'away': best_away})
                
                # 화면 표시
                with st.expander(f"VS | {match_id} ({start})", expanded=True):
                    # 1. 현재 최고 배당 (크게 보여주기)
                    c1, c2 = st.columns(2)
                    c1.metric(f"🏠 {home} (Home)", f"{best_home:.2f}")
                    c2.metric(f"✈️ {away} (Away)", f"{best_away:.2f}")
                    
                    # 2. 📜 변동 내역 (Log) 출력
                    st.markdown("---")
                    st.caption(f"📉 실시간 배당 변화 히스토리 (최근 {len(logs)}건)")
                    
                    history_text = ""
                    # 최신순으로 보여주기 (거꾸로)
                    for i in range(len(logs)-1, -1, -1):
                        log = logs[i]
                        
                        # 변동폭 계산 (바로 이전 기록과 비교)
                        h_diff_str, a_diff_str = "", ""
                        if i > 0:
                            prev = logs[i-1]
                            h_diff_str = format_change(log['home'], prev['home'])
                            a_diff_str = format_change(log['away'], prev['away'])
                        else:
                            h_diff_str = "(기준점)"
                            a_diff_str = "(기준점)"
                            
                        # 한 줄 출력
                        history_text += f"⏱️ **{log['time']}** | 홈: {log['home']:.2f} {h_diff_str}  vs  원정: {log['away']:.2f} {a_diff_str}\n\n"
                    
                    # 예쁜 박스 안에 내역 넣기
                    st.info(history_text)

        else:
            st.error("데이터 없음 (API 키 확인)")
