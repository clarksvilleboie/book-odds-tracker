 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
index 301ecc283351efab2a8dcba060538fbbdc9e3b73..99f6cb7dd38200a575413c27a0a0f2a09a176010 100644
--- a/app.py
+++ b/app.py
@@ -1,222 +1,206 @@
-import streamlit as st
-import requests
-
-# ======================
-# 설정 (여기만 수정)
-# ======================
-MY_NICKNAME = "jun lee"
-API_KEY = "e2d960a84ee7d4f9fd5481eda30ac918"  # ✅ 너의 the-odds-api 키로 바꿔
-
-st.set_page_config(page_title="Oddsportal Pro", layout="wide")
-
-# ======================
-# 1부 20팀 로고 (네가 올린 표 기준)
-# ======================
-TEAM_LOGOS_EPL = {
-    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
-    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
-    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/9/9a/Aston_Villa_FC_logo.svg",
-    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
-    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
-    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
-    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
-    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
-    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
-    "Newcastle United": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
-    "Sunderland": "https://upload.wikimedia.org/wikipedia/en/7/77/Sunderland_A.F.C._logo.svg",
-    "Fulham": "https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg",
-    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/0/0c/Crystal_Palace_FC_logo.svg",
-    "Brighton and Hove Albion": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
-    "Leeds United": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
-    "Tottenham Hotspur": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
-    "Nottingham Forest": "https://upload.wikimedia.org/wikipedia/en/d/d2/Nottingham_Forest_logo.svg",
-    "West Ham United": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
-    "Burnley": "https://upload.wikimedia.org/wikipedia/en/0/02/Burnley_FC_badge.svg",
-    "Wolverhampton Wanderers": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
-}
+import random
+from datetime import datetime, timedelta
 
-# Odds API 팀명/약칭이 다르게 올 때 흡수
-TEAM_ALIASES = {
-    "Man City": "Manchester City",
-    "Manchester City FC": "Manchester City",
-    "Man United": "Manchester United",
-    "Manchester Utd": "Manchester United",
-    "Manchester United FC": "Manchester United",
-    "Spurs": "Tottenham Hotspur",
-    "Tottenham": "Tottenham Hotspur",
-    "Newcastle": "Newcastle United",
-    "West Ham": "West Ham United",
-    "Wolves": "Wolverhampton Wanderers",
-    "Wolverhampton": "Wolverhampton Wanderers",
-    "Brighton": "Brighton and Hove Albion",
-    "Brighton & Hove Albion": "Brighton and Hove Albion",
-    "Nottm Forest": "Nottingham Forest",
-    "Notts Forest": "Nottingham Forest",
-    "AFC Bournemouth": "Bournemouth",
-    "Bournemouth AFC": "Bournemouth",
-}
+import streamlit as st
 
