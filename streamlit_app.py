import os
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

import httpx
import streamlit as st
from streamlit_autorefresh import st_autorefresh


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

REGIONS = "uk,eu"
ODDS_FORMAT = "decimal"
MARKETS = "h2h,totals"

TOP10_BOOKMAKERS = [
    "bet365", "pinnacle", "williamhill", "unibet", "ladbrokes",
    "paddypower", "betfair", "betvictor", "1xbet", "betsson"
]

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
# 1) CSS (라이트 테이블: 가독성 최우선)
# =========================
st.markdown("""
<style>
.small { font-size: 12px; color:#64748b; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.kick { color:#64748b; font-size:12px; margin-top:-6px; }

/* 화살표 */
.up { color:#dc2626; font-weight:900; }     /* 빨강 */
.down { color:#0284c7; font-weight:900; }   /* 파랑 */
.flat { color:#64748b; font-weight:700; }

/* 카드/구분 */
.hr { height:1px; background: #e5e7eb; margin: 16px 0; }

/* 표 (라이트) */
.tblwrap {
  border:1px solid #e5e7eb;
  border-radius:14px;
  overflow:hidden;
  background: #ffffff;
}
.tbl { width:100%; border-collapse:collapse; }
.tbl th, .tbl td { padding:9px 10px; border-bottom:1px solid #eef2f7; }
.tbl th {
  text-align:left;
  color:#0f172a;
  font-size:13px;
  background: #f8fafc;   /* 연한 헤더 */
}
.tbl td { font-size:14px; color:#0f172a; }
.r { text-align:right; white-space:nowrap; }
.tbl tr:hover td { background: #f8fafc; }
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

def normalize_totals_2_5(outcomes: list) -> Dict[str, float]:
    m = {}
    for o in outcomes:
        point = safe_float(o.get("point"))
        if point != 2.5:
            continue
        name = str(o.get("name", "")).lower()
        price = safe_float(o.get("price"))
        if name == "over":
            m["OVER_2_5"] = price
        elif name == "under":
            m["UNDER_2_5"] = price
    return m

def normalize_events(raw_events: list, show_all_bookmakers: bool) -> Dict[str, Any]:
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
            "markets": {"h2h": {}, "totals_2_5": {}},
        }

        for bm in ev.get("bookmakers", []):
            bm_key = bm.get("key")

            if (not show_all_bookmakers) and (bm_key not in TOP10_BOOKMAKERS):
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
                    m = normalize_totals_2_5(outcomes)
                    if m:
                        out["markets"]["totals_2_5"][bm_key] = {
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
        for market_key in ["h2h", "totals_2_5"]:
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
# 5) 렌더 (변화 있을 때만 표시)
# =========================
def fmt_cell(o: dict) -> str:
    if not o or o.get("price") is None:
        return "<span class='flat'>-</span>"

    price = float(o["price"])
    base = f"<span class='mono'>{price:.3f}</span>"

    d = o.get("delta")
    dirn = o.get("direction")

    if d is None or dirn is None:
        return base
    if abs(d) < 1e-12:
        return base

    if dirn == "UP":
        return base + f" <span class='up'>▲</span> <span class='mono up'>{d:+.2f}</span>"
    if dirn == "DOWN":
        return base + f" <span class='down'>▼</span> <span class='mono down'>{d:+.2f}</span>"

    return base

def dedup_by_title_keep_latest(bms: List[dict]) -> List[dict]:
    best = {}
    for bm in bms:
        t = (bm.get("title") or bm.get("bookmaker_key") or "").strip()
        lu = bm.get("last_update_utc") or ""
        if t not in best or lu > (best[t].get("last_update_utc") or ""):
            best[t] = bm
    return list(best.values())

def render_market_table_html(market: Dict[str, Any], cols: List[Tuple[str, str]]) -> str:
    bms = list(market.values())
    if not bms:
        return "<div class='small'>데이터 없음</div>"

    bms = dedup_by_title_keep_latest(bms)
    bms.sort(key=lambda x: (x.get("title") or "").lower())

    ths = "<th>Bookmaker</th>" + "".join([f"<th class='r'>{label}</th>" for _, label in cols])

    rows = []
    for bm in bms:
        title = bm.get("title") or bm.get("bookmaker_key")
        outcomes = bm.get("outcomes") or {}

        tds = [f"<td>{title}</td>"]
        for k, _label in cols:
            tds.append(f"<td class='r'>{fmt_cell(outcomes.get(k))}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")

    return f"""
    <div class="tblwrap">
      <table class="tbl">
        <thead><tr>{ths}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


# =========================
# 6) UI
# =========================
st.title("EPL Odds Tracker")
st.caption("가독성 버전: 표는 라이트(흰색), 변화 있을 때만 ▲▼ + 변화량 표시 (데이터 60초 캐시)")

auto = st.toggle("Auto refresh (15s rerun)", value=True)
if auto:
    st_autorefresh(interval=15_000, key="auto_refresh")

c1, c2, c3 = st.columns([2, 2, 2])
with c1:
    team_filter = st.selectbox("팀 필터", ["전체"] + EPL_TEAMS_20, index=0)
with c2:
    show_all_bookmakers = st.toggle("전체 북메이커 보기(추천)", value=True)
with c3:
    if st.button("지금 갱신(캐시 무시)"):
        fetch_odds_cached.clear()
        st.toast("캐시 초기화 완료.")

res = fetch_odds_cached()
if not res["ok"]:
    st.error(f"API 호출 실패: {res['error']}")
    st.stop()

st.success(f"Fetched (UTC): {res['fetched_utc']} / Events: {len(res['data'])}")

curr_events = normalize_events(res["data"], show_all_bookmakers=show_all_bookmakers)

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
    "<div class='small'>표시 규칙: <span class='up'>▲</span> 상승 / <span class='down'>▼</span> 하락. "
    "변화가 0이면 아무것도 안 붙음. 변화량은 <b>+0.05</b> 형식(2자리).</div>",
    unsafe_allow_html=True
)

if not events_list:
    st.info("표시할 경기가 없습니다.")
    st.stop()

for ev in events_list:
    home = ev.get("home_team")
    away = ev.get("away_team")
    kickoff = fmt_time(ev.get("commence_time_utc"))

    st.subheader(f"{home} vs {away}")
    st.markdown(f"<div class='kick'>Kickoff: <span class='mono'>{kickoff}</span></div>", unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")

    with left:
        st.write("### 1X2 (승/무/패)")
        h2h_cols = [("HOME", "Home(1)"), ("DRAW", "Draw(X)"), ("AWAY", "Away(2)")]
        st.markdown(render_market_table_html(ev["markets"].get("h2h", {}), h2h_cols), unsafe_allow_html=True)

    with right:
        st.write("### O/U 2.5 (언오버)")
        ou_cols = [("OVER_2_5", "Over 2.5"), ("UNDER_2_5", "Under 2.5")]
        st.markdown(render_market_table_html(ev["markets"].get("totals_2_5", {}), ou_cols), unsafe_allow_html=True)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
