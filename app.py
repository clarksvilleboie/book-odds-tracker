import streamlit as st
import requests

# ======================
# 설정
# ======================
MY_NICKNAME = "jun lee"
API_KEY = "e2d960a84ee7d4f9fd5481eda30ac918"  # ✅ 여기만 너 키로 바꿔

st.set_page_config(page_title="Oddsportal Pro", layout="wide")

# ======================
# ✅ 2026 현재 1부리그(20팀) 로고 세트 (네가 올린 표 기준)
# ======================
TEAM_LOGOS_EPL = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/9/9a/Aston_Villa_FC_logo.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Newcastle United": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Sunderland": "https://upload.wikimedia.org/wikipedia/en/7/77/Sunderland_A.F.C._logo.svg",
    "Fulham": "https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg",
    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/0/0c/Crystal_Palace_FC_logo.svg",
    "Brighton and Hove Albion": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    "Leeds United": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
    "Tottenham Hotspur": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
    "Nottingham Forest": "https://upload.wikimedia.org/wikipedia/en/d/d2/Nottingham_Forest_logo.svg",
    "West Ham United": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    "Burnley": "https://upload.wikimedia.org/wikipedia/en/0/02/Burnley_FC_badge.svg",
    "Wolverhampton Wanderers": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
}

# ✅ Odds API 팀명 표기가 가끔 다르게 오는 걸 흡수(별칭/약칭 처리)
TEAM_ALIASES = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Manchester Utd": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
    "Brighton": "Brighton and Hove Albion",
    "Nottm Forest": "Nottingham Forest",
    "Notts Forest": "Nottingham Forest",
    "Bournemouth AFC": "Bournemouth",
    "AFC Bournemouth": "Bournemouth",
}

def normalize_team_name(name: str) -> str:
    name = (name or "").strip()
    return TEAM_ALIASES.get(name, name)

def get_team_logo(team: str) -> str:
    team = normalize_team_name(team)
    return TEAM_LOGOS_EPL.get(team, "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg")

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
# Sidebar (EPL 고정)
# ======================
with st.sidebar:
    st.header("🏆 League")
    sport_key = st.selectbox("Select", ["soccer_epl"])  # ✅ EPL 고정

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
        st.error("데이터 불러오기 실패 (API KEY / 요청 제한 / sport_key 확인)")
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
            home_raw = game.get("home_team", "")
            away_raw = game.get("away_team", "")
            home = normalize_team_name(home_raw)
            away = normalize_team_name(away_raw)

            commence = game.get("commence_time", "")
            start_time = commence[11:16] if len(commence) >= 16 else "-"

            best_h = best_d = best_a = 0.0

            for b in game.get("bookmakers", []):
                if b.get("key") in VIP_BOOKIES:
                    m = next((m for m in b.get("markets", []) if m.get("key") == "h2h"), None)
                    if not m:
                        continue

                    for o in m.get("outcomes", []):
                        name = normalize_team_name(o.get("name", ""))
                        price = float(o.get("price", 0) or 0)

                        if name == home:
                            best_h = max(best_h, price)
                        elif name == away:
                            best_a = max(best_a, price)
                        elif name == "Draw":
                            best_d = max(best_d, price)

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
