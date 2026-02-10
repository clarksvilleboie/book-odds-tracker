import streamlit as st
import requests

# ======================
# 설정 (여기만 수정)
# ======================
MY_NICKNAME = "jun lee"
API_KEY = "e2d960a84ee7d4f9fd5481eda30ac918"  # ✅ 너의 the-odds-api 키로 바꿔

st.set_page_config(page_title="Oddsportal Pro", layout="wide")

# ======================
# 1부 20팀 로고 (네가 올린 표 기준)
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

# Odds API 팀명/약칭이 다르게 올 때 흡수
TEAM_ALIASES = {
    "Man City": "Manchester City",
    "Manchester City FC": "Manchester City",
    "Man United": "Manchester United",
    "Manchester Utd": "Manchester United",
    "Manchester United FC": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
    "Wolverhampton": "Wolverhampton Wanderers",
    "Brighton": "Brighton and Hove Albion",
    "Brighton & Hove Albion": "Brighton and Hove Albion",
    "Nottm Forest": "Nottingham Forest",
    "Notts Forest": "Nottingham Forest",
    "AFC Bournemouth": "Bournemouth",
    "Bournemouth AFC": "Bournemouth",
}

def normalize_team_name(name: str) -> str:
    name = (name or "").strip()
    return TEAM_ALIASES.get(name, name)

def get_team_logo(team: str) -> str:
    team = normalize_team_name(team)
    return TEAM_LOGOS_EPL.get(team, "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg")

# ======================
# CSS (UI)
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
        gap: 8px;
    }
    .team-section {
        display: flex; align-items: center; width: 45%;
        font-weight: 500; font-size: 0.95rem;
        gap: 6px;
        flex-wrap: wrap;
    }
    .team-logo {
        width: 24px; height: 24px;
        object-fit: contain;
    }
    .odd-box {
        border: 1px solid #e9ecef; border-radius: 3px; padding: 6px 0;
        text-align: center; width: 65px; display: inline-block;
        font-weight: 600; font-size: 0.9rem; background-color: #fcfcfc;
    }
    .best-odd {
        background-color: #fff9c4 !important;
        border-color: #fbc02d !important;
        color: #000 !important;
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
    st.selectbox("Select", ["soccer_epl"], index=0)
    st.caption("※ 로고는 ‘네가 올린 1부 20팀’ 기준으로 매핑됨")

sport_key = "soccer_epl"

# VIP 업체
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
        st.error("데이터 로드 실패 (API_KEY / 요청 제한 / 네트워크 확인)")
    else:
        data = res.json()

        st.markdown("""
        <div class="table-header">
            <div style="display:flex; justify-content:space-between; text-align:center;">
                <div style="width:10%;">Time</div>
                <div style="width:45%; text-align:left;">Match</div>
                <div style="width:15%;">1</div>
                <div style="width:15%;">X</div>
                <div style="width:15%;">2</div>
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

            # 배당 계산 (VIP bookies 중 최댓값)
            best_h = 0.0
            best_d = 0.0
            best_a = 0.0

            for b in game.get("bookmakers", []):
                if b.get("key") not in VIP_BOOKIES:
                    continue

                h2h = next((m for m in b.get("markets", []) if m.get("key") == "h2h"), None)
                if not h2h:
                    continue

                for o in h2h.get("outcomes", []):
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

            # ✅ 여기 중요: HTML은 반드시 unsafe_allow_html=True
            st.markdown(f"""
            <div class="match-row">
                <div style="width:10%; color:#999; font-size:0.85rem; text-align:center;">
                    {start_time}
                </div>

                <div class="team-section">
                    <img src="{get_team_logo(home)}" class="team-logo">
                    <span>{home}</span>
                    <span style="color:#666;">vs</span>
                    <span>{away}</span>
                    <img src="{get_team_logo(away)}" class="team-logo">
                </div>

                <div style="width:15%; text-align:center;"><span class="odd-box {h_cls}">{h_val}</span></div>
                <div style="width:15%; text-align:center;"><span class="odd-box {d_cls}">{d_val}</span></div>
                <div style="width:15%; text-align:center;"><span class="odd-box {a_cls}">{a_val}</span></div>
            </div>
            """, unsafe_allow_html=True)
