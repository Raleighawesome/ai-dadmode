#!/usr/bin/env python3
"""
fetch_today_events.py

Simplified calendar script for automated workflows.
Fetches today's calendar events and outputs JSON to stdout.
Designed for n8n SSH execute node integration.

Usage:
  ./fetch_today_events.py [--date YYYY-MM-DD] [--start <ISO|YYYY-MM-DD>] [--end <ISO|YYYY-MM-DD>] [--calendar-id ID] [--debug]

Output: JSON array of today's events with attendees
"""

import json
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_PATH = Path.home() / '.google' / 'token.json'
CREDENTIALS_PATH = Path.home() / '.google' / 'credentials.json'

def get_credentials() -> Credentials:
    """Get Google Calendar API credentials using OAuth2."""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(json.dumps({"error": f"Credentials file not found at {CREDENTIALS_PATH}"}), file=sys.stderr)
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials
        TOKEN_PATH.parent.mkdir(exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds

def get_user_email(service) -> str:
    """Extract user email from the authenticated service."""
    try:
        calendar = service.calendars().get(calendarId='primary').execute()
        return calendar.get('id', '')
    except HttpError:
        return "user@example.com"  # Fallback

def is_user_invited(event: Dict[str, Any], user_email: str) -> bool:
    """Check if the user is invited to the event."""
    attendees = event.get('attendees', [])
    if not attendees:
        return True  # No attendees list means include the event

    for attendee in attendees:
        if attendee.get('email', '').lower() == user_email.lower():
            return True
    return False

def has_user_declined(event: Dict[str, Any], user_email: str) -> bool:
    """Check if the user has declined the event."""
    attendees = event.get('attendees', [])
    for attendee in attendees:
        if attendee.get('email', '').lower() == user_email.lower():
            return attendee.get('responseStatus') == 'declined'
    return False

def format_datetime(dt_str: str) -> tuple[str, str]:
    """Format datetime string to date and time components."""
    if not dt_str:
        return '', ''

    try:
        if 'T' in dt_str:
            # Parse full datetime
            if dt_str.endswith('Z'):
                dt = datetime.fromisoformat(dt_str[:-1] + '+00:00')
            else:
                dt = datetime.fromisoformat(dt_str)

            # Convert to local timezone
            if dt.tzinfo is not None:
                dt = dt.astimezone()

            return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')
        else:
            # Date-only (all-day event)
            return dt_str, '00:00:00'
    except ValueError:
        return '', ''

def parse_datetime_param(value: str, is_start: bool) -> datetime:
    """Parse a date/datetime string and return timezone-aware UTC datetime.

    Supports:
    - YYYY-MM-DD (date-only)
    - ISO-8601 (e.g., 2025-11-06T09:00:00-05:00 or with 'Z')
    If no timezone is provided, assume local timezone, then convert to UTC.
    For date-only: start → 00:00:00, end → 23:59:59.999999 local, then convert to UTC.
    """
    local_tz = datetime.now().astimezone().tzinfo
    v = value.strip()
    # Date-only
    if 'T' not in v:
        try:
            d = datetime.strptime(v, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(f"Invalid date format for '{value}'. Use YYYY-MM-DD or ISO-8601.") from e
        if is_start:
            dt_local = d.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
        else:
            dt_local = d.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=local_tz)
        return dt_local.astimezone(timezone.utc)
    # Datetime
    iso = v.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format for '{value}'. Use ISO-8601.") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz)
    return dt.astimezone(timezone.utc)

def get_accepted_attendees(event: Dict[str, Any]) -> List[str]:
    """Get list of attendees who have accepted the event."""
    attendees = event.get('attendees', [])
    if not attendees:
        return []

    accepted = []
    for attendee in attendees:
        response_status = attendee.get('responseStatus', 'needsAction')
        if response_status in ['accepted', 'tentative']:
            email = attendee.get('email')
            if email:
                accepted.append(email)

    return accepted

def fetch_today_events(
    date_str: str | None = None,
    start_param: str | None = None,
    end_param: str | None = None,
    calendar_id: str = 'primary',
    debug: bool = False,
) -> List[Dict[str, Any]]:
    """Fetch calendar events for a specified window (defaults to today).

    - date_str: fetch the entire day (local) for YYYY-MM-DD
    - start_param/end_param: explicit window; ISO-8601 or YYYY-MM-DD
    - calendar_id: calendar to query (default 'primary')
    """
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        user_email = get_user_email(service)

        # Determine time window (UTC RFC3339)
        if date_str and (start_param or end_param):
            raise ValueError("Use either --date or --start/--end, not both.")

        if start_param or end_param:
            if not start_param or not end_param:
                raise ValueError("Provide both --start and --end when specifying a custom window.")
            start_dt_utc = parse_datetime_param(start_param, is_start=True)
            end_dt_utc = parse_datetime_param(end_param, is_start=False)
        else:
            # Default to today (or specific --date day) in local time, converted to UTC
            if date_str:
                base_date = date_str
            else:
                base_date = datetime.now().strftime('%Y-%m-%d')
            start_dt_utc = parse_datetime_param(base_date, is_start=True)
            end_dt_utc = parse_datetime_param(base_date, is_start=False)

        time_min = start_dt_utc.isoformat().replace('+00:00', 'Z')
        time_max = end_dt_utc.isoformat().replace('+00:00', 'Z')

        if debug:
            print(f"[debug] user={user_email} calendar={calendar_id}", file=sys.stderr)
            print(f"[debug] timeMin={time_min} timeMax={time_max}", file=sys.stderr)

        # Fetch events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        filtered_events = []
        now = datetime.now().astimezone()

        for event in events:
            # Skip workingLocation events
            if event.get('eventType') == 'workingLocation':
                continue

            # Check if user is invited
            if not is_user_invited(event, user_email):
                continue

            # Check if user declined (for future events)
            event_start = event.get('start', {})
            start_time_str = event_start.get('dateTime') or event_start.get('date')

            if start_time_str:
                try:
                    if 'T' in start_time_str:
                        if start_time_str.endswith('Z'):
                            event_dt = datetime.fromisoformat(start_time_str[:-1] + '+00:00')
                        else:
                            event_dt = datetime.fromisoformat(start_time_str)
                        if event_dt.tzinfo is not None:
                            event_dt = event_dt.astimezone()
                        else:
                            event_dt = event_dt.replace(tzinfo=timezone.utc).astimezone()
                    else:
                        event_dt = datetime.strptime(start_time_str, '%Y-%m-%d')
                        event_dt = event_dt.replace(tzinfo=timezone.utc).astimezone()

                    # Skip if declined and in future
                    if event_dt > now and has_user_declined(event, user_email):
                        continue
                except ValueError:
                    pass

            # Format event
            start = event.get('start', {})
            end = event.get('end', {})

            start_date, start_time = format_datetime(start.get('dateTime') or start.get('date'))
            end_date, end_time = format_datetime(end.get('dateTime') or end.get('date'))

            # Handle all-day events
            if not start_time or start_time == '00:00:00':
                if start.get('date'):
                    start_time = '00:00:00'
                    end_time = '23:59:59'

            formatted_event = {
                'date': start_date,
                'start_time': start_time,
                'end_time': end_time,
                'title': event.get('summary', 'No Title'),
                'accepted_attendees': get_accepted_attendees(event),
                'event_id': event.get('id', ''),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'organizer': event.get('organizer', {}).get('email', ''),
                'status': event.get('status', ''),
                'html_link': event.get('htmlLink', '')
            }

            filtered_events.append(formatted_event)

        return filtered_events

    except Exception as e:
        return [{"error": f"Failed to fetch calendar events: {str(e)}"}]

def main():
    """Main entry point - output JSON to stdout."""
    parser = argparse.ArgumentParser(description="Fetch Google Calendar events (JSON output)")
    parser.add_argument('--date', help='Fetch events for this date (YYYY-MM-DD)')
    parser.add_argument('--start', dest='start_param', help='Start datetime (ISO-8601 or YYYY-MM-DD)')
    parser.add_argument('--end', dest='end_param', help='End datetime (ISO-8601 or YYYY-MM-DD)')
    parser.add_argument('--calendar-id', default='primary', help='Calendar ID (default: primary)')
    parser.add_argument('--debug', action='store_true', help='Print debug info to stderr')
    args = parser.parse_args()

    events = fetch_today_events(
        date_str=args.date,
        start_param=args.start_param,
        end_param=args.end_param,
        calendar_id=args.calendar_id,
        debug=args.debug,
    )
    output = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_events': len(events),
        'events': events
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
