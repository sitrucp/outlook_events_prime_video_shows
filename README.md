# Amazon Prime Video Data Outlook Event Creation

This repository contains scripts to process Amazon Prime viewing history data and create Outlook calendar events using the Microsoft Graph API.

## Features
1. **Data Cleaning**: Preprocess Amazon Prime viewing history data.
2. **Event Creation**: Create Outlook calendar events for viewing entries.
3. **Logging**: Maintain logs for processed events and last event creation.

## Workflow Summary
1. Request and download your Amazon Prime viewing history data.
2. Preprocess the data using `process_raw_data.py`.
3. Use `create_events.py` to create Outlook events from the cleaned data.
4. Check logs for details and track processing.

## Prerequisites
- **Microsoft Graph API Credentials**: `client_id`, `tenant_id`, `client_secret`, `user_id`
- **Required Libraries**:  `pandas`, `numpy`, `requests`, `pytz`

## Usage

### Step 1: Obtain Your Amazon Prime Viewing History
1. Go to [Amazon Account Settings](https://www.amazon.ca/gp/css/homepage.html?ref_=nav_AccountFlyout_ya).
2. Scroll down and select the link **"Request your data"**.
3. Choose **Prime Video** and confirm your request.
4. Wait for a confirmation email from Amazon (it may take a few days).
5. Download the data from the provided link.
6. Extract `PrimeVideo.ViewingHistory.csv` from the downloaded zip file in the `PrimeVideo.ViewingHistory` folder.

### Step 2: Clean the Data
Run the `process_raw_data.py` script to clean the downloaded data file `PrimeVideo.ViewingHistory.csv` (extracted from the downloaded zip file). This outputs a new csv file `PrimeVideo.ViewingHistory_clean.csv` (cleaned and preprocessed data).

### Step 3: Create Outlook Calendar Events
Run the `create_events.py` script to create calendar events using the cleaned data `PrimeVideo.ViewingHistory_clean.csv` (generated in Step 2)

## Logs
Two logs are created for tracking progress:
1. **Create Events Log**: Tracks processing details and errors during event creation (`create_events_log.txt`).
2. **Last Event Log**: Tracks the most recent processed event to start from in future runs (`last_event_log.csv`).

## Example Directory Structure
```
repo/
|
├── process_raw_data.py
├── create_events.py
├── PrimeVideo.ViewingHistory.csv
├── PrimeVideo.ViewingHistory_clean.csv
│── create_events_log.txt
│── last_event_log.csv
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