-def normalize_team_name(name: str) -> str:
-    name = (name or "").strip()
-    return TEAM_ALIASES.get(name, name)
+st.set_page_config(page_title="EPL Odds Tracker", layout="wide")
+
+EPL_TEAMS = [
+    "Arsenal",
+    "Aston Villa",
+    "Bournemouth",
+    "Brentford",
+    "Brighton & Hove Albion",
+    "Burnley",
+    "Chelsea",
+    "Crystal Palace",
+    "Everton",
+    "Fulham",
+    "Leeds United",
+    "Liverpool",
+    "Manchester City",
+    "Manchester United",
+    "Newcastle United",
+    "Nottingham Forest",
+    "Sunderland",
+    "Tottenham Hotspur",
+    "West Ham United",
+    "Wolverhampton Wanderers",
+]
+
+
+def make_sample_rows() -> list[dict]:
+    """간단한 레이아웃 확인용 샘플 데이터."""
+    random.seed(7)
+    fixtures = [
+        ("Liverpool", "Arsenal"),
+        ("Manchester City", "Chelsea"),
+        ("Tottenham Hotspur", "Newcastle United"),
+        ("Manchester United", "Aston Villa"),
+        ("Everton", "West Ham United"),
+        ("Leeds United", "Fulham"),
+        ("Brentford", "Bournemouth"),
+        ("Crystal Palace", "Brighton & Hove Albion"),
+        ("Burnley", "Nottingham Forest"),
+        ("Sunderland", "Wolverhampton Wanderers"),
+    ]
+
+    now = datetime.now().replace(second=0, microsecond=0)
+    rows = []
+
+    for idx, (home, away) in enumerate(fixtures):
+        kickoff = now + timedelta(hours=idx * 2)
+
+        o1_old = round(random.uniform(1.6, 3.4), 2)
+        ox_old = round(random.uniform(2.8, 4.0), 2)
+        o2_old = round(random.uniform(2.0, 4.8), 2)
+
+        o1_new = round(o1_old + random.uniform(-0.25, 0.25), 2)
+        ox_new = round(ox_old + random.uniform(-0.25, 0.25), 2)
+        o2_new = round(o2_old + random.uniform(-0.25, 0.25), 2)
+
+        rows.append(
+            {
+                "kickoff": kickoff.strftime("%m/%d %H:%M"),
+                "home": home,
+                "away": away,
+                "o1_old": o1_old,
+                "o1_new": o1_new,
+                "ox_old": ox_old,
+                "ox_new": ox_new,
+                "o2_old": o2_old,
+                "o2_new": o2_new,
+            }
+        )
+    return rows
+
+
+def diff_badge(old: float, new: float) -> str:
+    change = round(new - old, 2)
+    if change > 0:
+        return f"<span class='up'>▲ +{change:.2f}</span>"
+    if change < 0:
+        return f"<span class='down'>▼ {change:.2f}</span>"
+    return "<span class='same'>- 0.00</span>"
 
-def get_team_logo(team: str) -> str:
-    team = normalize_team_name(team)
-    return TEAM_LOGOS_EPL.get(team, "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg")
 
