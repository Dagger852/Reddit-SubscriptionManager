import praw
import pandas as pd
import sqlite3
from flask import Flask, jsonify
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
from dotenv import load_dotenv
from prawcore import RequestException, TooManyRequests

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variables to track API usage
api_requests = []
throttle_interval = 60  # Initial throttle interval in seconds
throttle_limit = 55  # API request limit per minute
retry_delay = 60  # Delay in seconds before retrying a failed request

# Authenticate with PRAW using environment variables
reddit = praw.Reddit(client_id=os.getenv('CLIENT_ID'),
                     client_secret=os.getenv('CLIENT_SECRET'),
                     user_agent=os.getenv('USER_AGENT'))

# Function to make an API request
def make_api_request():
    try:
        # Get your subscribed subreddits and users
        me = reddit.redditor(os.getenv('REDDIT_USERNAME'))
        subreddits = [s for s in me.subreddits(limit=None)]
        #users = [u for u in me.friends(limit=None)]

        # Create a list of dictionaries containing subreddit and user information
        data = []
        for sub in subreddits:
            data.append({
                'name': sub.display_name,
                'type': 'Subreddit',
                'rank': sub.subscribers if hasattr(sub, 'subscribers') else '',
                'vip': '',
                'free': '',
                'rr': '',
                'pp': '',
                'altAcct1': '',
                'altAcct2': '',
                'deleted': '',
                'tags': '',
                'other': ''
            })

        
        # Create a dataframe
        df = pd.DataFrame(data, columns=['Subscription'])
        df['Type'] = df['Subscription'].apply(lambda x: 'User' if x.startswith('u_') else 'Subreddit')
        df['Rank'] = None  # Placeholder for Rank column
        df['Deleted'] = 'No'  # Default value for Deleted column

        return data
    except Exception as e:
        logger.exception(f"Error occurred while making API request: {str(e)}")
        raise

# Function to check API usage and throttle if necessary
def check_api_usage():
    global throttle_interval

    try:
        # Get the current timestamp
        current_time = datetime.now()

        # Remove API requests older than 1 minute from the list
        while api_requests and api_requests[0] < current_time - timedelta(minutes=1):
            api_requests.pop(0)

        # Check if the number of API requests exceeds the limit
        if len(api_requests) > throttle_limit:
            logger.warning(f'API request limit exceeded. Throttling API polling to every {throttle_interval} seconds.')
            throttle_interval = 90  # Increase the throttle interval to 90 seconds
        else:
            throttle_interval = 60  # Reset the throttle interval to 60 seconds

        # Add the current timestamp to the list of API requests
        api_requests.append(current_time)
    except Exception as e:
        logger.exception(f"Error occurred while checking API usage: {str(e)}")
        raise

# Function to update the database
def update_database():
    logger.info('Updating the database...')

    try:
        # Make an API request
        data = make_api_request()

        # Create a dataframe from the list of dictionaries
        new_df = pd.DataFrame(data)
        new_df['last_updated'] = datetime.now()  # Add a 'last_updated' column with the current datetime

        # Save the dataframe to a SQLite database
        conn = sqlite3.connect('my_database.db')

        # Load the existing data
        existing_df = pd.read_sql_query('SELECT * FROM my_table', conn)

        # Merge the new and existing data, keeping only the new records
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['name', 'type'], keep='last')

        # Get the new entries since the last run
        last_run = existing_df['last_updated'].max() if not existing_df.empty else None
        new_entries = updated_df[updated_df['last_updated'] > last_run] if last_run else updated_df

        # Log the changes
        log_changes(existing_df, updated_df)

        # Save the updated data to the database
        updated_df.to_sql('my_table', conn, if_exists='replace', index=False)

        conn.close()
        logger.info('Database update completed.')
    except TooManyRequests as e:
        # Handle rate limiting error
        logger.error(f'Rate limit exceeded. Retrying in {retry_delay} seconds.')
        time.sleep(retry_delay)
    except RequestException as e:
        # Handle other API request errors
        logger.error(f'API request failed: {str(e)}. Retrying in {retry_delay} seconds.')
        time.sleep(retry_delay)
    except Exception as e:
        logger.exception(f"Error occurred while updating the database: {str(e)}")
        raise
    else:
        # API request successful, wait for the throttle interval before making the next request
        time.sleep(throttle_interval)

