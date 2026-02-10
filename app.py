import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# [설정] 닉네임과 API 키
MY_NICKNAME = "jun lee"
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="EPL Odds Flow Pro", layout="wide")

# 🎨 [디자인] Behance 시안 느낌의 프리미엄 다크 테마
st.markdown("""
<style>
    .main { background-color: #0F172A; color: #F8FAFC; }
    .header-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 30px; text-align: center; border-radius: 20px;
        border: 1px solid #334155; margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .main-title {
        font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .table-header {
        background-color: #1E293B; border-radius: 10px;
        padding: 15px; font-weight: 700; color: #94A3B8;
        font-size: 0.85rem; margin-bottom: 10px; border: 1px solid #334155;
    }
    .match-row {
        background-color: #1E293B; border-radius: 12px; padding: 15px;
        margin-bottom: 12px; border: 1px solid #334155;
        display: flex; align-items: center; transition: 0.3s;
    }
    .match-row:hover { border-color: #38BDF8; transform: translateY(-2px); }
    .team-logo { width: 28px; height: 28px; object-fit: contain; }
    .odd-box {
        background-color: #0F172A; border: 1px solid #334155;
        border-radius: 8px; padding: 10px 0; width: 70px;
        text-align: center; font-weight: 700; color: #38BDF8;
    }
    .best-odd {
        background: linear-gradient(135deg, #FACC15 0%, #EAB308 100%);
        color: #0F172A !important; border: none;
    }
    .stButton>button {
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        color: white; border: none; border-radius: 12px;
        padding: 15px; font-weight: 700; width: 100%; transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# 🖼️ [로고 매핑] 보내주신 리스트 + 현재 EPL 팀 고해상도 매핑
EPL_LOGOS = {
    "Arsenal": "359", "Manchester City": "382", "Aston Villa": "362", 
    "Chelsea": "363", "Manchester United": "360", "Liverpool": "364",
    "Brentford": "337", "Everton": "368", "Bournemouth": "349",
    "Newcastle United": "361", "Fulham": "370", "Crystal Palace": "384",
    "Brighton and Hove Albion": "331", "Tottenham Hotspur": "367", 
    "Nottingham Forest": "393", "West Ham United": "371", "Wolverhampton Wanderers": "380",
    "Leicester City": "375", "Southampton": "376", "Ipswich Town": "374"
}

def get_logo_url(team_name):
    # 팀 이름이 포함된 ID 찾기 (예: 'Man Utd' -> 'Manchester United')
    for name, id in EPL_LOGOS.items():
        if name in team_name or team_name in name:
            return f"https://a.espncdn.com/i/teamlogos/soccer/500/{id}.png"
    return "https://a.espncdn.com/i/teamlogos/soccer/500/default-team-logo.png"

# 메인 헤더
st.markdown(f"""
<div class="header-box">
    <div class="main-title">EPL ODDS FLOW PRO</div>
    <div style="color: #94A3B8;">Premium Market Analysis for {MY_NICKNAME}</div>
</div>
""", unsafe_allow_html=True)

# 사이드바 (깔끔하게 정리)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg", width=150)
    st.divider()
    st.caption("현재 1부 리그 20개 팀 데이터를 실시간으로 추적합니다.")

# 데이터 호출 및 출력
if st.button('🔄 실시간 배당 데이터 동기화'):
    url = f'https://api.the-odds-api.com/v4/sports/soccer_epl/odds'
    params = {'apiKey': API_KEY, 'regions': 'us,uk,eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    res = requests.get(url, params=params)
    
    if res.status_code == 200:
        data = res.json()
        
        # 오즈포털 스타일 헤더
        st.markdown("""
        <div class="table-header">
            <div style="display: flex; justify-content: space-between; text-align: center;">
                <div style="width: 10%;">TIME</div>
                <div style="width: 45%; text-align: left;">PREMIER LEAGUE MATCH</div>
                <div style="width: 15%;">1</div><div style="width: 15%;">X</div><div style="width: 15%;">2</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for game in data:
            home, away = game['home_team'], game['away_team']
            time = game['commence_time'][11:16]
            
            # 최고 배당 계산
            b_h, b_d, b_a = 0, 0, 0
            for b in game['bookmakers']:
                h2h = next((m for m in b['markets'] if m['key'] == 'h2h'), None)
                if h2h:
                    h = next((x['price'] for x in h2h['outcomes'] if x['name'] == home), 0)
                    a = next((x['price'] for x in h2h['outcomes'] if x['name'] == away), 0)
                    d = next((x['price'] for x in h2h['outcomes'] if x['name'] == 'Draw'), 0)
                    b_h, b_d, b_a = max(b_h, h), max(b_d, d), max(best_a := b_a, a)

            # 출력 데이터 가공
            h_logo, a_logo = get_logo_url(home), get_logo_url(away)
            
            st.markdown(f"""
            <div class="match-row">
                <div style="width: 10%; color: #64748B; font-weight: 600; text-align: center;">{time}</div>
                <div style="width: 45%; display: flex; align-items: center; gap: 10px;">
                    <img src="{h_logo}" class="team-logo">
                    <span style="font-size: 0.9rem;">{home}</span>
                    <span style="color: #475569; font-size: 0.7rem;">VS</span>
                    <span style="font-size: 0.9rem;">{away}</span>
                    <img src="{a_logo}" class="team-logo">
                </div>
                <div style="width: 15%; text-align: center;"><div class="odd-box best-odd">{b_h:.2f}</div></div>
                <div style="width: 15%; text-align: center;"><div class="odd-box">{b_d:.2f}</div></div>
                <div style="width: 15%; text-align: center;"><div class="odd-box">{b_a:.2f}</div></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("API 연동 실패. 키를 확인하세요.")
