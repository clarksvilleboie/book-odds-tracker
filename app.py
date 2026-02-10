import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키를 적어주세요
MY_NICKNAME = "jun lee"
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="Odds Flow Tracker", layout="wide")

# 스타일 설정
st.markdown("""
<style>
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #1E1E1E;
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px #cccccc;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #555555;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 30px;
        font-style: italic;
    }
    .stDataFrame {font-size: 14px;}
    div[data-testid="stExpander"] details summary p {
        font-weight: bold;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<p class="main-title">Sports Odds Flow Tracker</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Developed by {MY_NICKNAME}</p>', unsafe_allow_html=True)
st.markdown("---")

# VIP 업체 리스트
VIP_BOOKIES = [
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'bovada', 'betrivers',
    'bet365', 'williamhill', 'unibet', '888sport', 'betvictor',
    'ladbrokes', 'coral', 'betfair_ex_eu', 'pinnacle'
]

# 리그 설정
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
with st.sidebar:
    st.header("🔍 필터 설정")
    sport_type = st.radio("종목 선택", list(LEAGUES.keys()))
    selected_league_name = st.selectbox("리그 선택", list(LEAGUES[sport_type].keys()))
    sport_key = LEAGUES[sport_type][selected_league_name]
    st.info(f"현재 선택: **{selected_league_name}**")
    
    # 데이터 초기화 버튼 (너무 많이 쌓이면 누르세요)
    if st.button("🗑️ 기록 초기화"):
        st.session_state['odds_history'] = {}
        st.session_state['prev_history'] = {}
        st.success("모든 기록이 삭제되었습니다.")

# 세션 상태 초기화
if 'odds_history' not in st.session_state:
    st.session_state['odds_history'] = {}  # 그래프용 전체 기록
if 'prev_history' not in st.session_state:
    st.session_state['prev_history'] = {}  # 화살표용 직전 기록

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
    prev_hist = st.session_state['prev_history']
    change_text = ""
    if unique_id in prev_hist:
        diff = current_val - prev_hist[unique_id]
        if diff > 0.001:
            change_text = f"🔺{diff:.2f}"
        elif diff < -0.001:
            change_text = f"🔻{abs(diff):.2f}"
    prev_hist[unique_id] = current_val
    return change_text

# 메인 버튼
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    refresh_btn = st.button('🔄 실시간 배당 데이터 가져오기 (Click)', type="primary", use_container_width=True)

if refresh_btn:
    with st.spinner(f'{selected_league_name} 데이터를 분석 중입니다...'):
        data = get_data(API_KEY, sport_key)
        
        if data:
            now_str = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ 업데이트 완료: {now_str}")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start_time = game['commence_time'][:10]
                match_id = f"{home} vs {away}" # 경기 고유 ID
                
                with st.expander(f"VS | {match_id} ({start_time})", expanded=True):
                    odds_list = []
                    
                    # 최고 배당 추적용 변수
                    best_home_odd = 0
                    best_away_odd = 0
                    
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
                            
                            # 최고 배당 갱신
                            if h_odd > best_home_odd: best_home_odd = h_odd
                            if a_odd > best_away_odd: best_away_odd = a_odd
                            
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
                    
                    # 1. 그래프용 데이터 저장 (최고 배당 기준)
                    if match_id not in st.session_state['odds_history']:
                        st.session_state['odds_history'][match_id] = []
                    
                    # 현재 시간의 최고 배당을 기록
                    if best_home_odd > 0 and best_away_odd > 0:
                        st.session_state['odds_history'][match_id].append({
                            'Time': now_str,
                            f'{home} (홈)': best_home_odd,
                            f'{away} (원정)': best_away_odd
                        })

                    # 2. 그래프 그리기 (데이터가 2개 이상일 때부터)
                    history_data = st.session_state['odds_history'][match_id]
                    if len(history_data) > 1:
                        st.caption("📈 실시간 최고 배당 흐름 (버튼을 누를 때마다 기록됩니다)")
                        chart_df = pd.DataFrame(history_data).set_index('Time')
                        st.line_chart(chart_df)
                    
                    # 3. 상세 표 그리기
                    if odds_list:
                        df = pd.DataFrame(odds_list)
                        max_home = df['홈_raw'].max()
                        max_away = df['원정_raw'].max()
                        max_draw = df['무_raw'].max() if '무_raw' in df.columns else 0
                        
                        df['홈 승 (Home)'] = df.apply(lambda x: f"{format_best_odds(x['홈_raw'], max_home)} {x['변동(홈)']}", axis=1)
                        df['원정 승 (Away)'] = df.apply(lambda x: f"{format_best_odds(x['원정_raw'], max_away)} {x['변동(원정)']}", axis=1)
                        
                        if max_draw > 0:
                            df['무승부 (Draw)'] = df.apply(lambda x: f"{format_best_odds(x['무_raw'], max_draw)} {x['변동(무)']}", axis=1)
                            cols = ['사이트', '홈 승 (Home)', '무승부 (Draw)', '원정 승 (Away)']
                        else:
                            cols = ['사이트', '홈 승 (Home)', '원정 승 (Away)']
                            
                        st.dataframe(df[cols], use_container_width=True, hide_index=True)
                    else:
                        st.warning("배당 데이터가 없습니다.")
        else:
            st.error("데이터 통신 실패 (API 키 확인 필요)")
