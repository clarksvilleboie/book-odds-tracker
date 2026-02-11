import os
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

import httpx
import pandas as pd
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

# ✅ 시장
REGIONS = "uk,eu"
ODDS_FORMAT = "decimal"
MARKETS = "h2h,totals"  # 1X2 + totals(O/U)

# ✅ 10개 업체 (응답에 있는 것만 표시됨)
TOP10_BOOKMAKERS = [
    "bet365", "pinnacle", "williamhill", "unibet", "ladbrokes",
    "paddypower", "betfair", "betvictor", "1xbet", "betsson"
]

# ✅ 팀 필터(실제 데이터에서 자동 추출도 가능하지만, MVP는 고정 리스트)
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
# 1) 유틸
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

def arrow(dirn: Optional[str]) -> str:
    if dirn == "UP":
        return "▲"
    if dirn == "DOWN":
        return "▼"
    return "—"

def fmt_time(iso: str) -> str:
    if not iso:
        return "-"
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


# =========================
# 2) API 호출 (1분 캐시 = “1분 업데이트”)
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
# 3) 정규화 (UI용 구조 만들기)
# =========================
def normalize_h2h(home: str, away: str, outcomes: list) -> Dict[str, float]:
    # HOME / DRAW / AWAY
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
    # totals 중 point==2.5 만: OVER_2_5 / UNDER_2_5
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
            "markets": {"h2h": {}, "totals_2_5": {}},
        }

        for bm in ev.get("bookmakers", []):
            bm_key = bm.get("key")
            # top10만(원하면 이 필터 꺼도 됨)
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
# 4) UI
# =========================
st.title("EPL Odds Tracker")
st.caption("1X2 + O/U 2.5, 상위 10개 업체 비교, 직전 대비 ▲▼ 표시 (데이터 60초 캐시)")

# 자동 새로고침 (화면은 15초마다 리렌더 / 데이터는 60초 TTL)
auto = st.toggle("Auto refresh", value=True)
if auto:
    st_autorefresh(interval=15_000, key="auto_refresh")

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    team_filter = st.selectbox("팀 필터", ["전체"] + EPL_TEAMS_20, index=0)
with col2:
    show_all_bookmakers = st.toggle("Top10 필터 끄기(전체 보기)", value=False)
with col3:
    if st.button("지금 갱신(캐시 무시)"):
        fetch_odds_cached.clear()
        st.toast("캐시 초기화 완료. 다음 로드에서 새로 받아옵니다.")

# top10 필터 끄면, 그냥 저장할 때부터 전체를 쓰는 게 맞지만
# MVP에서는 normalize단계에서 top10 필터를 쓰고 있으니,
# 토글을 켜면 “top10 리스트를 임시로 비움” 방식으로 처리
if show_all_bookmakers:
    TOP10_BOOKMAKERS[:] = []  # 비우면 필터가 사실상 해제됨(아래 normalize에서 조건 바꿀 거라서)
    # 위 줄이 싫으면, 아래 normalize 조건을 if show_all_bookmakers: continue 제거 형태로 바꾸면 됨.

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

st.markdown("**표시 규칙:** ▲=배당 상승 / ▼=배당 하락 / —=변화 없음 또는 첫 수집")

if not events_list:
    st.info("표시할 경기가 없습니다.")
    st.stop()


def market_to_df(market: Dict[str, Any], cols: List[Tuple[str, str]]) -> pd.DataFrame:
    """
    cols: [(key,label)]
    """
    rows = []
    for bm_key, bm in market.items():
        row = {"Bookmaker": bm.get("title") or bm_key}
        outcomes = bm.get("outcomes", {})
        for ok, label in cols:
            o = outcomes.get(ok)
            if not o or o.get("price") is None:
                row[label] = "-"
            else:
                p = float(o["price"])
                row[label] = f"{p:.3f} {arrow(o.get('direction'))}"
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.sort_values("Bookmaker")


for ev in events_list:
    home = ev.get("home_team")
    away = ev.get("away_team")
    kickoff = fmt_time(ev.get("commence_time_utc"))

    st.subheader(f"{home} vs {away}")
    st.caption(f"Kickoff: {kickoff}")

    cL, cR = st.columns(2)

    with cL:
        st.write("### 1X2 (승/무/패)")
        h2h_cols = [("HOME", "Home(1)"), ("DRAW", "Draw(X)"), ("AWAY", "Away(2)")]
        df_h2h = market_to_df(ev["markets"].get("h2h", {}), h2h_cols)
        if df_h2h.empty:
            st.info("1X2 데이터 없음")
        else:
            st.dataframe(df_h2h, use_container_width=True, hide_index=True)

    with cR:
        st.write("### O/U 2.5 (언오버)")
        ou_cols = [("OVER_2_5", "Over 2.5"), ("UNDER_2_5", "Under 2.5")]
        df_ou = market_to_df(ev["markets"].get("totals_2_5", {}), ou_cols)
        if df_ou.empty:
            st.info("O/U 2.5 데이터 없음")
        else:
            st.dataframe(df_ou, use_container_width=True, hide_index=True)

    st.divider()
