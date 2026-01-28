import os, json
from datetime import date, timedelta

import gspread
from google.oauth2.service_account import Credentials
import myfitnesspal

COLUMNS = ["Date", "Calories", "Carbs", "Fat", "Protein", "Sodium", "Sugar"]

def gs_client():
    info = json.loads(os.environ["GCP_SA_JSON"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

def main():
    gc = gs_client()
    sh = gc.open_by_key(os.environ["GSHEET_ID"])
    ws = sh.worksheet(os.environ["GSHEET_TAB"])

    if ws.row_values(1) != COLUMNS:
        ws.update("A1:G1", [COLUMNS])

    client = myfitnesspal.Client(
        os.environ["MFP_USERNAME"],
        os.environ["MFP_PASSWORD"]
    )

    for d in [date.today() - timedelta(days=1), date.today()]:
        day = client.get_date(d.year, d.month, d.day)
        t = day.totals

        row = [
            d.isoformat(),
            t.get("calories"),
            t.get("carbohydrates"),
            t.get("fat"),
            t.get("protein"),
            t.get("sodium"),
            t.get("sugar"),
        ]

        dates = ws.col_values(1)
        if row[0] in dates:
            i = dates.index(row[0]) + 1
            ws.update(f"A{i}:G{i}", [row])
        else:
            ws.append_row(row)

    print("SYNC OK")

if __name__ == "__main__":
    main()

