# Reddit Subscription Manager

This Python script pulls all subreddits that a user follows on Reddit and adds them into a tabular format. The script uses the PRAW (Python Reddit API Wrapper) library to interact with the Reddit API.

## Features

- Authenticate with Reddit using your username, password, client ID, and client secret.
- Retrieve the list of subreddits you are subscribed to.
- Display the list of subscribed subreddits in a tabular format.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/dagger852/reddit-subscriptionmanager.git
    cd reddit-subscriptionmanager
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Create a Reddit application to obtain your client ID and client secret. You can do this at [Reddit's App Preferences](https://www.reddit.com/prefs/apps).

2. Run the script:

    ```bash
    python main.py
    ```

3. You will be prompted to enter your Reddit username, password, client ID, and client secret.

4. The script will authenticate with Reddit and retrieve your subscribed subreddits, displaying them in a table.

## Classes and Functions

### `RedditAuth`

A class that handles the authentication process for accessing the Reddit API.

- **Arguments:**
  - `username`: Your Reddit username.
  - `password`: Your Reddit password.
  - `client_id`: Your Reddit application client ID.
  - `client_secret`: Your Reddit application client secret.

### `SubscriptionManager`

A class that handles the retrieval of the user's subscribed subreddits and formatting them into a table.

- **Arguments:**
  - `auth`: A `RedditAuth` object.

### `main()`

The main function that creates a `RedditAuth` object and a `SubscriptionManager` object and calls the `SubscriptionManager`'s `get_subscriptions()` method to retrieve and display the user's subscribed subreddits.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## Acknowledgements

- [PRAW (Python Reddit API Wrapper)](https://praw.readthedocs.io/en/latest/) for providing the API wrapper for Reddit.


    ##  TO DO LIST
        convert hyperlink into the NAME column (with display name only)
        Update table to load filtering and sorting first,
            then update pagination 
                Update pagination to move deleted entries to separate page (in sidebar?)
                Update pagination to treat IGNORE entries to separate page (in sidebar?)
        Filter Column values (and delete filter value box?)
        Fix .csv export function

        Change Sidebar to be collapsed by default
        Make other table fields editable and easy to write to
        Adjust page sizing for open/close of sidebar
        add logging to CLEAR ENTRIES

        Modal box changes
            Change to black font
            Add a "CANCEL" button, 
                which cancels the add-subreddit function altogether
            

            on Cancel click, close Modal box 
            on Save click,  write to .db  and Close Modal box
