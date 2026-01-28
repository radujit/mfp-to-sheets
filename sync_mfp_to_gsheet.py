import os
import json
from datetime import date, timedelta

import requests
import gspread
from google.oauth2.service_account import Credentials


# =====================
# CONFIG
# =====================
COLUMNS = ["Date", "Calories", "Carbs", "Fat", "Protein", "Sodium", "Sugar"]
MFP_BASE = "https://www.myfitnesspal.com"


# =====================
# GOOGLE SHEETS
# =====================
def gs_client():
    info = json.loads(os.environ["GCP_SA_JSON"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


# =====================
# MFP SESSION (NextAuth)
# =====================
def mfp_session_from_cookies():
    raw = os.environ["MFP_COOKIES"]
    s = requests.Session()

    # User-Agent realist (important)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": MFP_BASE + "/",
        "Origin": MFP_BASE,
    })

    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            s.cookies.set(k.strip(), v.strip(), domain=".myfitnesspal.com", path="/")

    return s


# =====================
# FETCH DAILY TOTALS
# =====================
def fetch_day_totals(session, d: date):
    # Endpoint intern folosit de UI (JSON)
    # IMPORTANT: acesta funcționează cu NextAuth cookies
    url = (
        f"{MFP_BASE}/reports/nutrition.json"
        f"?date={d.isoformat()}"
    )

    r = session.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"MFP HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()

    # Structură defensivă (MFP mai schimbă chei)
    totals = data.get("totals", {}) or {}

    return {
        "calories": totals.get("calories", ""),
        "carbohydrates": totals.get("carbohydrates", ""),
        "fat": totals.get("fat", ""),
        "protein": totals.get("protein", ""),
        "sodium": totals.get("sodium", ""),
        "sugar": totals.get("sugar", ""),
    }


# =====================
# MAIN
# =====================
def main():
    # Sheets
    gc = gs_client()
    sh = gc.open_by_key(os.environ["GSHEET_ID"])
    ws = sh.worksheet(os.environ["GSHEET_TAB"])

    if ws.row_values(1) != COLUMNS:
        ws.update("A1:G1", [COLUMNS])

    # MFP
    session = mfp_session_from_cookies()

    # Sync yesterday + today (safe)
    days = [date.today() - timedelta(days=1), date.today()]

    dates_col = ws.col_values(1)

    for d in days:
        t = fetch_day_totals(session, d)

        row = [
            d.isoformat(),
            t["calories"],
            t["carbohydrates"],
            t["fat"],
            t["protein"],
            t["sodium"],
            t["sugar"],
        ]

        if row[0] in dates_col:
            i = dates_col.index(row[0]) + 1
            ws.update(f"A{i}:G{i}", [row])
        else:
            ws.append_row(row, value_input_option="USER_ENTERED")

    print("SYNC OK")


if __name__ == "__main__":
    main()
