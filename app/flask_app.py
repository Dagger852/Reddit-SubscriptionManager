from flask import Flask, render_template, request, redirect, url_for, jsonify
import praw
import sqlite3

app = Flask(__name__)

# PRAW configuration
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
USER_AGENT = 'your_user_agent'

# SQLite database connection
DATABASE = 'subreddits.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index7.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        # Retrieve the list of existing subscriptions using the PRAW library
        reddit = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent=USER_AGENT)
        subscriptions = list(reddit.user.subreddits(limit=None))

        # Process each subscription and store the information in the database
        conn = get_db_connection()
        for subscription in subscriptions:
            # Extract relevant information from the subscription object
            name = subscription.display_name
            # Add other relevant information as needed

            # Store the subscription information in the database
            conn.execute('''
                INSERT INTO subreddits (name)
                VALUES (?)
            ''', (name,))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('setup.html')

if __name__ == '__main__':
    app.run(debug=True)