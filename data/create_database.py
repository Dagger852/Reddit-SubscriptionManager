import sqlite3

# Create a connection to the database file
conn = sqlite3.connect('subreddits.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Create the subreddits table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subreddits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        rank INTEGER,
        vip INTEGER,
        free INTEGER,
        rr INTEGER,
        pp INTEGER,
        alt_acct_1 TEXT,
        alt_acct_2 TEXT,
        deleted INTEGER,
        tags TEXT,
        other TEXT,
        add INTEGER
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()