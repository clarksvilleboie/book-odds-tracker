import os
import json
import time
import sqlite3
from datetime import datetime, timezone, timedelta

import requests
import pandas as pd
import streamlit as st


# =========================================================
# 1) 기본 설정
# =========================================================
APP_TITLE = "EPL Odds Movement Dashboard"
DB_PATH = "odds_snapshots.sqlite3"

# 너가 사용하는 API 키/호스트/엔드포인트를 여기에 넣거나,
# Streamlit Secrets(.streamlit/secrets.toml)로 관리해도 됨.
API_KEY = e2d960a84ee7d4f9fd5481eda30ac918("ODDS_API_KEY", "")
API_HOST = os.getenv("ODDS_API_HOST", "")
API_BASE_URL = os.getenv("ODDS_API_BASE_URL", "")

# EPL 20개 팀 (표준명)
EPL_TEAMS = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
    "Leicester City", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Southampton", "Tottenham Hotspur",
    "West Ham United", "Wolverhampton Wanderers"
]

# 팀명 흔들림(별칭) 표준화 매핑
TEAM_ALIASES = {
    "Man City": "Manchester City",
    "Manchester City FC": "Manchester City",
    "Man United": "Manchester United",
    "Manchester Utd": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Wolves": "Wolverhampton Wanderers",
    "Nott'm Forest": "Nottingham Forest",
    "Notts Forest": "Nottingham Forest",
    "Brighton & Hove Albion": "Brighton",
    "Ipswich": "Ipswich Town",
}

# (선택) 팀 로고 URL 매핑 (너가 원하는 이미지로 갈아끼우면 됨)
TEAM_LOGOS = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg",
    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Brighton": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/0/0c/Crystal_Palace_FC_logo.svg",
    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Fulham": "https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg",
    "Ipswich Town": "https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg",
    "Leicester City": "https://upload.wikimedia.org/wikipedia/en/6/63/Leicester02.png",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Newcastle United": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Nottingham Forest": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg",
    "Southampton": "https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg",
    "Tottenham Hotspur": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
    "West Ham United": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    "Wolverhampton Wanderers": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
}


# =========================================================
# 2) 유틸 함수
# =========================================================
def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def normalize_team(name: str) -> str:
    if not name:
        return name
    name = name.strip()
    return TEAM_ALIASES.get(name, name)

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        captured_at TEXT NOT NULL,
        provider TEXT NOT NULL,
        league TEXT NOT NULL,
        market TEXT NOT NULL,
        bookmaker TEXT NOT NULL,
        match_id TEXT NOT NULL,
        kickoff_at TEXT,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        selection TEXT NOT NULL,
        odds REAL NOT NULL
    );
    """)

    # 조회 성능 인덱스
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_time ON snapshots(captured_at);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_match ON snapshots(match_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_teams ON snapshots(home_team, away_team);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_market ON snapshots(market, bookmaker);")

    conn.commit()
    conn.close()

def insert_rows(rows: list[dict]):
    if not rows:
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executemany("""
    INSERT INTO snapshots (
        captured_at, provider, league, market, bookmaker, match_id, kickoff_at,
        home_team, away_team, selection, odds
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, [
        (
            r["captured_at"], r["provider"], r["league"], r["market"], r["bookmaker"],
            r["match_id"], r.get("kickoff_at"),
            r["home_team"], r["away_team"], r["selection"], float(r["odds"])
        )
        for r in rows
    ])

    conn.commit()
    n = cur.rowcount
    conn.close()
    return n

def read_snapshots(time_window_hours: int = 48) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    since = (datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).replace(microsecond=0).isoformat()
    df = pd.read_sql_query(
        "SELECT * FROM snapshots WHERE captured_at >= ?",
        conn,
        params=(since,)
    )
    conn.close()
    return df

