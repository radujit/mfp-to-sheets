import os
import json
from datetime import date, timedelta

import gspread
from google.oauth2.service_account import Credentials
import myfitnesspal

from http.cookiejar import CookieJar
from requests.cookies import create_cookie


# ===== CONFIG =====
COLUMNS = ["Date", "Calories", "Carbs", "Fat", "Protein", "Sodium", "Sugar"]


# ===== GOOGLE SHEETS =====
def gs_client():
    info = json.loads(os.environ["GCP_SA_JSON"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


# ===== MFP CLIENT (COOKIES) =====
def mfp_client_from_cookies():
    raw = os.environ["MFP_COOKIES"]

    cj = CookieJar()

    for line in raw.splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            cj.set_cookie(
                create_cookie(
                    name=name.strip(),
                    value=value.strip(),
                    domain=".myfitnesspal.com",
                    path="/"
                )
            )

    return myfitnesspal.Client(cookiejar=cj)


# ===== MAIN =====
def main():
    # Google Sheets
    gc = gs_client()
    sh = gc.open_by_key(os.environ["GSHEET_ID"])
    ws = sh.worksheet(os.environ["GSHEET_TAB"])

    # Header
    if ws.row_values(1) != COLUMNS:
        ws.update("A1:G1", [COLUMNS])

    # MyFitnessPal
    client = mfp_client_from_cookies()

    # Sync yesterday + today
    days = [date.today() - timedelta(days=1), date.today()]

    for d in days:
        day = client.get_date(d.year, d.month, d.day)
        t = day.totals or {}

        row = [
            d.isoformat(),
            t.get("calories", ""),
            t.get("carbohydrates", ""),
            t.get("fat", ""),
            t.get("protein", ""),
            t.get("sodium", ""),
            t.get("sugar", ""),
        ]

        dates = ws.col_values(1)

        if row[0] in dates:
            i = dates.index(row[0]) + 1
            ws.update(f"A{i}:G{i}", [row])
        else:
            ws.append_row(row, value_input_option="USER_ENTERED")

    print("SYNC OK")


if __name__ == "__main__":
    main()
