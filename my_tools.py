import os
# Setting up google api
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# from crewai_tools import tool
from langchain.tools import tool

# Setting up calendar
from datetime import datetime
import pytz

# Mail format handlings
import base64
import json
# Setttig up the gmail api


def setup_gmail():
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    # Check if token file exists and load credentials
    if os.path.exists("gmail_token.json"):
        try:
            creds = Credentials.from_authorized_user_file(
                "gmail_token.json", SCOPES)
        except (ValueError, json.decoder.JSONDecodeError):
            print("Invalid token file. Requiring reauthorization.")
            os.remove("gmail_token.json")
            creds = None
    # If credentials are not valid, start authorization flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "gmail_credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open("gmail_token.json", "w") as token:
            token.write(creds.to_json())
    # Build the Gmail API service
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# # Tools


@tool("get gmail")
def getGmail(email_number: int) -> str:
    """
    Tool name: getGmail
    Description: Fetch the specified Gmail using the Gmail API.
    Arguments:
    - email_number: An integer representing which email to fetch. 1 for latest, 2 for second latest, etc.

    Returns:
    - A string containing the email's subject, sender, date, and full body.
    """
    service = setup_gmail()
    if not service:
        return "Failed to connect to Gmail service."

    try:
        # Fetch messages
        results = service.users().messages().list(
            userId="me", maxResults=email_number).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No messages found."

        # Fetch specific email by index
        message = messages[email_number-1]
        msg = service.users().messages().get(
            userId="me", id=message["id"], format="full").execute()

        # Extract relevant email data
        email_details = ""
        headers = msg.get("payload", {}).get("headers", [])
        for header in headers:
            if header["name"] == "Subject":
                email_details += f"Subject: {header['value']}\n"
            if header["name"] == "From":
                email_details += f"From: {header['value']}\n"
            if header["name"] == "Date":
                email_details += f"Date: {header['value']}\n"

        # Extract the email body
        body = extract_email_body(msg.get("payload", {}))
        email_details += f"Body:\n{body}\n"

        return email_details

    except HttpError as error:
        return f"An error occurred: {error}"


def extract_email_body(payload):
    """
    Extracts the email body from the payload.
    Prioritizes text/plain over text/html if both are available.
    """
    body = ""

    # If the email is multipart, loop through each part
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body = base64.urlsafe_b64decode(
                    part["body"]["data"]).decode("utf-8")
                break  # Prioritize plain text, so we can break the loop
            elif part["mimeType"] == "text/html":
                body = base64.urlsafe_b64decode(
                    part["body"]["data"]).decode("utf-8")
                # Keep checking for text/plain, but use HTML if no plain text is found
    else:
        # If the email isn't multipart, decode the single part
        body += base64.urlsafe_b64decode(payload["body"]
                                         ["data"]).decode("utf-8")
    return body


# Example usage
email_input = {"email_number": 1}
email = getGmail.invoke(email_input)
print(email)

# Setting up Google Calendar


def setup_google_calenar():
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None

    if os.path.exists("google_calendar_token.json"):
        creds = Credentials.from_authorized_user_file(
            "google_calendar_token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "google_calendar_credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("google_calendar_token.json", "w") as token:
            token.write(creds.to_json())
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")


@tool("get upcoming events")
def get_upcoming_events(n: int = 1) -> str:
    """
    Tool Name: get_upcoming_events
    Description: Useful for some upcoming events from google calendar

    Arguments:
    n: number of upcoming events.

    returns:
    A json containing information about upcoming events oin google calendar
    """
    service = setup_google_calenar()
    try:
        now = dt.datetime.utcnow().isoformat() + "Z"
        event_result = service.events().list(calendarId="primary", timeMin=now,
                                             maxResults=n, singleEvents=True, orderBy="startTime").execute()
    except HttpError as error:
        return f"Error occured: {error}"

    events = event_result.get("items", [])
    if not events:
        return json.dumps({"message": "No upcoming events found."})

    events_data = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        event_data = {
            "start": start,
            "summary": event.get("summary", "No Summary")
        }
        events_data.append(event_data)

    events_json = json.dumps(events_data, indent=4)
    return events_json


@tool("create google calendar event")
def create_event(start_time: str, end_time: str, description: str):
    """
    Tool name: create_event

    Description: It creates a google calendar event.

    Arguments:
    start_time: a string containing start time of the event in ISO 8601 format. ISO 8601 formate is YYYY-MM-DDThh:mm:ss
    end_timee: a string containing end time of the event in ISO 8601 format. ISO 8601 formate is YYYY-MM-DDThh:mm:ss
    description:

    Returns:
    string containig event link
    """
    service = setup_google_calenar()
    # Configure time
    timeZone = "Asia/Kolkata"
    # Start time
    dt = datetime.fromisoformat(start_time)
    tz = pytz.timezone(timeZone)
    localized_dt = tz.localize(dt)
    start = localized_dt.isoformat()
    # End time
    dt = datetime.fromisoformat(end_time)
    tz = pytz.timezone(timeZone)
    localized_dt = tz.localize(dt)
    end = localized_dt.isoformat()

    event = {
        'summary': description,
        'start': {
            'dateTime': start_time,
            'timeZone': timeZone,
        },
        'end': {
            'dateTime': end_time,
            'timeZone': timeZone,
        },
    }

    try:
        event_result = service.events().insert(
            calendarId='primary', body=event).execute()
        return f'Event created: {event_result.get("htmlLink")}'
    except HttpError as error:
        return f'An error occurred: {error}'


# # Test create_event tool
# start_time = "2024-09-04T17:00:00"
# end_time = "2024-09-04T18:00:00"
# description = "Electroceramics quiz next Monday. Syllabus from start to lecture 9. No plagiarism allowed. Bring calculator."
# result = create_event(start_time, end_time, description)
# print(result)
