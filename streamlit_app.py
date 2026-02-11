import os
import streamlit as st
import httpx

st.set_page_config(page_title="EPL Odds Tracker - Smoke Test", layout="wide")

# 1) Secrets/환경변수에서 키 읽기 (코드에 직접 쓰지 말기)
ODDS_API_KEY = st.secrets.get("ODDS_API_KEY") if hasattr(st, "secrets") else None
ODDS_API_KEY = ODDS_API_KEY or os.getenv("ODDS_API_KEY")

st.title("✅ EPL Odds Tracker (Smoke Test)")
st.write("배포/키/요청이 정상인지 먼저 확인하는 테스트 화면")

if not ODDS_API_KEY:
    st.error("ODDS_API_KEY가 없습니다. Streamlit Cloud → Settings → Secrets에 넣어야 합니다.")
    st.stop()

st.success("ODDS_API_KEY 로딩 OK")

SPORT_KEY = "soccer_epl"
URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"
params = {
    "apiKey": ODDS_API_KEY,
    "regions": "uk,eu",
    "markets": "h2h",
    "oddsFormat": "decimal",
    "dateFormat": "iso",
}

if st.button("API 호출 테스트"):
    try:
        r = httpx.get(URL, params=params, timeout=20)
        st.write("HTTP status:", r.status_code)
        r.raise_for_status()
        data = r.json()
        st.success(f"성공! 경기 {len(data)}개 받아옴")
        # 첫 경기만 미리보기
        if data:
            st.json(data[0])
    except Exception as e:
        st.error(f"API 호출 실패: {e}")
