# ============================================================
#           WebEarl Technologies — Google Authentication
# ============================================================

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import ALL_SCOPES

# --- File Paths ---
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_credentials():
    """
    Handles Google OAuth2 authentication.
    - First run: Opens browser for login and saves token.json
    - Later runs: Uses saved token.json directly (no browser)
    """
    creds = None

    # Check if token.json already exists (means already logged in before)
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, ALL_SCOPES)
            print("✅ Loaded existing Google credentials from token.json")
        except Exception as e:
            print(f"⚠️  Could not load token.json: {e}")
            creds = None

    # If no valid credentials, ask user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")
            except Exception as e:
                print(f"⚠️  Could not refresh credentials: {e}")
                creds = None

        if not creds:
            # Check if credentials.json exists
            if not os.path.exists(CREDENTIALS_FILE):
                print("\n❌ ERROR: credentials.json not found!")
                print("👉 Please download it from Google Cloud Console")
                print("   and place it in the HR-Automation folder.")
                return None, None, None

            print("\n🌐 Opening browser for Google login...")
            print("   Please log in and click Allow in the browser window.")
            print("   (This will only happen once)\n")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, ALL_SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("✅ Login successful!")
            except Exception as e:
                print(f"❌ Login failed: {e}")
                return None, None, None

        # Save token.json for future runs
        try:
            with open(TOKEN_FILE, "w") as token_file:
                token_file.write(creds.to_json())
            print("💾 Credentials saved to token.json (no login needed next time)")
        except Exception as e:
            print(f"⚠️  Could not save token.json: {e}")

    # Build Gmail and Calendar service objects
    try:
        gmail_service = build("gmail", "v1", credentials=creds)
        calendar_service = build("calendar", "v3", credentials=creds)
        print("✅ Gmail API connected successfully!")
        print("✅ Google Calendar API connected successfully!")
        return creds, gmail_service, calendar_service

    except Exception as e:
        print(f"❌ Could not connect to Google APIs: {e}")
        return None, None, None


def test_connection():
    """
    Test if Gmail and Calendar connections are working properly.
    Run this file directly to test: python auth.py
    """
    print("\n" + "="*50)
    print("  WebEarl HR Automation — Connection Test")
    print("="*50 + "\n")

    creds, gmail_service, calendar_service = get_credentials()

    if not gmail_service or not calendar_service:
        print("\n❌ Connection failed. Please check your credentials.json file.")
        return

    # Test Gmail
    try:
        profile = gmail_service.users().getProfile(userId="me").execute()
        print(f"\n📧 Gmail connected as: {profile['emailAddress']}")
    except Exception as e:
        print(f"❌ Gmail test failed: {e}")

    # Test Calendar
    try:
        calendar_list = calendar_service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        print(f"📅 Google Calendar connected!")
        print(f"   Found {len(calendars)} calendar(s) in your account:")
        for cal in calendars[:3]:  # Show first 3 calendars only
            print(f"   → {cal['summary']}")
    except Exception as e:
        print(f"❌ Calendar test failed: {e}")

    print("\n✅ All connections working! You are ready to run the pipeline.")
    print("="*50 + "\n")


# Run this file directly to test connection
if __name__ == "__main__":
    test_connection()