def compute_movement(df: pd.DataFrame, lookback_minutes: int = 60) -> pd.DataFrame:
    """
    최신 스냅샷(각 key별 가장 최근) vs (lookback_minutes 전 시점에 가장 가까운 스냅샷) 비교.
    key = provider, league, market, bookmaker, match_id, selection
    """
    if df.empty:
        return df

    df = df.copy()
    df["captured_at_dt"] = pd.to_datetime(df["captured_at"], utc=True, errors="coerce")
    df["kickoff_at_dt"] = pd.to_datetime(df["kickoff_at"], utc=True, errors="coerce")

    key_cols = ["provider", "league", "market", "bookmaker", "match_id", "selection"]

    # 최신값
    latest = (
        df.sort_values("captured_at_dt")
          .groupby(key_cols, as_index=False)
          .tail(1)
    )

    # 과거 기준 시점
    target_time = latest["captured_at_dt"].max() - pd.Timedelta(minutes=lookback_minutes)

    # target_time 이전 중 가장 가까운 값
    past_candidates = df[df["captured_at_dt"] <= target_time].copy()
    if past_candidates.empty:
        latest["odds_past"] = pd.NA
        latest["delta"] = pd.NA
        latest["pct_change"] = pd.NA
        return latest

    past = (
        past_candidates.sort_values("captured_at_dt")
                      .groupby(key_cols, as_index=False)
                      .tail(1)
                      .rename(columns={"odds": "odds_past", "captured_at": "captured_at_past"})
    )

    merged = latest.merge(
        past[key_cols + ["odds_past", "captured_at_past"]],
        on=key_cols,
        how="left"
    )

    merged["delta"] = merged["odds"] - merged["odds_past"]
    merged["pct_change"] = (merged["delta"] / merged["odds_past"]) * 100.0
    return merged


# =========================================================
# 3) API 어댑터(여기만 너 API에 맞춰 수정하면 됨)
# =========================================================
def fetch_odds_from_provider(
    provider: str,
    league: str = "EPL",
    market: str = "1X2",
) -> list[dict]:
    """
    반환 형식(표준):
    [
      {
        "provider": "YOUR_PROVIDER",
        "league": "EPL",
        "market": "1X2",
        "bookmaker": "bet365",
        "match_id": "12345",
        "kickoff_at": "2026-02-15T15:00:00+00:00",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "selection": "HOME" | "DRAW" | "AWAY",
        "odds": 1.95
      },
      ...
    ]
    """

    # -------------------------------------------------------
    # ✅ TODO: 여기부터 너가 쓰는 API로 바꾸면 된다.
    # 예시로는 "더미 데이터"를 반환하도록 해놨음.
    # -------------------------------------------------------
    captured_at = now_utc_iso()

    dummy = [
        {
            "captured_at": captured_at,
            "provider": provider,
            "league": league,
            "market": market,
            "bookmaker": "dummybook",
            "match_id": "EPL_ARS_CHE_2026-02-15",
            "kickoff_at": "2026-02-15T15:00:00+00:00",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "selection": "HOME",
            "odds": 1.92
        },
        {
            "captured_at": captured_at,
            "provider": provider,
            "league": league,
            "market": market,
            "bookmaker": "dummybook",
            "match_id": "EPL_ARS_CHE_2026-02-15",
            "kickoff_at": "2026-02-15T15:00:00+00:00",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "selection": "DRAW",
            "odds": 3.60
        },
        {
            "captured_at": captured_at,
            "provider": provider,
            "league": league,
            "market": market,
            "bookmaker": "dummybook",
            "match_id": "EPL_ARS_CHE_2026-02-15",
            "kickoff_at": "2026-02-15T15:00:00+00:00",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "selection": "AWAY",
            "odds": 4.10
        },
    ]

    # 팀명 정규화
    for r in dummy:
        r["home_team"] = normalize_team(r["home_team"])
        r["away_team"] = normalize_team(r["away_team"])

    return dummy


# =========================================================
# 4) Streamlit UI
# =========================================================
def sidebar_controls():
    st.sidebar.header("Filters")

    provider = st.sidebar.selectbox("Provider", ["DEMO_PROVIDER"], index=0)
    market = st.sidebar.selectbox("Market", ["1X2", "OU_2.5", "AH_0"], index=0)

    lookback = st.sidebar.selectbox("Lookback", ["15m", "60m", "6h", "24h"], index=1)
    lookback_map = {"15m": 15, "60m": 60, "6h": 360, "24h": 1440}

    window_hours = st.sidebar.selectbox("History Window", [24, 48, 72, 168], index=1)

    team_filter = st.sidebar.multiselect("Teams (home/away)", EPL_TEAMS, default=[])

    only_upcoming = st.sidebar.checkbox("Only upcoming matches", value=True)

    return {
        "provider": provider,
        "market": market,
        "lookback_minutes": lookback_map[lookback],
        "window_hours": window_hours,
        "team_filter": team_filter,
        "only_upcoming": only_upcoming
    }

def ui_header():
    st.title(APP_TITLE)
    st.caption("Stores odds snapshots → computes movement over time → visualizes movers & timelines.")

