import os
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

import httpx
import streamlit as st


# =========================
# 0) 기본 설정
# =========================
st.set_page_config(page_title="EPL Odds Tracker", layout="wide")

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY") if hasattr(st, "secrets") else None
ODDS_API_KEY = ODDS_API_KEY or os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    st.error("ODDS_API_KEY가 없습니다. Streamlit Cloud → Settings → Secrets에 넣어주세요.")
    st.stop()

SPORT_KEY = "soccer_epl"
ODDS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"

REGIONS = "us,uk,eu"
ODDS_FORMAT = "decimal"
MARKETS = "h2h,totals"

# ✅ 사진처럼 라인별로 펼치기: 2.5 / 3.0 / 3.5만
TOTAL_POINTS = [2.5, 3.0, 3.5]

# ✅ 상위 10개(우선 포함: Pinnacle/Bet365/FanDuel)
PREFERRED_TOP10_ORDER = [
    "pinnacle",
    "bet365",
    "fanduel",
    "draftkings",
    "betmgm",
    "caesars",
    "pointsbetus",
    "betrivers",
    "betfair",
    "williamhill",
]
MAX_BOOKMAKERS = 10

EPL_TEAMS_20 = [
    "Arsenal",
    "Manchester City",
    "Liverpool",
    "Chelsea",
    "Manchester United",
    "Tottenham",
    "Newcastle United",
    "Aston Villa",
    "Brighton and Hove Albion",
    "West Ham United",
    "Brentford",
    "Wolverhampton Wanderers",
    "Fulham",
    "Crystal Palace",
    "AFC Bournemouth",
    "Everton",
    "Nottingham Forest",
    "Leicester City",
    "Southampton",
    "Ipswich Town",
]