-# ======================
-# CSS (UI)
-# ======================
-st.markdown("""
+st.markdown(
+    """
 <style>
-    .main { background-color: #ffffff; color: #333333; }
-    .header-box {
-        background-color: #2c3e50; color: white; padding: 20px;
-        text-align: center; border-radius: 0 0 15px 15px; margin-bottom: 25px;
-    }
-    .table-header {
-        background-color: #f1f3f5; border-top: 2px solid #34495e;
-        border-bottom: 1px solid #dee2e6; font-weight: bold;
-        padding: 12px; font-size: 0.85rem; color: #495057;
-    }
-    .match-row {
-        border-bottom: 1px solid #f0f0f0; padding: 15px 0;
-        display: flex; align-items: center; justify-content: space-between;
-        gap: 8px;
-    }
-    .team-section {
-        display: flex; align-items: center; width: 45%;
-        font-weight: 500; font-size: 0.95rem;
-        gap: 6px;
-        flex-wrap: wrap;
-    }
-    .team-logo {
-        width: 24px; height: 24px;
-        object-fit: contain;
-    }
-    .odd-box {
-        border: 1px solid #e9ecef; border-radius: 3px; padding: 6px 0;
-        text-align: center; width: 65px; display: inline-block;
-        font-weight: 600; font-size: 0.9rem; background-color: #fcfcfc;
-    }
-    .best-odd {
-        background-color: #fff9c4 !important;
-        border-color: #fbc02d !important;
-        color: #000 !important;
-    }
+.main-title {
+    background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
+    color: white;
+    padding: 20px;
+    border-radius: 14px;
+    margin-bottom: 16px;
+}
+.sub-text {
+    color: #cbd5e1;
+    margin-top: 4px;
+}
+.panel {
+    border: 1px solid #e5e7eb;
+    border-radius: 12px;
+    padding: 14px;
+    background: #ffffff;
+    margin-bottom: 12px;
+}
+.table-wrap {
+    border: 1px solid #e5e7eb;
+    border-radius: 12px;
+    overflow: hidden;
+}
+.head-row, .match-row {
+    display: grid;
+    grid-template-columns: 120px 1.6fr 1fr 1fr 1fr;
+    gap: 8px;
+    align-items: center;
+    padding: 12px 14px;
+}
+.head-row {
+    background: #f8fafc;
+    font-weight: 700;
+    border-bottom: 1px solid #e5e7eb;
+}
+.match-row:nth-child(odd) { background: #fcfcfd; }
+.match-row + .match-row { border-top: 1px solid #f1f5f9; }
+.team-line { font-weight: 600; }
+.odd-group { font-size: 0.9rem; }
+.odd-current {
+    font-weight: 700;
+    font-size: 1rem;
+    margin-right: 6px;
+}
+.up { color: #16a34a; font-weight: 700; }
+.down { color: #dc2626; font-weight: 700; }
+.same { color: #64748b; font-weight: 700; }
 </style>
-""", unsafe_allow_html=True)
+""",
+    unsafe_allow_html=True,
+)
 
-# ======================
-# Header
-# ======================
 st.markdown(
-    f'<div class="header-box"><h1>Oddsportal Pro</h1><p>Developed by {MY_NICKNAME}</p></div>',
-    unsafe_allow_html=True
+    """
+<div class="main-title">
+    <h2 style="margin:0;">⚽ EPL Odds Tracker (Layout Draft)</h2>
+    <p class="sub-text">20개 팀 기준 배당 변화(1/X/2)를 한 화면에서 보기 쉽게 구성한 시안</p>
+</div>
+""",
+    unsafe_allow_html=True,
 )
 
-# ======================
-# Sidebar (EPL 고정)
-# ======================
 with st.sidebar:
-    st.header("🏆 League")
-    st.selectbox("Select", ["soccer_epl"], index=0)
-    st.caption("※ 로고는 ‘네가 올린 1부 20팀’ 기준으로 매핑됨")
-
-sport_key = "soccer_epl"
-
-# VIP 업체
-VIP_BOOKIES = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pinnacle']
-
-# ======================
-# Main
-# ======================
-if st.button("🔄 Update Real-time Odds", type="primary", use_container_width=True):
-    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
-    params = {
-        "apiKey": API_KEY,
-        "regions": "us,uk,eu",
-        "markets": "h2h",
-        "oddsFormat": "decimal"
-    }
-
-    res = requests.get(url, params=params)
-
-    if res.status_code != 200:
-        st.error("데이터 로드 실패 (API_KEY / 요청 제한 / 네트워크 확인)")
-    else:
-        data = res.json()
-
-        st.markdown("""
-        <div class="table-header">
-            <div style="display:flex; justify-content:space-between; text-align:center;">
-                <div style="width:10%;">Time</div>
-                <div style="width:45%; text-align:left;">Match</div>
-                <div style="width:15%;">1</div>
-                <div style="width:15%;">X</div>
-                <div style="width:15%;">2</div>
-            </div>
+    st.header("필터")
+    selected_team = st.selectbox("팀 선택", ["전체"] + EPL_TEAMS)
+    move_filter = st.radio("변화 필터", ["전체", "상승만", "하락만"], horizontal=True)
+    st.caption("지금은 UI 시안용 샘플 데이터입니다.")
+
+rows = make_sample_rows()
+
+if selected_team != "전체":
+    rows = [r for r in rows if selected_team in (r["home"], r["away"])]
+
+if move_filter == "상승만":
+    rows = [r for r in rows if (r["o1_new"] - r["o1_old"] > 0) or (r["ox_new"] - r["ox_old"] > 0) or (r["o2_new"] - r["o2_old"] > 0)]
+elif move_filter == "하락만":
+    rows = [r for r in rows if (r["o1_new"] - r["o1_old"] < 0) or (r["ox_new"] - r["ox_old"] < 0) or (r["o2_new"] - r["o2_old"] < 0)]
+
+col1, col2, col3 = st.columns(3)
+with col1:
+    st.markdown(f"<div class='panel'><b>경기 수</b><br><span style='font-size:1.3rem'>{len(rows)}</span></div>", unsafe_allow_html=True)
+with col2:
+    avg_home = sum(r["o1_new"] for r in rows) / len(rows) if rows else 0
+    st.markdown(f"<div class='panel'><b>평균 홈승 배당</b><br><span style='font-size:1.3rem'>{avg_home:.2f}</span></div>", unsafe_allow_html=True)
+with col3:
+    avg_away = sum(r["o2_new"] for r in rows) / len(rows) if rows else 0
+    st.markdown(f"<div class='panel'><b>평균 원정승 배당</b><br><span style='font-size:1.3rem'>{avg_away:.2f}</span></div>", unsafe_allow_html=True)
+
+st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
+st.markdown(
+    """
+    <div class="head-row">
+        <div>Kickoff</div>
+        <div>Match</div>
+        <div>1 (Home)</div>
+        <div>X (Draw)</div>
+        <div>2 (Away)</div>
+    </div>
+    """,
+    unsafe_allow_html=True,
+)
+
+for row in rows:
+    st.markdown(
+        f"""
+        <div class="match-row">
+            <div>{row['kickoff']}</div>
+            <div class="team-line">{row['home']} vs {row['away']}</div>
+            <div class="odd-group"><span class="odd-current">{row['o1_new']:.2f}</span>{diff_badge(row['o1_old'], row['o1_new'])}</div>
+            <div class="odd-group"><span class="odd-current">{row['ox_new']:.2f}</span>{diff_badge(row['ox_old'], row['ox_new'])}</div>
+            <div class="odd-group"><span class="odd-current">{row['o2_new']:.2f}</span>{diff_badge(row['o2_old'], row['o2_new'])}</div>
         </div>
-        """, unsafe_allow_html=True)
-
-        for game in data:
-            home_raw = game.get("home_team", "")
-            away_raw = game.get("away_team", "")
-            home = normalize_team_name(home_raw)
-            away = normalize_team_name(away_raw)
-
-            commence = game.get("commence_time", "")
-            start_time = commence[11:16] if len(commence) >= 16 else "-"
-
-            # 배당 계산 (VIP bookies 중 최댓값)
-            best_h = 0.0
-            best_d = 0.0
-            best_a = 0.0
-
-            for b in game.get("bookmakers", []):
-                if b.get("key") not in VIP_BOOKIES:
-                    continue
-
-                h2h = next((m for m in b.get("markets", []) if m.get("key") == "h2h"), None)
-                if not h2h:
-                    continue
-
-                for o in h2h.get("outcomes", []):
-                    name = normalize_team_name(o.get("name", ""))
-                    price = float(o.get("price", 0) or 0)
-
-                    if name == home:
-                        best_h = max(best_h, price)
-                    elif name == away:
-                        best_a = max(best_a, price)
-                    elif name == "Draw":
-                        best_d = max(best_d, price)
-
-            h_val = f"{best_h:.2f}" if best_h else "-"
-            d_val = f"{best_d:.2f}" if best_d else "-"
-            a_val = f"{best_a:.2f}" if best_a else "-"
-
-            h_cls = "best-odd" if best_h else ""
-            d_cls = "best-odd" if best_d else ""
-            a_cls = "best-odd" if best_a else ""
-
-            # ✅ 여기 중요: HTML은 반드시 unsafe_allow_html=True
-            st.markdown(f"""
-            <div class="match-row">
-                <div style="width:10%; color:#999; font-size:0.85rem; text-align:center;">
-                    {start_time}
-                </div>
-
-                <div class="team-section">
-                    <img src="{get_team_logo(home)}" class="team-logo">
-                    <span>{home}</span>
-                    <span style="color:#666;">vs</span>
-                    <span>{away}</span>
-                    <img src="{get_team_logo(away)}" class="team-logo">
-                </div>
-
-                <div style="width:15%; text-align:center;"><span class="odd-box {h_cls}">{h_val}</span></div>
-                <div style="width:15%; text-align:center;"><span class="odd-box {d_cls}">{d_val}</span></div>
-                <div style="width:15%; text-align:center;"><span class="odd-box {a_cls}">{a_val}</span></div>
-            </div>
-            """, unsafe_allow_html=True)
+        """,
+        unsafe_allow_html=True,
+    )
+
+st.markdown("</div>", unsafe_allow_html=True)
 
EOF
)