def ui_refresh_button(cfg):
    col1, col2, col3 = st.columns([1,1,3])
    with col1:
        if st.button("📥 Fetch & Save Snapshot", use_container_width=True):
            rows = fetch_odds_from_provider(
                provider=cfg["provider"],
                league="EPL",
                market=cfg["market"]
            )
            # captured_at 필드 없으면 채우기
            captured = now_utc_iso()
            for r in rows:
                if "captured_at" not in r:
                    r["captured_at"] = captured
            n = insert_rows(rows)
            st.success(f"Saved {n} rows into DB.")
    with col2:
        if st.button("🧹 Reset DB", use_container_width=True):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            ensure_db()
            st.warning("DB reset done.")
    with col3:
        st.write("DB:", os.path.abspath(DB_PATH))

def apply_filters(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    # 팀 필터(홈/원정 포함)
    if cfg["team_filter"]:
        out = out[
            out["home_team"].isin(cfg["team_filter"]) |
            out["away_team"].isin(cfg["team_filter"])
        ]

    # 업커밍 경기만
    if cfg["only_upcoming"]:
        kickoff = pd.to_datetime(out["kickoff_at"], utc=True, errors="coerce")
        out = out[kickoff >= datetime.now(timezone.utc) - timedelta(minutes=5)]

    return out

def show_top_movers(mv: pd.DataFrame):
    st.subheader("Top Movers")
    if mv.empty or "delta" not in mv.columns:
        st.info("Not enough history yet. Fetch snapshots a few times, then check movers.")
        return

    mv2 = mv.copy()
    mv2["abs_delta"] = mv2["delta"].abs()
    mv2 = mv2.sort_values("abs_delta", ascending=False)

    cols = [
        "kickoff_at", "home_team", "away_team",
        "market", "bookmaker", "selection",
        "odds_past", "odds", "delta", "pct_change",
        "captured_at_past", "captured_at"
    ]
    cols = [c for c in cols if c in mv2.columns]
    st.dataframe(mv2[cols].head(30), use_container_width=True)

def show_match_detail(df_all: pd.DataFrame, cfg: dict):
    st.subheader("Match Detail (Time Series)")

    if df_all.empty:
        st.info("No data. Fetch a snapshot first.")
        return

    # match 선택
    df_all = df_all.copy()
    df_all["match_label"] = df_all["home_team"] + " vs " + df_all["away_team"] + " | " + df_all["match_id"]
    match_ids = df_all["match_label"].dropna().unique().tolist()
    match_label = st.selectbox("Select a match", match_ids, index=0)

    chosen = df_all[df_all["match_label"] == match_label].copy()
    if chosen.empty:
        st.info("No rows for this match.")
        return

    # selection 선택
    selections = sorted(chosen["selection"].unique().tolist())
    selection = st.selectbox("Selection", selections, index=0)

    chosen = chosen[chosen["selection"] == selection].copy()
    chosen["captured_at_dt"] = pd.to_datetime(chosen["captured_at"], utc=True, errors="coerce")
    chosen = chosen.sort_values("captured_at_dt")

    st.write("Rows:", len(chosen))

    # 라인차트(기본 streamlit)
    chart_df = chosen[["captured_at_dt", "odds", "bookmaker"]].copy()
    chart_df = chart_df.rename(columns={"captured_at_dt": "time"})
    # bookmaker가 여러개면 pivot
    pivot = chart_df.pivot_table(index="time", columns="bookmaker", values="odds", aggfunc="last")
    st.line_chart(pivot)

    st.dataframe(chosen[[
        "captured_at", "kickoff_at", "bookmaker", "market", "selection", "odds"
    ]], use_container_width=True)

def show_team_cards(cfg: dict):
    st.subheader("EPL Teams")
    cols = st.columns(5)
    for i, team in enumerate(EPL_TEAMS):
        with cols[i % 5]:
            logo = TEAM_LOGOS.get(team)
            if logo:
                st.image(logo, width=70)
            st.markdown(f"**{team}**")

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    ensure_db()

    ui_header()
    cfg = sidebar_controls()
    ui_refresh_button(cfg)

    # Load + filter
    raw = read_snapshots(time_window_hours=cfg["window_hours"])
    filtered = apply_filters(raw, cfg)

    # Movement
    mv = compute_movement(filtered, lookback_minutes=cfg["lookback_minutes"])

    tab1, tab2, tab3 = st.tabs(["📈 Movers", "🕒 Match Detail", "🧩 Teams"])

    with tab1:
        show_top_movers(mv)

    with tab2:
        show_match_detail(filtered, cfg)

    with tab3:
        show_team_cards(cfg)

    st.divider()
    st.caption("Tip: Movers need history. Click 'Fetch & Save Snapshot' multiple times over time (or schedule externally).")

if __name__ == "__main__":
    main()
