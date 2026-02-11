import os
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

import httpx
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# =========================
# ✅ 기본 설정
# =========================
st.set_page_config(page_title="EPL Odds Dashboard (Streamlit MVP)", layout="wide")

ODDS_API_KEY = (
    st.secrets.get("ODDS_API_KEY", None)
    if hasattr(st, "secrets")
    else None
) or os.getenv("ODDS_API_KEY") or "e2d960a84ee7d960a84ee7d4f9fd5481eda30ac918"

# 너가 준 키(정상): e2d960a84ee7d4f9fd5481eda30ac918
# 위 줄은 혹시 오타/환경변수 없을 때 대비용. 아래에서 다시 안전하게 덮어씀.
if ODDS_API_KEY.endswith("..."):
    ODDS_API_KEY = "e2d960a84ee7d4f9fd5481eda30ac918"

SPORT_KEY = "soccer_epl"
REGIONS = "uk,eu"            # 필요하면 "us,uk,eu" 로 변경
ODDS_FORMAT = "decimal"
MARKETS = "h2h,totals"       # 1X2 + totals(언오버)

ODDS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"

# “상위 10개” 후보. 실제 응답에 존재하는 것만 화면에 뜸.
TOP10_BOOKMAKERS = [
    "bet365", "pinnacle", "williamhill", "unibet", "ladbrokes",
    "paddypower", "betfair", "betvictor", "1xbet", "betsson"
]

# 필터용 EPL 20팀 (시즌마다 바뀜 -> 여기만 바꾸면 됨)
EPL_TEAMS_20 = [
    "Arsenal",
    "Manchester City",
    "Liverpool",
    "Chelsea",
    "Manchester United",
    "Tottenham",
    "Newcastle United",
    "Aston Villa",
    "Brighton",
    "West Ham",
    "Brentford",
    "Wolves",
    "Fulham",
    "Crystal Palace",
    "Bournemouth",
    "Everton",
    "Nottingham Forest",
    "Leicester City",
    "Southampton",
    "Ipswich Town",
]


# =========================
# ✅ 유틸
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
    """
    returns (prev_price, delta, direction)
    direction: UP / DOWN / UNCHANGED / None
    """
    if prev is None or curr is None:
        return prev, None, None
    d = curr - prev
    if abs(d) < 1e-12:
        return prev, 0.0, "UNCHANGED"
    return prev, d, "UP" if d > 0 else "DOWN"

def normalize_h2h(home: str, away: str, outcomes: list) -> Dict[str, float]:
    """
    HOME / DRAW / AWAY 로 정규화
    """
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
    """
    totals 중 point==2.5 만 저장
    OVER_2_5 / UNDER_2_5
    """
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

def format_time(iso: str) -> str:
    if not iso:
        return "-"
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # 로컬 시간 표시(대충 보기 좋게)
        return d.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


# =========================
# ✅ Odds API 호출 (1분 TTL 캐시)
# =========================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_odds_cached() -> Dict[str, Any]:
    """
    60초 동안 캐시. 즉, 스케줄러 없이도 '1분마다 업데이트'가 됨.
    (Streamlit 특성상 계속 실행 중인 백그라운드 스케줄러를 굳이 안 돌리는 게 안정적)
    """
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso",
    }
    try:
        with httpx.Client(timeout=25) as client:
            r = client.get(ODDS_URL, params=params)
            r.raise_for_status()
            data = r.json()
        return {"ok": True, "data": data, "fetched_utc": utc_now_iso(), "error": None}
    except Exception as e:
        return {"ok": False, "data": [], "fetched_utc": utc_now_iso(), "error": str(e)}


