import streamlit as st
import requests
import pandas as pd

# ==========================================
# [설정] 닉네임과 API 키
MY_NICKNAME = "jun lee"
API_KEY = 'e2d960a84ee7d4f9fd5481eda30ac918'
# ==========================================

st.set_page_config(page_title="EPL Leaderboard Pro", layout="wide")

# 🎨 [UI 개선] 눈이 편하고 글자가 잘 보이는 화이트&클린 테마
st.markdown("""
<style>
    /* 배경을 밝은 회색/화이트 톤으로 변경 */
    .stApp { background-color: #F3F4F6; color: #111827; }
    
    /* 헤더 영역: EPL 공식 보라색 느낌 */
    .header-box {
        background-color: #3D195B; color: white; padding: 25px;
        text-align: center; border-radius: 0 0 20px 20px; margin-bottom: 20px;
    }
    
    /* 경기 행(Row): 화이트 카드에 진한 테두리 */
    .match-card {
        background-color: #FFFFFF; border: 2px solid #E5E7EB;
        border-radius: 15px; padding: 15px; margin-bottom: 10px;
        display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 텍스트 가독성: 폰트 크기 키우고 진하게 */
    .team-name { font-size: 1.1rem; font-weight: 700; color: #1F2937; }
    .match-time { color: #6B7280; font-weight: 600; font-size: 0.9rem; }
    
    /* 배당 박스: 배경색을 넣어서 숫자 부각 */
    .odd-box {
        background-color: #F9FAFB; border: 1px solid #D1D5DB;
        border-radius: 8px; padding: 10px 0; width: 75px;
        text-align: center; font-weight: 800; color: #374151; font-size: 1rem;
    }
    /* 최고 배당 강조: 형광 노란색 배경 */
    .best-odd { background-color: #FEF08A !important; border-color: #FACC15 !important; color: #000 !important; }
    
    .team-logo { width: 32px; height: 32px; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

# 🖼️ [사용자 명단 기반] EPL 20개 팀 로고 매핑 (번리/리즈 포함)
EPL_LOGOS = {
    "아스널": "359", "맨체스터 시티": "382", "애스턴 빌라": "362", "첼시": "363", 
    "맨유": "360", "리버풀": "364", "브렌트포드": "337", "에버턴": "368", 
    "본머스": "349", "뉴캐슬": "361", "선덜랜드": "366", "풀럼": "370", 
    "팰리스": "384", "브라이튼": "331", "리즈 유나이티드": "357", "토트넘": "367", 
    "노팅엄": "393", "웨스트햄": "371", "번리": "381", "울버햄튼": "380"
}

def get_logo(team_name):
    for name, id in EPL_LOGOS.items():
        if name in team_name or team_name in name:
            return f"https://a.espncdn.com/i/teamlogos/soccer/500/{id}.png"
    return "https://a.espncdn.com/i/teamlogos/soccer/500/default-team-logo.png"

# 상단 UI
st.markdown(f'<div class="header-box"><h1 style="margin:0;">🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL REAL-TIME ODDS</h1><p style="margin:0; opacity:0.8;">Market Monitor for {MY_NICKNAME}</p></div>', unsafe_allow_html=True)

# 데이터 호출 (생략 - 기존 로직 유지)
if st.button('🔄 배당 데이터 새로고침 (클릭)', type="primary", use_container_width=True):
    # API 호출 부분 (soccer_epl)
    # ... (데이터를 받아온 후 루프 실행) ...
    # 예시 출력 구조:
    st.markdown(f"""
    <div class="match-card">
        <div style="width: 10%;" class="match-time">19:30</div>
        <div style="width: 45%; display: flex; align-items: center; gap: 10px;">
            <img src="{get_logo('번리')}" class="team-logo">
            <span class="team-name">번리</span>
            <span style="color:#9CA3AF;">VS</span>
            <span class="team-name">리버풀</span>
            <img src="{get_logo('리버풀')}" class="team-logo">
        </div>
        <div style="width: 15%; text-align: center;"><div class="odd-box best-odd">3.45</div></div>
        <div style="width: 15%; text-align: center;"><div class="odd-box">3.20</div></div>
        <div style="width: 15%; text-align: center;"><div class="odd-box">1.95</div></div>
    </div>
    """, unsafe_allow_html=True)