# =========================
# 1) CSS (표/테두리/아코디언)
# =========================
st.markdown("""
<style>
.small { font-size: 12px; color:#64748b; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.up { color:#dc2626; font-weight:900; }
.down { color:#0284c7; font-weight:900; }
.flat { color:#64748b; font-weight:700; }

/* 테이블 */
.tblwrap{
  border:1.5px solid #cbd5e1;
  border-radius:14px;
  overflow:hidden;
  background:#fff;
  box-shadow: 0 1px 0 rgba(15,23,42,0.04);
}
.tbl{ width:100%; border-collapse:collapse; }
.tbl th, .tbl td{
  padding:9px 10px;
  border-bottom:1.25px solid #cbd5e1;
  border-right:1.0px solid #e2e8f0;
}
.tbl th:last-child, .tbl td:last-child{ border-right:none; }
.tbl th{
  text-align:left;
  color:#0f172a;
  font-size:13px;
  background:#f1f5f9;
  border-bottom:1.5px solid #94a3b8;
}
.tbl td{ font-size:14px; color:#0f172a; }
.tbl tr:hover td{ background:#f8fafc; }

/* 셀 안: 왼쪽(배당) / 오른쪽(변화) */
.cellflex{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
}
.leftval{ text-align:left; }
.rightchg{ text-align:right; white-space:nowrap; }

/* 경기 배너 expander */
div[data-testid="stExpander"] > details {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #ffffff;
}
div[data-testid="stExpander"] > details > summary {
  padding: 12px 14px;
  font-weight: 800;
  color: #0f172a;
}
div[data-testid="stExpander"] > details > summary:hover {
  background: #f8fafc;
}

/* O/U 라인 expander(안쪽) */
.ouwrap div[data-testid="stExpander"] > details {
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #ffffff;
}
.ouwrap div[data-testid="stExpander"] > details > summary {
  padding: 10px 12px;
  font-weight: 800;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 2) 유틸
# =========================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def direction(prev: Optional[float], curr: Optional[float]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    if prev is None or curr is None:
        return prev, None, None
    d = curr - prev
    if abs(d) < 1e-12:
        return prev, 0.0, "UNCHANGED"
    return prev, d, "UP" if d > 0 else "DOWN"

def fmt_time(iso: str) -> str:
    if not iso:
        return "-"
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso

def point_key(p: float) -> str:
    return f"{p:.1f}".replace(".", "_")  # 2.5 -> 2_5


# =========================
# 3) API 호출 (1분 캐시)
# =========================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_odds_cached() -> Dict[str, Any]:
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso",
    }
    try:
        r = httpx.get(ODDS_URL, params=params, timeout=25)
        r.raise_for_status()
        return {"ok": True, "data": r.json(), "fetched_utc": utc_now_iso(), "error": None}
    except Exception as e:
        return {"ok": False, "data": [], "fetched_utc": utc_now_iso(), "error": str(e)}


# =========================
# 4) 정규화
# =========================
def normalize_h2h(home: str, away: str, outcomes: list) -> Dict[str, float]:
    m = {}
    for o in outcomes:
        name = o.get("name")
        price = safe_float(o.get("price"))
        if name == home:
            m["HOME"] = price
        elif name == away:
            m["AWAY"] = price
        elif str(name).lower() == "draw":
            m["DRAW"] = price
    return m

def normalize_totals_points(outcomes: list, points: List[float]) -> Dict[str, float]:
    want = set(points)
    m = {}
    for o in outcomes:
        p = safe_float(o.get("point"))
        if p is None or p not in want:
            continue
        name = str(o.get("name", "")).lower()
        price = safe_float(o.get("price"))
        pk = point_key(p)
        if name == "over":
            m[f"OVER_{pk}"] = price
        elif name == "under":
            m[f"UNDER_{pk}"] = price
    return m

def normalize_events(raw_events: list) -> Dict[str, Any]:
    events = {}
    for ev in raw_events:
        event_id = ev.get("id")
        home = ev.get("home_team")
        away = ev.get("away_team")
        commence = ev.get("commence_time")

        out = {
            "event_id": event_id,
            "home_team": home,
            "away_team": away,
            "commence_time_utc": commence,
            "markets": {"h2h": {}, "totals_multi": {}},
        }

        bms = ev.get("bookmakers", []) or []
        bm_map = {b.get("key"): b for b in bms if b.get("key")}

        selected_keys = [k for k in PREFERRED_TOP10_ORDER if k in bm_map][:MAX_BOOKMAKERS]
        if len(selected_keys) < MAX_BOOKMAKERS:
            rest = sorted([k for k in bm_map.keys() if k not in selected_keys])
            selected_keys += rest[: (MAX_BOOKMAKERS - len(selected_keys))]

        for bm_key in selected_keys:
            bm = bm_map.get(bm_key)
            if not bm:
                continue

            bm_title = bm.get("title") or bm_key
            bm_last_update = bm.get("last_update")

            for mk in bm.get("markets", []):
                mk_key = mk.get("key")
                mk_last_update = mk.get("last_update") or bm_last_update
                outcomes = mk.get("outcomes", [])

                if mk_key == "h2h":
                    m = normalize_h2h(home, away, outcomes)
                    if m:
                        out["markets"]["h2h"][bm_key] = {
                            "bookmaker_key": bm_key,
                            "title": bm_title,
                            "last_update_utc": mk_last_update,
                            "outcomes": m,
                        }
                elif mk_key == "totals":
                    m = normalize_totals_points(outcomes, TOTAL_POINTS)
                    if m:
                        out["markets"]["totals_multi"][bm_key] = {
                            "bookmaker_key": bm_key,
                            "title": bm_title,
                            "last_update_utc": mk_last_update,
                            "outcomes": m,
                        }

        events[event_id] = out
    return events

def compute_delta(curr_events: Dict[str, Any], prev_events: Dict[str, Any]) -> Dict[str, Any]:
    out_events = copy.deepcopy(curr_events)

    for event_id, ev in out_events.items():
        for market_key in ["h2h", "totals_multi"]:
            market = ev["markets"].get(market_key, {})
            for bm_key, bm in market.items():
                curr_outcomes = bm.get("outcomes", {})
                new_outcomes = {}

                for ok, curr_price in curr_outcomes.items():
                    prev_price = None
                    try:
                        prev_price = prev_events[event_id]["markets"][market_key][bm_key]["outcomes"].get(ok)
                    except Exception:
                        prev_price = None

                    prev_p, d, dirn = direction(prev_price, curr_price)
                    new_outcomes[ok] = {
                        "price": curr_price,
                        "prev_price": prev_p,
                        "delta": d,
                        "direction": dirn,
                    }

                bm["outcomes"] = new_outcomes
    return out_events


# =========================
# 5) 렌더
# =========================
def fmt_cell_left_right(o: dict) -> str:
    if not o or o.get("price") is None:
        return "<span class='flat'>-</span>"

    price = float(o["price"])
    left = f"<span class='mono leftval'>{price:.3f}</span>"

    d = o.get("delta")
    dirn = o.get("direction")

    if d is None or dirn is None or abs(d) < 1e-12:
        right = "<span class='flat rightchg'></span>"
        return f"<div class='cellflex'>{left}{right}</div>"

    if dirn == "UP":
        right = f"<span class='rightchg up'>▲ {d:+.2f}</span>"
    elif dirn == "DOWN":
        right = f"<span class='rightchg down'>▼ {d:+.2f}</span>"
    else:
        right = "<span class='flat rightchg'></span>"

    return f"<div class='cellflex'>{left}{right}</div>"

def render_market_table_html(market: Dict[str, Any], cols: List[Tuple[str, str]]) -> str:
    if not market:
        return "<div class='small'>데이터 없음</div>"

    order_index = {k: i for i, k in enumerate(PREFERRED_TOP10_ORDER)}
    items = list(market.items())
    items.sort(key=lambda kv: order_index.get(kv[0], 9999))

    ths = "<th>Bookmaker</th>" + "".join([f"<th>{label}</th>" for _, label in cols])

    rows = []
    for bm_key, bm in items[:MAX_BOOKMAKERS]:
        title = bm.get("title") or bm_key
        outcomes = bm.get("outcomes") or {}

        tds = [f"<td>{title}</td>"]
        for k, _label in cols:
            tds.append(f"<td>{fmt_cell_left_right(outcomes.get(k))}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")

    return f"""
    <div class="tblwrap">
      <table class="tbl">
        <thead><tr>{ths}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """

def build_totals_market_for_point(ev_markets_totals: Dict[str, Any], p: float) -> Dict[str, Any]:
    """
    totals_multi(북메이커 전체 outcomes)에서 특정 point(2.5/3.0/3.5)만 남긴 market dict를 새로 만든다
    -> expander 하나당 표 하나 렌더
    """
    pk = point_key(p)
    need_keys = {f"OVER_{pk}", f"UNDER_{pk}"}

    out_market = {}
    for bm_key, bm in ev_markets_totals.items():
        new_bm = copy.deepcopy(bm)
        outs = new_bm.get("outcomes") or {}
        filtered = {k: v for k, v in outs.items() if k in need_keys}
        if filtered:
            new_bm["outcomes"] = filtered
            out_market[bm_key] = new_bm

    return out_market


# =========================
# 6) UI
# =========================
st.title("EPL Odds Tracker")
st.caption("사진 느낌: O/U 라인(2.5 / 3.0 / 3.5) 눌러서 펼치면 북메이커 배당 주르륵 (수동 갱신)")

c1, c2 = st.columns([2, 1])
with c1:
    team_filter = st.selectbox("팀 필터", ["전체"] + EPL_TEAMS_20, index=0)
with c2:
    if st.button("갱신 (API 다시 호출 / 캐시 무시)"):
        fetch_odds_cached.clear()
        st.toast("캐시 초기화 완료. 새 데이터로 갱신합니다.")

res = fetch_odds_cached()
if not res["ok"]:
    st.error(f"API 호출 실패: {res['error']}")
    st.stop()

st.success(f"Fetched (UTC): {res['fetched_utc']} / Events: {len(res['data'])}")

curr_events = normalize_events(res["data"])

if "prev_events" not in st.session_state:
    st.session_state.prev_events = {}

events_with_delta = compute_delta(curr_events, st.session_state.prev_events)
st.session_state.prev_events = copy.deepcopy(curr_events)

events_list = list(events_with_delta.values())

if team_filter != "전체":
    tf = team_filter.lower()
    events_list = [e for e in events_list if tf in (e.get("home_team", "").lower()) or tf in (e.get("away_team", "").lower())]

events_list.sort(key=lambda e: e.get("commence_time_utc") or "")

st.markdown(
    "<div class='small'>표시 규칙: 셀 왼쪽=배당, 셀 오른쪽=변화(▲/▼ + 변화량). 0이면 변화 표시 안 함.</div>",
    unsafe_allow_html=True
)

if not events_list:
    st.info("표시할 경기가 없습니다.")
    st.stop()

for ev in events_list:
    home = ev.get("home_team")
    away = ev.get("away_team")
    kickoff = fmt_time(ev.get("commence_time_utc"))

    with st.expander(f"{home} vs {away}  |  Kickoff: {kickoff}", expanded=False):
        left, right = st.columns(2, gap="large")

        with left:
            st.write("### 1X2 (승/무/패)")
            h2h_cols = [("HOME", "Home(1)"), ("DRAW", "Draw(X)"), ("AWAY", "Away(2)")]
            st.markdown(render_market_table_html(ev["markets"].get("h2h", {}), h2h_cols), unsafe_allow_html=True)

        with right:
            st.write("### O/U (언오버) — 라인 눌러서 펼치기")

            st.markdown("<div class='ouwrap'>", unsafe_allow_html=True)

            totals_all = ev["markets"].get("totals_multi", {})

            for p in TOTAL_POINTS:
                # 라인별 market 구성
                m_point = build_totals_market_for_point(totals_all, p)
                cols = [(f"OVER_{point_key(p)}", f"Over {p:g}"), (f"UNDER_{point_key(p)}", f"Under {p:g}")]

                with st.expander(f"Over/Under +{p:g}", expanded=False):
                    st.markdown(render_market_table_html(m_point, cols), unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
