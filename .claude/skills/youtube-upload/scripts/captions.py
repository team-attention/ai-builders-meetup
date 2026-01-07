#!/usr/bin/env python3
"""
YouTube Caption Upload

Uploads SRT subtitle to YouTube video.
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from auth import get_credentials


def get_youtube_service():
    """Build YouTube API service."""
    from googleapiclient.discovery import build

    creds = get_credentials()
    return build("youtube", "v3", credentials=creds)


def upload_caption(
    video_id: str,
    caption_file: str,
    language: str = "en",
    name: str = "English"
) -> str:
    """
    Upload caption/subtitle to a YouTube video.

    Args:
        video_id: YouTube video ID
        caption_file: Path to SRT file
        language: Language code (en, ko, etc.)
        name: Display name for the caption track

    Returns:
        Caption ID
    """
    from googleapiclient.http import MediaFileUpload

    youtube = get_youtube_service()

    # Prepare caption metadata
    body = {
        "snippet": {
            "videoId": video_id,
            "language": language,
            "name": name,
            "isDraft": False
        }
    }

    # Upload caption file
    media = MediaFileUpload(caption_file, mimetype="application/x-subrip")

    print(f"Uploading caption: {caption_file}")
    print(f"Video ID: {video_id}")
    print(f"Language: {language} ({name})")

    response = youtube.captions().insert(
        part="snippet",
        body=body,
        media_body=media
    ).execute()

    caption_id = response["id"]
    print(f"\nCaption uploaded!")
    print(f"Caption ID: {caption_id}")

    return caption_id


def main():
    parser = argparse.ArgumentParser(description="Upload caption to YouTube video")
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    parser.add_argument("--file", required=True, help="Caption file path (SRT)")
    parser.add_argument("--language", default="en", help="Language code")
    parser.add_argument("--name", default="English", help="Caption track name")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: Caption file not found: {args.file}")
        sys.exit(1)

    try:
        caption_id = upload_caption(
            args.video_id,
            args.file,
            args.language,
            args.name
        )
        print(f"\ncaption_id={caption_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