# Function to add test data to the database
def add_test_data():
    logger.info('Adding test data to the database...')

    try:
        # Create a list of dictionaries with test data
        test_data = [
            {'name': 'TestSubreddit1', 'type': 'Subreddit', 'rank': 100, 'vip': 'Yes', 'free': 'No', 'rr': 'Yes', 'pp': 'No', 'altAcct1': 'Alt1', 'altAcct2': 'Alt2', 'deleted': 'No', 'tags': 'Tag1, Tag2', 'other': 'Other info'},
            {'name': 'TestSubreddit2', 'type': 'Subreddit', 'rank': 200, 'vip': 'No', 'free': 'Yes', 'rr': 'No', 'pp': 'Yes', 'altAcct1': '', 'altAcct2': '', 'deleted': 'No', 'tags': 'Tag3', 'other': ''},
            {'name': 'TestUser1', 'type': 'User', 'rank': 'last', 'vip': 'No', 'free': 'Yes', 'rr': 'No', 'pp': 'No', 'altAcct1': 'Alt3', 'altAcct2': '', 'deleted': 'No', 'tags': '', 'other': 'Other info'},
            {'name': 'TestUser2', 'type': 'User', 'rank': 'last', 'vip': 'Yes', 'free': 'No', 'rr': 'Yes', 'pp': 'Yes', 'altAcct1': '', 'altAcct2': 'Alt4', 'deleted': 'Yes', 'tags': 'Tag4', 'other': ''}
        ]

        # Create a dataframe from the test data
        test_df = pd.DataFrame(test_data)
        test_df['last_updated'] = datetime.now()  # Add a 'last_updated' column with the current datetime

        # Save the test data to the database
        conn = sqlite3.connect('my_database.db')
        test_df.to_sql('my_table', conn, if_exists='append', index=False)
        conn.close()

        logger.info('Test data added successfully.')
    except Exception as e:
        logger.exception(f"Error occurred while adding test data: {str(e)}")
        raise
    
# Function to log the changes
def log_changes(existing_df, updated_df):
    try:
        # Get the new subscriptions added
        new_subs = set(updated_df['name']) - set(existing_df['name'])
        if new_subs:
            logger.info(f"New subscriptions added: {', '.join(new_subs)}")

        # Get the subscriptions removed
        removed_subs = set(existing_df['name']) - set(updated_df['name'])
        if removed_subs:
            logger.info(f"Subscriptions removed: {', '.join(removed_subs)}")

        # Get the changes to the "Deleted" field
        deleted_changes = updated_df[updated_df['deleted'] != existing_df['deleted']]
        for _, row in deleted_changes.iterrows():
            logger.info(f"{row['name']} - Deleted: {row['deleted']}")
    except Exception as e:
        logger.exception(f"Error occurred while logging changes: {str(e)}")
        raise

# Create a scheduler
scheduler = BackgroundScheduler()

# Schedule the update_database function to run every 4 days
scheduler.add_job(update_database, 'interval', days=4)

# Start the scheduler
scheduler.start()
logger.info('Scheduler started.')

# Create a Flask app that serves the data in the database
app = Flask(__name__)

@app.route('/')
def get_data():
    logger.info('Retrieving data from the database...')

    try:
        # Connect to the database and get the data
        conn = sqlite3.connect('my_database.db')
        df = pd.read_sql_query('SELECT * FROM my_table', conn)
        conn.close()

        # Convert the data to JSON and return it
        logger.info('Data retrieved successfully.')
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logger.exception(f"Error occurred while retrieving data from the database: {str(e)}")
        return jsonify({'error': 'An error occurred while retrieving data.'}), 500

@app.route('/refresh', methods=['POST'])
def refresh_data():
    logger.info('Refreshing data with PRAW...')

    try:
        # Call the update_database function to refresh the data
        update_database()

        logger.info('Data refreshed successfully.')
        return jsonify({'message': 'Data refreshed successfully.'}), 200
    except Exception as e:
        logger.exception(f"Error occurred while refreshing data: {str(e)}")
        return jsonify({'error': 'An error occurred while refreshing data.'}), 500

if __name__ == '__main__':
    logger.info('Adding test data...')
    add_test_data()

    logger.info('Starting the Flask app...')
    app.run()
