"""Google Sheets input reader."""

from typing import Iterator

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    gspread = None
    Credentials = None


def read_google_sheet(sheet_url_or_id: str, credentials_file: str | None = None) -> Iterator[dict[str, str]]:
    """Read SMS data from Google Sheets.

    Args:
        sheet_url_or_id: Google Sheet URL or ID
        credentials_file: Path to service account credentials JSON file

    Yields:
        Dictionary records from Google Sheet

    Raises:
        ImportError: If Google Sheets libraries are not installed
        RuntimeError: If authentication fails or sheet cannot be read
    """
    if gspread is None:
        raise ImportError(
            "Google Sheets support requires gspread and google-auth libraries. "
            "Install with: pip install gspread google-auth google-auth-oauthlib"
        )

    try:
        if credentials_file:
            creds = Credentials.from_service_account_file(credentials_file,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                       "https://www.googleapis.com/auth/drive"])
        else:
            creds = Credentials.from_service_account_info({})

        client = gspread.authorize(creds)

        # Extract sheet ID from URL if needed
        sheet_id = sheet_url_or_id
        if "/spreadsheets/d/" in sheet_url_or_id:
            sheet_id = sheet_url_or_id.split("/spreadsheets/d/")[1].split("/")[0].split("?")[0].strip()

        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1  # Use the first worksheet

        # Get all records
        records = worksheet.get_all_records()

        if not records:
            raise ValueError("No data found in the Google Sheet")

        yield from records

    except DefaultCredentialsError as e:
        raise RuntimeError(
            "Google Sheets authentication failed. Please provide valid credentials. "
            "You can create a service account at: https://console.cloud.google.com/apis/credentials"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to read Google Sheet: {str(e)}") from e
