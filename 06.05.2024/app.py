import praw
import pandas as pd
import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
import time
from dotenv import load_dotenv
from prawcore import RequestException, TooManyRequests


# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Variables to track API usage
api_requests = []
throttle_interval = 60  # Initial throttle interval in seconds
throttle_limit = 55  # API request limit per minute
retry_delay = 60  # Delay in seconds before retrying a failed request

# Authenticate with PRAW using environment variables
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)

# print(reddit.auth.authorize(code))
print(reddit.user.me())

# Disable read-only mode (must have a valid authorization)
reddit.read_only = False


# Function to make an API request
def make_api_request():
    max_retries = 3
    retry_delay = 75  # delay in seconds before retrying a failed request

    for retry in range(max_retries):
        try:

            # Get your subscribed subreddits and users
            subreddits = list(reddit.user.subreddits(limit=None))
            logger.debug(f"Retrieved subreddits: {subreddits}")

            # Create a list of dictionaries containing subreddit and user information
            data = []
            for sub in subreddits:
                name = sub.display_name
                data.append(
                    {
                        "name": name,
                        "type": None,
                        "rank": None,
                        "vip": None,
                        "free": None,
                        "rr": None,
                        "pp": None,
                        "altAcct1": None,
                        "altAcct2": None,
                        "deleted": None,
                        "tags": None,
                        "other": None,
                    }
                )
            logger.debug(f"Initial data: {data}")

            # Process the retrieved data and determine the subreddit type and rank
            for sub in data:
                name = sub["name"]
                if name.startswith("u_"):
                    sub["type"] = "User"
                    sub["rank"] = f"http://reddit.com/{name.replace('u_', 'u/')}"
                else:
                    sub["type"] = "Subreddit"
                    sub["rank"] = f"http://reddit.com/r/{name}"
                logger.debug(f"Processed subreddit: {sub}")

            logger.debug(f"Final data: {data}")
            return data

        except TooManyRequests as e:
            # Handle rate limiting error
            logger.error(f"Rate limit exceeded. Retrying in {retry_delay} seconds.")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        except RequestException as e:
            # Handle other API request errors
            logger.error(
                f"API request failed: {str(e)}. Retrying in {retry_delay} seconds."
            )
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        except Exception as e:
            logger.exception(f"Error occurred while making API request: {str(e)}")
            raise

    # If all retries fail, raise an exception
    raise Exception("Max retries exceeded. API request failed.")


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
            logger.warning(
                f"API request limit exceeded. Throttling API polling to every {throttle_interval} seconds."
            )
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
    logger.info("Updating the database...")

    try:
        # Make an API request
        data = make_api_request()

        # Create a dataframe from the list of dictionaries
        new_df = pd.DataFrame(data)
        new_df["last_updated"] = (
            datetime.now()
        )  # Add a 'last_updated' column with the current datetime

        # Save the dataframe to a SQLite database
        conn = sqlite3.connect("app/data/subreddits.db")

        # Load the existing data
        existing_df = pd.read_sql_query("SELECT * FROM subreddits", conn)

        # Merge the new and existing data, keeping only the new records
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(
            subset=["name", "type"], keep="last"
        )

        # Get the new entries since the last run
        last_run = existing_df["last_updated"].max() if not existing_df.empty else None
        new_entries = (
            updated_df[updated_df["last_updated"] > last_run]
            if last_run
            else updated_df
        )

        # Log the changes
        log_changes(existing_df, updated_df)

        # Save the updated data to the database
        updated_df.to_sql("subreddits", conn, if_exists="replace", index=False)

        conn.close()
        logger.info("Database update completed.")
    except TooManyRequests as e:
        # Handle rate limiting error
        logger.error(f"Rate limit exceeded. Retrying in {retry_delay} seconds.")
        time.sleep(retry_delay)
    except RequestException as e:
        # Handle other API request errors
        logger.error(
            f"API request failed: {str(e)}. Retrying in {retry_delay} seconds."
        )
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
        new_subs = set(updated_df["name"]) - set(existing_df["name"])
        if new_subs:
            logger.info(f"New subscriptions added: {', '.join(new_subs)}")

        # Get the subscriptions removed
        removed_subs = set(existing_df["name"]) - set(updated_df["name"])
        if removed_subs:
            logger.info(f"Subscriptions removed: {', '.join(removed_subs)}")

        # Get the changes to the "Deleted" field
        merged_df = pd.merge(
            updated_df,
            existing_df[["name", "type", "deleted"]],
            on=["name", "type"],
            how="left",
            suffixes=("_updated", "_existing"),
        )
        deleted_changes = merged_df[
            merged_df["deleted_updated"] != merged_df["deleted_existing"]
        ]
        for _, row in deleted_changes.iterrows():
            logger.info(f"{row['name']} - Deleted: {row['deleted']}")
    except Exception as e:
        logger.exception(f"Error occurred while logging changes: {str(e)}")
        raise


