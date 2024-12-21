import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import sys
import os
import csv
import logging


#--- Get msgraph config variables ---#
config_msgraph_path = os.getenv("ENV_VARS_PATH")  # Get path to directory contaiining config_msgraph.py
if not config_msgraph_path:
    raise ValueError("ENV_VARS_PATH environment variable not set")
sys.path.insert(0, config_msgraph_path)

from config_msgraph import config_msgraph

client_id=config_msgraph["client_id"]
tenant_id=config_msgraph["tenant_id"]
client_secret=config_msgraph["client_secret"]
user_id=config_msgraph["user_id"]

#--- Define files ---#
input_file = "PrimeVideo.ViewingHistory_clean.csv"
last_event_log_file = "last_event_log.csv"
create_event_log = "create_events_log.txt"

#--- Setup logging ---#
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(create_event_log),
        logging.StreamHandler(sys.stdout)
    ]
)

#--- Function to obtain an access token ---#
def get_access_token(client_id, tenant_id, client_secret):
    logging.info("Obtaining access token from Microsoft Graph API")
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises an exception for HTTP error codes
    logging.info("Access token obtained successfully")
    return response.json().get('access_token')

#--- Function to convert timezone and calculate end time  ---#

def adjust_times(df):
    logging.info("Adjusting timezones for the records")
    utc_zone = pytz.utc
    est_zone = pytz.timezone('America/New_York')
    for index, row in df.iterrows():
        try:
            # Directly use the Timestamp object
            start_time_utc = row['Playback Start Datetime (UTC)'].replace(tzinfo=utc_zone)
            # Calculate end time in UTC
            duration = timedelta(minutes=row['Duration Minutes'])
            end_time_utc = start_time_utc + duration
            # Convert both times to EST
            start_time_est = start_time_utc.astimezone(est_zone).strftime('%Y-%m-%d %H:%M:%S')
            end_time_est = end_time_utc.astimezone(est_zone).strftime('%Y-%m-%d %H:%M:%S')
            # Update DataFrame
            df.at[index, 'Playback Start Datetime (EST)'] = start_time_est
            df.at[index, 'Playback End Datetime (EST)'] = end_time_est
        except Exception as e:
            logging.error(f"Error adjusting times for row {index}: {e}")

#--- Function to read the last event date from retrieve_log.csv ---#

def get_last_event_date():
    try:
        with open(last_event_log_file, 'r') as f:
            reader = csv.DictReader(f)
            last_event = next(reader)
            logging.info(f"Last event date retrieved: {last_event['last_event_date']}")
            return datetime.strptime(last_event['last_event_date'], '%Y-%m-%d').date()
    except (FileNotFoundError, StopIteration):
        logging.warning("Log file not found or is empty, using default date")
        return datetime.min.date()

#--- Function to update the retrieve_log.csv with the latest event date ---#

def update_last_event_date(latest_date, latest_title):
    with open(last_event_log_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['last_event_date', 'last_event_title'])
        writer.writeheader()
        writer.writerow({
            'last_event_date': latest_date.strftime('%Y-%m-%d'),
            'last_event_title': latest_title
        })
    logging.info(f"Updated last event log: {latest_date} - {latest_title}")

#--- Function to create a calendar event using Microsoft Graph API ---#

def create_calendar_event(access_token, row):
    # Create the event description, incorporating the duration
    description_html = (
        f"Title: {row['Title']}<br>"
        f"Start: {row['Playback Start Datetime (EST)']}<br>"
        f"End: {row['Playback End Datetime (EST)']}<br>"
        f"Duration: {row['Duration Minutes']} minutes"
    )

    # Adjusted event payload to use the pre-calculated times and duration
    event_payload = {
        "subject": f"Prime TV: {row['Title']}",
        "start": {"dateTime": row['Playback Start Datetime (EST)'], "timeZone": "America/Toronto"},
        "end": {"dateTime": row['Playback End Datetime (EST)'], "timeZone": "America/Toronto"},
        "body": {"contentType": "HTML", "content": description_html},
        "categories": ["Prime TV"]
    }

    # Send the request to create the event
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    try:
        response = requests.post(f"https://graph.microsoft.com/v1.0/users/{user_id}/events", headers=headers, json=event_payload)
        response.raise_for_status()  # Ensure successful request
        logging.info(f"Event created successfully for {row['Title']}")
    except Exception as e:
        logging.error(f"Failed to create event for {row['Title']}: {e}")

#--- Main script to process the CSV data and create events ---#

def main():
    logging.info("Starting the process of reading CSV data and creating events")

    access_token = get_access_token(client_id, tenant_id, client_secret)
    
    # Load the CSV file
    df = pd.read_csv(input_file)
    logging.info(f"CSV data loaded successfully with {len(df)} records")

    # Filter out blank rows
    df = df.dropna(how='all')
    logging.info(f"Data after removing blank rows: {len(df)} records")

    # Remove rows with invalid or missing datetime
    df = df.dropna(subset=['Playback Start Datetime (UTC)'])
    logging.info(f"Data after removing rows with missing datetimes: {len(df)} records")

    # Convert 'Playback Start Datetime (UTC)' to datetime
    df['Playback Start Datetime (UTC)'] = pd.to_datetime(df['Playback Start Datetime (UTC)'], errors='coerce')
    
    # Filter out rows where datetime conversion failed
    df = df.dropna(subset=['Playback Start Datetime (UTC)'])
    logging.info(f"Data after ensuring valid datetimes: {len(df)} records")

    # Filter out rows with Duration less than 10 minutes
    df = df[df['Duration Minutes'] >= 10]
    logging.info(f"Data after filtering short durations: {len(df)} records")

    # Adjust times
    adjust_times(df)

    # Get the last event date
    last_event_date = get_last_event_date()

    # Filter records newer than last_event_date
    df = df[df['Playback Start Datetime (UTC)'].dt.date > last_event_date]
    logging.info(f"Data after filtering older events: {len(df)} records")

    # Ensure the DataFrame is not empty after filtering
    if df.empty:
        logging.info("No new events to create.")
        return

    # Iterate with the updated DataFrame including duration
    for index, row in df.iterrows():
        try:
            create_calendar_event(access_token, row)
            break
        except Exception as e:
            logging.error(f"Failed to create event for {row['Playback Start Datetime (EST)']} {row['Title']} Error: {e}")

    # Update the retrieve_log.csv with the latest event date
    latest_event_date = df['Playback Start Datetime (UTC)'].max().date()
    latest_event_title = df.loc[df['Playback Start Datetime (UTC)'].idxmax(), 'Title']
    update_last_event_date(latest_event_date, latest_event_title)

    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()
