import pandas as pd
import numpy as np
from datetime import datetime, timedelta


input_file = "PrimeVideo.ViewingHistory.csv"
output_file = "PrimeVideo.ViewingHistory_clean.csv"

# Load the CSV file
df = pd.read_csv(input_file)

# Remove excessive quotation marks from the 'Title' column
df['Title'] = df['Title'].str.strip('"')

# Remove fractional seconds from the 'Playback Start Datetime (UTC)' column
df['Playback Start Datetime (UTC)'] = df['Playback Start Datetime (UTC)'].str.split('.').str[0]

# Filter out records with Title "Not available"
df = df[df['Title'] != "Not available"]

# Convert 'Seconds Viewed' to minutes and round up
df['Duration Minutes'] = np.ceil(df['Seconds Viewed'] / 60).astype(int)

# Calculate 'Playback End Datetime (UTC)' using 'Playback Start Datetime (UTC)' and 'Duration Minutes'
def calculate_end_time(row):
    # Parse the start time without fractional seconds
    start_time = datetime.strptime(row['Playback Start Datetime (UTC)'], '%Y-%m-%d %H:%M:%S')
    # Calculate duration in minutes
    duration = timedelta(minutes=row['Duration Minutes'])
    # Calculate the end time
    end_time = start_time + duration
    # Format the end time without fractional seconds
    return end_time.strftime('%Y-%m-%d %H:%M:%S')

# Apply the function to calculate the end time
df['Playback End Datetime (UTC)'] = df.apply(calculate_end_time, axis=1)

# Drop the original 'Seconds Viewed' column
df = df.drop(columns=['Seconds Viewed'])

# Group by 'Title' and aggregate
agg_df = df.groupby('Title').agg({
    'Playback Start Datetime (UTC)': 'min',
    'Playback End Datetime (UTC)': 'max',
    'Duration Minutes': 'max'
}).reset_index()

# Convert 'Playback Start Datetime (UTC)' to datetime type without fractional seconds
agg_df['Playback Start Datetime (UTC)'] = pd.to_datetime(
    agg_df['Playback Start Datetime (UTC)'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

# Format datetime columns to remove any fractional seconds
agg_df['Playback Start Datetime (UTC)'] = agg_df['Playback Start Datetime (UTC)'].dt.strftime('%Y-%m-%d %H:%M:%S')
agg_df['Playback End Datetime (UTC)'] = pd.to_datetime(
    agg_df['Playback End Datetime (UTC)']).dt.strftime('%Y-%m-%d %H:%M:%S')

# Sort the DataFrame by 'Playback Start Datetime (UTC)'
agg_df = agg_df.sort_values('Playback Start Datetime (UTC)', ascending=False)

# Reorder the columns as specified
column_order = ['Playback Start Datetime (UTC)', 'Playback End Datetime (UTC)', 'Title', 'Duration Minutes']
agg_df = agg_df[column_order]

# Save the aggregated DataFrame to a new CSV file
agg_df.to_csv(output_file, index=False)

print("data saved to:", output_file)