# Create a scheduler
scheduler = BackgroundScheduler()

# Schedule the update_database function to run every 4 days
scheduler.add_job(update_database, "interval", days=4)

# Start the scheduler
scheduler.start()
logger.info("Scheduler started.")

# Create a Flask app that serves the data in the database
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index2.html")


@app.route("/setup", methods=["GET"])
def setup_get():
    return render_template("setup.html")


@app.route("/refresh", methods=["POST"])
def setup_post():
    try:
        # Call the update_database function to retrieve subscriptions and set up the database
        update_database()
        logger.info("Database setup completed.")
        return redirect(url_for("index"))
    except Exception as e:
        logger.exception(f"Error occurred during database setup: {str(e)}")
        return "An error occurred during database setup."


@app.route("/data")
def get_data():
    logger.info("Retrieving data from the database...")

    try:
        # Connect to the database and get the data
        conn = sqlite3.connect("app/data/subreddits.db")
        df = pd.read_sql_query("SELECT * FROM subreddits", conn)
        logger.info(f"Retrieved data from the database: {df}")
        conn.close()

        # Convert the data to JSON and return it
        logger.info("Data retrieved successfully.")
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        logger.exception(
            f"Error occurred while retrieving data from the database: {str(e)}"
        )
        return jsonify({"error": "An error occurred while retrieving data."}), 500


@app.route("/refresh", methods=["POST"])
def refresh_data():
    logger.info("Refreshing data with PRAW...")

    try:
        # Call the update_database function to refresh the data
        update_database()

        logger.info("Data refreshed successfully.")
        return jsonify({"message": "Data refreshed successfully."}), 200
    except Exception as e:
        logger.exception(f"Error occurred while refreshing data: {str(e)}")
        return jsonify({"error": "An error occurred while refreshing data."}), 500


def update_database():
    logger.info("Updating the database...")

    try:
        # Make an API request
        data = make_api_request()
        logger.info(f"Retrieved data: {data}")

        # Create a dataframe from the list of dictionaries
        new_df = pd.DataFrame(data)
        new_df["last_updated"] = datetime.now()
        logger.info(f"Created new dataframe: {new_df}")

        # Convert 'last_updated' column to string
        new_df["last_updated"] = new_df["last_updated"].astype(str)

        # Save the dataframe to a SQLite database
        conn = sqlite3.connect("app/data/subreddits.db")

        # Load the existing data
        existing_df = pd.read_sql_query("SELECT * FROM subreddits", conn)
        logger.info(f"Loaded existing dataframe: {existing_df}")

        # Merge the new and existing data, keeping only the new records
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(
            subset=["name", "type"], keep="last"
        )
        logger.info(f"Merged dataframe: {updated_df}")

        # Convert 'last_updated' column to string in the merged dataframe
        updated_df["last_updated"] = updated_df["last_updated"].astype(str)

        # Save the updated data to the database
        updated_df.to_sql("subreddits", conn, if_exists="replace", index=False)
        logger.info("Updated data saved to the database.")

        conn.close()
        logger.info("Database update completed.")
    except Exception as e:
        logger.exception(f"Error occurred while updating the database: {str(e)}")
        raise


@app.route("/update-data", methods=["POST"])
def update_data():
    logger.info("Updating data based on user input...")

    try:
        # Get the user input from the request
        user_input = request.json

        # Connect to the database
        conn = sqlite3.connect("app/data/subreddits.db")
        c = conn.cursor()

        # Update the database based on the user input
        for item in user_input:
            name = item["name"]
            field = item["field"]
            value = item["value"]

            # Update the corresponding field in the 'subreddits' table
            c.execute(
                f"UPDATE subreddits SET {field} = ? WHERE name = ?", (value, name)
            )

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        logger.info("Data updated successfully.")
        return jsonify({"message": "Data updated successfully."}), 200
    except Exception as e:
        logger.exception(f"Error occurred while updating data: {str(e)}")
        return jsonify({"error": "An error occurred while updating data."}), 500


@app.route("/clear-entries", methods=["POST"])
def clear_entries():
    logger.info("Clearing all entries from the database...")

    try:
        # Connect to the database
        conn = sqlite3.connect("app/data/subreddits.db")
        c = conn.cursor()

        # Delete all entries from the 'subreddits' table
        c.execute("DELETE FROM subreddits")

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        logger.info("All entries cleared successfully.")
        return jsonify({"message": "All entries cleared successfully."}), 200
    except Exception as e:
        logger.exception(f"Error occurred while clearing entries: {str(e)}")
        return jsonify({"error": "An error occurred while clearing entries."}), 500


if __name__ == "__main__":
    logger.info("Starting the Flask app...")
    app.run()
