#!/usr/bin/env python3
"""
YouTube Video Upload

Uploads video to YouTube using Data API v3.
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from auth import get_credentials


def get_youtube_service():
    """Build YouTube API service."""
    from googleapiclient.discovery import build

    creds = get_credentials()
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    privacy: str = "private",
    category: str = "22"
) -> str:
    """
    Upload video to YouTube.

    Args:
        video_path: Path to video file
        title: Video title (max 100 chars)
        description: Video description (max 5000 chars)
        privacy: private/unlisted/public
        category: Category ID (22 = People & Blogs)

    Returns:
        Video ID
    """
    from googleapiclient.http import MediaFileUpload

    youtube = get_youtube_service()

    # Prepare metadata
    body = {
        "snippet": {
            "title": title[:100],  # YouTube limit
            "description": description[:5000],  # YouTube limit
            "categoryId": category,
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    # Prepare upload
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"Uploading: {video_path} ({file_size_mb:.1f}MB)")
    print(f"Title: {title}")
    print(f"Privacy: {privacy}")

    # Use resumable upload for large files
    media = MediaFileUpload(
        video_path,
        chunksize=50 * 1024 * 1024,  # 50MB chunks
        resumable=True
    )

    # Execute upload
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    start_time = time.time()

    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Progress: {progress}%")

    elapsed = time.time() - start_time
    video_id = response["id"]

    print(f"\nUpload complete!")
    print(f"Video ID: {video_id}")
    print(f"URL: https://youtu.be/{video_id}")
    print(f"Duration: {elapsed:.1f}s")

    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Video file path")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--privacy", default="private",
                       choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)

    try:
        video_id = upload_video(
            args.video,
            args.title,
            args.description,
            args.privacy
        )
        print(f"\nvideo_id={video_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
