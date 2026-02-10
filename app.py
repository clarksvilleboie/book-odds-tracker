import streamlit as st
import requests
from datetime import datetime

# ======================
# 설정
# ======================
MY_NICKNAME = "jun lee"
API_KEY = "e2d960a84ee7d4f9fd5481eda30ac918"

st.set_page_config(page_title="Oddsportal Pro", layout="wide")

# ======================
# 팀 로고 (EPL)
# ======================
TEAM_LOGOS_EPL = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/9/9a/Aston_Villa_FC_logo.svg",
    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Brighton and Hove Albion": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Leeds United": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Newcastle United": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Tottenham Hotspur": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
    "West Ham United": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
}

def get_team_logo(team):
    return TEAM_LOGOS_EPL.get(
        team,
        "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
    )

# ======================
# CSS
# ======================
st.markdown("""
<style>
.main { background-color: #ffffff; color: #333333; }
.header-box {
    background-color: #2c3e50; color: white; padding: 20px;
    text-align: center; border-radius: 0 0 15px 15px; margin-bottom: 25px;
}
.table-header {
    background-color: #f1f3f5; border-top: 2px solid #34495e;
    border-bottom: 1px solid #dee2e6; font-weight: bold;
    padding: 12px; font-size: 0.85rem; color: #495057;
}
.match-row {
    border-bottom: 1px solid #f0f0f0; padding: 15px 0;
    display: flex; align-items: center; justify-content: space-between;
}
.team-section {
    display: flex; align-items: center; width: 45%;
    font-weight: 500; font-size: 0.95rem;
}
.team-logo {
    width: 24px; height: 24px; margin: 0 8px;
    object-fit: contain;
}
.odd-box {
    border: 1px solid #e9ecef; border-radius: 3px;
    padding: 6px 0; text-align: center; width: 65px;
    font-weight: 600; font-size: 0.9rem; background-color: #fcfcfc;
}
.best-odd {
    background-color: #fff9c4 !important;
    border-color: #fbc02d !important;
}
</style>
""", unsafe_allow_html=True)

# ======================
# Header
# ======================
st.markdown(
    f'<div class="header-box"><h1>Oddsportal Pro</h1><p>Developed by {MY_NICKNAME}</p></div>',
    unsafe_allow_html=True
)

# ======================
# Sidebar
# ======================
with st.sidebar:
    st.header("🏆 League")
    sport_key = st.selectbox("Select", ["soccer_epl"])

VIP_BOOKIES = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pinnacle']

# ======================
# Main
# ======================
if st.button("🔄 Update Real-time Odds", type="primary", use_container_width=True):

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us,uk,eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    res = requests.get(url, params=params)

    if res.status_code != 200:
        st.error("데이터 불러오기 실패")
    else:
        data = res.json()

        st.markdown("""
        <div class="table-header">
            <div style="display:flex; justify-content:space-between;">
                <div style="width:10%; text-align:center;">Time</div>
                <div style="width:45%;">Match</div>
                <div style="width:15%; text-align:center;">1</div>
                <div style="width:15%; text-align:center;">X</div>
                <div style="width:15%; text-align:center;">2</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for game in data:
            home = game["home_team"]
            away = game["away_team"]
            start_time = game["commence_time"][11:16]

            best_h = best_d = best_a = 0

            for b in game["bookmakers"]:
                if b["key"] in VIP_BOOKIES:
                    m = next((m for m in b["markets"] if m["key"] == "h2h"), None)
                    if m:
                        for o in m["outcomes"]:
                            if o["name"] == home:
                                best_h = max(best_h, o["price"])
                            elif o["name"] == away:
                                best_a = max(best_a, o["price"])
                            elif o["name"] == "Draw":
                                best_d = max(best_d, o["price"])

            h_val = f"{best_h:.2f}" if best_h else "-"
            d_val = f"{best_d:.2f}" if best_d else "-"
            a_val = f"{best_a:.2f}" if best_a else "-"

            h_cls = "best-odd" if best_h else ""
            d_cls = "best-odd" if best_d else ""
            a_cls = "best-odd" if best_a else ""

            st.markdown(f"""
            <div class="match-row">
                <div style="width:10%; text-align:center; color:#999;">{start_time}</div>
                <div class="team-section">
                    <img src="{get_team_logo(home)}" class="team-logo">
                    {home} vs {away}
                    <img src="{get_team_logo(away)}" class="team-logo">
                </div>
                <div style="width:15%; text-align:center;"><span class="odd-box {h_cls}">{h_val}</span></div>
                <div style="width:15%; text-align:center;"><span class="odd-box {d_cls}">{d_val}</span></div>
                <div style="width:15%; text-align:center;"><span class="odd-box {a_cls}">{a_val}</span></div>
            </div>
            """, unsafe_allow_html=True)