def normalize_events(raw_events: list) -> Dict[str, Any]:
    """
    raw -> normalized
    events[event_id] = {
      home_team, away_team, commence_time_utc,
      markets: { h2h: {bm_key: {...}}, totals_2_5: {...} }
    }
    """
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
            if bm_key not in TOP10_BOOKMAKERS:
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
    """
    prev 대비 변화값 붙여서 반환.
    curr_events 그대로 구조 유지하되 outcomes 값을
    { price, prev_price, delta, direction } 로 바꿈.
    """
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
# ✅ UI (CSS)
# =========================
st.markdown(
    """
<style>
.small { font-size: 12px; color: #94a3b8; }
.badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; }
.badge-ok { background:#064e3b; color:#d1fae5; border:1px solid #065f46; }
.badge-err { background:#7f1d1d; color:#fee2e2; border:1px solid #991b1b; }
.arrow-up { color:#f87171; font-weight:800; }
.arrow-down { color:#38bdf8; font-weight:800; }
.arrow-flat { color:#64748b; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.card { border:1px solid rgba(148,163,184,0.2); border-radius:16px; padding:16px; background: rgba(15,23,42,0.6); }
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# ✅ Header
# =========================
colA, colB = st.columns([3, 1])
with colA:
    st.title("EPL Odds Dashboard (Streamlit MVP)")
    st.caption("1X2 + O/U 2.5, 북메이커 10개 비교, 직전 대비 ▲▼ (1분 캐시 기반 업데이트)")
with colB:
    # 화면 자동 새로고침(프론트) - 15초마다 rerun
    auto = st.toggle("Auto refresh", value=True)
    if auto:
        st_autorefresh(interval=15_000, key="auto_refresh")  # 15초마다 화면 rerun


# =========================
# ✅ Controls
# =========================
c1, c2, c3 = st.columns([2, 2, 2])
with c1:
    team_filter = st.selectbox("팀 필터 (경기 포함 팀)", ["전체"] + EPL_TEAMS_20, index=0)
with c2:
    st.write(" ")
    manual = st.button("지금 갱신(캐시 무시)")
with c3:
    st.write(" ")
    st.caption("팁: 북메이커가 적게 뜨면 REGIONS를 'us,uk,eu'로 바꿔봐.")

# 캐시 무시 버튼
if manual:
    fetch_odds_cached.clear()
    st.toast("캐시 초기화 완료. 다음 로드에서 새로 받아옴.")


# =========================
# ✅ Data Load
# =========================
res = fetch_odds_cached()
meta_col1, meta_col2, meta_col3 = st.columns([2, 2, 2])

with meta_col1:
    if res["ok"]:
        st.markdown(f"<span class='badge badge-ok'>OK</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge badge-err'>ERROR</span>", unsafe_allow_html=True)

with meta_col2:
    st.markdown(f"<div class='small'>Fetched (UTC): <span class='mono'>{res['fetched_utc']}</span></div>", unsafe_allow_html=True)

with meta_col3:
    if not res["ok"]:
        st.markdown(f"<div class='small'>Error: {res['error']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='small'>Regions: <span class='mono'>{REGIONS}</span> / Markets: <span class='mono'>{MARKETS}</span></div>", unsafe_allow_html=True)

raw_events = res["data"] if res["ok"] else []


# =========================
# ✅ Normalize + Delta 비교
# =========================
curr_events = normalize_events(raw_events)

if "prev_events" not in st.session_state:
    st.session_state.prev_events = {}

events_with_delta = compute_delta(curr_events, st.session_state.prev_events)

# 다음 rerun에서 “직전”이 되도록 저장
st.session_state.prev_events = copy.deepcopy(curr_events)


# =========================
# ✅ Team filter 적용 + 정렬
# =========================
events_list = list(events_with_delta.values())

if team_filter != "전체":
    tf = team_filter.lower()
    events_list = [
        e for e in events_list
        if tf in (e.get("home_team", "").lower()) or tf in (e.get("away_team", "").lower())
    ]

events_list.sort(key=lambda e: e.get("commence_time_utc") or "")


# =========================
# ✅ Rendering helpers
# =========================
def arrow_html(dirn: Optional[str]) -> str:
    if dirn == "UP":
        return "<span class='arrow-up'>▲</span>"
    if dirn == "DOWN":
        return "<span class='arrow-down'>▼</span>"
    if dirn == "UNCHANGED":
        return "<span class='arrow-flat'>—</span>"
    return "<span class='arrow-flat'>—</span>"

def fmt_price_block(obj: dict) -> str:
    if not obj or obj.get("price") is None:
        return "<span class='small'>-</span>"
    p = obj["price"]
    try:
        p_txt = f"{float(p):.3f}"
    except Exception:
        p_txt = str(p)

    return f"<span class='mono'>{p_txt}</span> {arrow_html(obj.get('direction'))}"

def render_market_table(market: dict, cols: List[Tuple[str, str]]) -> str:
    """
    market: { bm_key: {title, outcomes{...}} }
    cols: [(outcome_key, label), ...]
    """
    bms = list(market.values())
    if not bms:
        return "<div class='small'>데이터 없음</div>"

    # 정렬: title 기준
    bms.sort(key=lambda x: (x.get("title") or "").lower())

    head = "<tr><th style='text-align:left; padding:8px;'>Bookmaker</th>" + "".join(
        [f"<th style='text-align:right; padding:8px;'>{label}</th>" for _, label in cols]
    ) + "</tr>"

    rows = []
    for bm in bms:
        title = bm.get("title") or bm.get("bookmaker_key")
        outcomes = bm.get("outcomes") or {}
        tds = [f"<td style='text-align:right; padding:8px;'>{fmt_price_block(outcomes.get(k))}</td>" for k, _ in cols]
        row = f"<tr style='border-top:1px solid rgba(148,163,184,0.2);'><td style='padding:8px; white-space:nowrap;'>{title}</td>{''.join(tds)}</tr>"
        rows.append(row)

    table = f"""
<div style="overflow-x:auto; border:1px solid rgba(148,163,184,0.2); border-radius:16px;">
  <table style="width:100%; min-width:720px; border-collapse:collapse;">
    <thead style="background:rgba(2,6,23,0.6);">{head}</thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
"""
    return table


# =========================
# ✅ Main
# =========================
st.markdown(
    "<div class='small'>표시 규칙: <span class='arrow-up'>▲(빨강)=배당 상승</span>, "
    "<span class='arrow-down'>▼(파랑)=배당 하락</span>, <span class='arrow-flat'>—=변화 없음/첫 수집</span></div>",
    unsafe_allow_html=True
)

if not events_list:
    st.info("현재 표시할 경기가 없음 (필터/시간/응답 범위 확인).")
    st.stop()

for ev in events_list:
    home = ev.get("home_team")
    away = ev.get("away_team")
    t = format_time(ev.get("commence_time_utc"))

    st.markdown(
        f"""
<div class="card">
  <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
    <div style="font-size:18px; font-weight:800;">{home} <span class="small">vs</span> {away}</div>
    <div class="small">Kickoff: <span class="mono">{t}</span></div>
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    c_left, c_right = st.columns(2, gap="large")

    # 1X2
    with c_left:
        st.subheader("1X2 (승/무/패)")
        h2h_cols = [("HOME", "Home(1)"), ("DRAW", "Draw(X)"), ("AWAY", "Away(2)")]
        h2h_html = render_market_table(ev["markets"].get("h2h", {}), h2h_cols)
        st.markdown(h2h_html, unsafe_allow_html=True)

    # O/U 2.5
    with c_right:
        st.subheader("O/U 2.5 (언오버)")
        ou_cols = [("OVER_2_5", "Over 2.5"), ("UNDER_2_5", "Under 2.5")]
        ou_html = render_market_table(ev["markets"].get("totals_2_5", {}), ou_cols)
        st.markdown(ou_html, unsafe_allow_html=True)

    st.write("")  # spacing
