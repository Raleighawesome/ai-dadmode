#!/usr/bin/env python3
"""
YouTube Transcript Extractor
Extracts transcripts from YouTube videos and returns structured data.

Usage:
    python youtube_transcript_extractor.py <youtube_url>

Output:
    JSON with video metadata and transcript
"""

import sys
import json
import re
from urllib.parse import urlparse, parse_qs

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    print(json.dumps({
        "error": "youtube-transcript-api not installed",
        "message": "Install with: pip install youtube-transcript-api"
    }), file=sys.stderr)
    sys.exit(1)


def extract_video_id(url):
    """
    Extract video ID from various YouTube URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    parsed = urlparse(url)

    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
    elif parsed.hostname == 'youtu.be':
        return parsed.path[1:]

    return None


def get_video_metadata(video_id):
    """
    Attempt to get basic video metadata.
    Note: This is limited without YouTube API key.
    """
    # Without API key, we can only return video ID and construct URL
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}"
    }


def get_transcript(video_id):
    """
    Fetch transcript for the given video ID.
    Returns transcript text and language.
    """
    try:
        # Create API instance
        api = YouTubeTranscriptApi()

        # Try to get English transcript first
        languages = ['en', 'en-US', 'en-GB']
        fetched = None

        for lang in languages:
            try:
                fetched = api.fetch(video_id, languages=[lang])
                break
            except:
                continue

        # If no English transcript, try any available language
        if not fetched:
            try:
                fetched = api.fetch(video_id)
            except Exception as e:
                raise Exception(f"No transcript available for video: {video_id}")

        # Combine all text segments
        full_text = ' '.join([snippet.text for snippet in fetched.snippets])

        # Get timestamped segments for reference
        segments = [{
            'start': snippet.start,
            'duration': snippet.duration,
            'text': snippet.text
        } for snippet in fetched.snippets]

        return {
            'language': fetched.language_code,
            'is_generated': fetched.is_generated,
            'full_text': full_text,
            'segments': segments,
            'segment_count': len(segments)
        }

    except TranscriptsDisabled:
        raise Exception(f"Transcripts are disabled for video: {video_id}")
    except NoTranscriptFound:
        raise Exception(f"No transcript found for video: {video_id}")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing argument",
            "message": "Usage: python youtube_transcript_extractor.py <youtube_url>"
        }), file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        print(json.dumps({
            "error": "Invalid URL",
            "message": f"Could not extract video ID from URL: {url}"
        }), file=sys.stderr)
        sys.exit(1)

    try:
        # Get metadata
        metadata = get_video_metadata(video_id)

        # Get transcript
        transcript_data = get_transcript(video_id)

        # Combine results
        result = {
            **metadata,
            **transcript_data,
            "success": True
        }

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({
            "error": "Extraction failed",
            "message": str(e),
            "video_id": video_id,
            "success": False
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
