#!/usr/bin/env python3
"""
YouTube OAuth Authentication

Handles OAuth 2.0 flow for YouTube Data API v3.
"""

import sys
import argparse
from pathlib import Path

# OAuth scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"  # For captions
]

# Token/secrets paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"
TOKEN_FILE = PROJECT_ROOT / ".youtube_token.json"


def check_auth() -> tuple[bool, str]:
    """Check if valid authentication exists."""
    if not TOKEN_FILE.exists():
        return False, "Token file not found"

    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            return True, "Token expired but refreshable"
        return creds.valid, "Token valid" if creds.valid else "Token invalid"
    except Exception as e:
        return False, str(e)


def get_credentials():
    """Get or refresh OAuth credentials."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                print(f"Error: {CLIENT_SECRETS_FILE} not found")
                print("\n1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download JSON and save as 'client_secrets.json'")
                sys.exit(1)

            print("Starting OAuth flow...")
            print("A browser window will open for authentication.")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    return creds


def main():
    parser = argparse.ArgumentParser(description="YouTube OAuth Authentication")
    parser.add_argument("--check", action="store_true", help="Check auth status")
    args = parser.parse_args()

    if args.check:
        valid, message = check_auth()
        print(f"Auth status: {'OK' if valid else 'FAILED'} - {message}")
        sys.exit(0 if valid else 1)

    # Run auth flow
    try:
        from google.oauth2.credentials import Credentials  # noqa: F401
        from google.auth.transport.requests import Request  # noqa: F401
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
    except ImportError:
        print("Error: Required packages not installed")
        print("Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)

    get_credentials()
    print("Authentication successful!")


if __name__ == "__main__":
    main()
