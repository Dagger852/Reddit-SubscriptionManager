# app.py
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

        # Create a list of dictionaries containing subreddit and user information
        data = []
        for sub in subreddits:
            data.append({
                'Subscription': sub.display_name,
                'Type': 'User' if sub.display_name.startswith('u_') else 'Subreddit',
                'Hyperlink': f"https://reddit.com/u/{sub.display_name[2:]}" if sub.display_name.startswith('u_') else f"https://reddit.com/r/{sub.display_name}",
                'Deleted': 'No'
            })

        return data
    except Exception as e:
        logger.exception(f"Error occurred while making API request: {str(e)}")
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
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Subscription'], keep='last')

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

# Function to log the changes
def log_changes(existing_df, updated_df):
    try:
        # Get the new subscriptions added
        new_subs = set(updated_df['Subscription']) - set(existing_df['Subscription'])
        if new_subs:
            logger.info(f"New subscriptions added: {', '.join(new_subs)}")

        # Get the subscriptions removed
        removed_subs = set(existing_df['Subscription']) - set(updated_df['Subscription'])
        if removed_subs:
            logger.info(f"Subscriptions removed: {', '.join(removed_subs)}")

        # Get the changes to the "Deleted" field
        deleted_changes = updated_df[updated_df['Deleted'] != existing_df['Deleted']]
        for _, row in deleted_changes.iterrows():
            logger.info(f"{row['Subscription']} - Deleted: {row['Deleted']}")
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
