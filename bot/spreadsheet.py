import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from decimal import Decimal

# Путь к credentials.json
SERVICE_ACCOUNT_FILE = "config/credentials.json"
SPREADSHEET_ID = "1MsCZAkWvn38XQ7trEx2hPl5SsgIcjwGu_Q2da1COOY8"
SHEET_NAME = "Лист1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def save_to_google_sheets(amount: Decimal, category: str, comment: str, username: str) -> None:
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, str(amount), category, comment, username])