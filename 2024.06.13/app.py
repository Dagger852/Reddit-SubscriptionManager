import csv
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_migrate import Migrate
from config import Config
from models import db, Subreddit, ChangeLog
import praw
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables to track API usage
api_requests = []
throttle_interval = 60  # Initial throttle interval in seconds
throttle_limit = 55  # API request limit per minute
retry_delay = 60  # Delay in seconds before retrying a failed request

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Initialize PRAW
reddit = praw.Reddit(
    client_id=app.config['REDDIT_CLIENT_ID'],
    client_secret=app.config['REDDIT_CLIENT_SECRET'],
    user_agent=app.config['REDDIT_USER_AGENT'],
    username=app.config['REDDIT_USERNAME'],
    password=app.config['REDDIT_PASSWORD']
)

# print(reddit.auth.authorize(code))
print(reddit.user.me())

@app.before_first_request
def setup():
    logger.info("Setting up the database and refreshing subscriptions.")
    with app.app_context():
        db.create_all()
    refresh_subscriptions()

def is_user_deleted(username):
    try:
        reddit.redditor(username).name  # Access fullname to check existence
        return False  # User account exists
    except praw.exceptions.RedditAPIException as e:
        if e.error_type == 'NOT_FOUND':
            return True  # User account is deleted
        else:
            raise  # Re-raise if it's not a 'NOT_FOUND' error

def is_user_suspended(username):
    try:
        reddit.redditor(username).name  # Access fullname to check existence
        return False  # User account exists and is not suspended
    except praw.exceptions.RedditAPIException as e:
        if e.error_type == 'NOT_FOUND':
            return False  # User account is deleted
        elif e.error_type == 'FORBIDDEN':
            return True  # User account is suspended
        else:
            raise  # Re-raise if it's not a 'NOT_FOUND' or 'FORBIDDEN' error

def check_deleted_users():
    logger.info("Checking for deleted users.")
    subreddits = Subreddit.query.all()
    deleted_users = []
    for subreddit in subreddits:
        if not subreddit.deleted:
            if is_user_deleted(subreddit.name):
                subreddit.deleted = True
                db.session.commit()
                deleted_users.append(subreddit.name)
                logger.info(f"User {subreddit.name} marked as deleted.")

    if deleted_users:
        with open("deleted_users.log", "a") as log_file:
            log_file.write(f"Deleted users check on {datetime.now()}:\n")
            for user in deleted_users:
                log_file.write(f"{user}\n")
        flash(f"Deleted users detected: {', '.join(deleted_users)}", 'warning')

def refresh_subscriptions():
    logger.info("Refreshing subscriptions from Reddit.")
    subreddits = list(reddit.user.subreddits(limit=None))
    logger.debug(f"Retrieved subreddits: {subreddits}")

    current_subreddits = {subreddit.name: subreddit for subreddit in Subreddit.query.all()}
    
    data = []
    for sub in subreddits:
        name = sub.display_name
        data.append(
            {
                "name": name,
                "type": None,
                "title": sub.title,
                "url": None,
                "rank": None,
                "vip": None,
                "free": None,
                "rr": None,
                "pp": None,
                "alt_acct1": None,
                "alt_acct2": None,
                "deleted": False,
                "tags": None,
            }
        )
    logger.debug(f"Initial data: {data}")

   # Process the retrieved data and determine the subreddit type and rank
    for sub in data:
        name = sub["name"]
        if name.startswith("u_"):
            sub["type"] = "User"
            sub["url"] = f"http://reddit.com/{name.replace('u_', 'u/')}"
        else:
            sub["type"] = "Subreddit"
            sub["url"] = f"http://reddit.com/r/{name}"
        # logger.debug(f"Processed subreddit: {sub}")


    new_subreddits = {sub["name"]: sub for sub in data}

    added_subreddits = set(new_subreddits.keys()) - set(current_subreddits.keys())
    for name in added_subreddits:
        subreddit = new_subreddits[name]
        new_sub = Subreddit(
            name=subreddit["name"],
            type=subreddit["type"],
            title=subreddit["title"],
            url=subreddit["url"],
            rank=subreddit["rank"],
            vip=subreddit["vip"],
            free=subreddit["free"],
            rr=subreddit["rr"],
            pp=subreddit["pp"],
            alt_acct1=subreddit["alt_acct1"],
            alt_acct2=subreddit["alt_acct2"],
            tags=subreddit["tags"],
            deleted=subreddit["deleted"],
        )
        db.session.add(new_sub)
        log_change('Added', name, subreddit["title"])
        logger.info(f"Added new subreddit: {name}")

    removed_subreddits = set(current_subreddits.keys()) - set(new_subreddits.keys())
    for name in removed_subreddits:
        subreddit = current_subreddits[name]
        log_change('Removed', name, subreddit.title)
        db.session.delete(subreddit)
        logger.info(f"Removed subreddit: {name}")

    db.session.commit()
    logger.info("Subscription refresh complete.")


def log_change(action, name, title):
    change = ChangeLog(action=action, name=name, title=title)
    db.session.add(change)
    db.session.commit()
    logger.info(f"Logged change: {action} - {name} - {title}")

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    sort_by = request.args.get('sort_by', 'name')
    direction = request.args.get('direction', 'asc')

    sort_column = {
        'name': Subreddit.name,
        'title': Subreddit.title
    }.get(sort_by, Subreddit.name)

    if direction == 'desc':
        sort_column = sort_column.desc()

    subreddits = Subreddit.query.filter_by(deleted=False).order_by(sort_column).paginate(page=page, per_page=per_page)
    logger.info(f"Displaying page {page} of subreddits sorted by {sort_by} in {direction} order.")

    return render_template('index.html', subreddits=subreddits, sort_by=sort_by, direction=direction, per_page=per_page)

# delete subreddit entry
@app.route('/deleted')
def deleted_entries():
    page = request.args.get('page', 1, type=int)
    subreddits = Subreddit.query.filter_by(deleted=True).paginate(page=page, per_page=25)
    logger.info("Displaying deleted entries.")
    return render_template('deleted_entries.html', subreddits=subreddits)

# restores subreddit entry
@app.route('/restore_subreddit/<int:id>', methods=['GET', 'POST'])
def restore_subreddit(id):
    subreddit = Subreddit.query.get_or_404(id)
    if request.method == 'POST':
        subreddit.deleted = False
        db.session.commit()
        flash('Subreddit restored successfully.', 'success')
        return redirect(url_for('index')) 
    return render_template('restore_subreddit.html', subreddit=subreddit)

@app.route('/add', methods=['GET', 'POST'])
def add_subreddit():
    if request.method == 'POST':
        name = request.form['name']
        rank = request.form.get('rank')
        vip = request.form.get('VIP')
        free = request.form.get('Free')
        rr = request.form.get('RR')
        pp = request.form.get('PP')
        alt_acct1 = request.form.get('AltAcct1')
        alt_acct2 = request.form.get('AltAcct2')
        tags = request.form.get('Tags')
        if not Subreddit.query.filter_by(name=name).first():
            new_subreddit = Subreddit(name=name, title=request.form['title'], rank=rank, vip=vip, free=free, rr=rr, pp=pp, alt_acct1=alt_acct1, alt_acct2=alt_acct2, tags=tags)
            db.session.add(new_subreddit)
            db.session.commit()
            log_change('Added', name, new_subreddit.title)
            flash(f'Subreddit {name} added successfully!', 'success')
            logger.info(f"Subreddit {name} added successfully.")
        else:
            flash(f'Subreddit {name} already exists.', 'danger')
            logger.warning(f"Attempted to add existing subreddit: {name}.")
        return redirect(url_for('index'))
    return render_template('add_subreddit.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_subreddit(id):
    subreddit = Subreddit.query.get_or_404(id)
    if request.method == 'POST':
        old_name = subreddit.name
        old_title = subreddit.title
        subreddit.name = request.form['name']
        subreddit.title = request.form['title']
        subreddit.rank = request.form.get('rank')
        subreddit.vip = request.form.get('VIP')
        subreddit.free = request.form.get('Free')
        subreddit.rr = request.form.get('RR')
        subreddit.pp = request.form.get('PP')
        subreddit.alt_acct1 = request.form.get('AltAcct1')
        subreddit.alt_acct2 = request.form.get('AltAcct2')
        subreddit.tags = request.form.get('Tags')
        db.session.commit()
        log_change('Edited', old_name, f'from "{old_title}" to "{subreddit.title}"')
        flash(f'Subreddit {subreddit.name} updated successfully!', 'success')
        logger.info(f"Subreddit {subreddit.name} updated successfully.")
        return redirect(url_for('index'))
    return render_template('edit_subreddit.html', subreddit=subreddit)

@app.route('/delete_subreddit/<int:id>', methods=['GET', 'POST'])
def delete_subreddit(id):
    subreddit = Subreddit.query.get_or_404(id)
    if request.method == 'POST':
        # Mark subreddit as deleted
        subreddit.deleted = True
        db.session.commit()
        flash('Subreddit successfully marked as deleted.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_subreddit.html', subreddit=subreddit) 

@app.route('/log')
def view_log():
    logs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
    for log in logs:
        log.timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    logger.info("Displaying change log.")
    return render_template('log.html', logs=logs)

@app.route('/export', methods=['GET'])
def export():
    subreddits = Subreddit.query.filter_by(deleted=False).all()
    return export_to_csv(subreddits, 'active_subreddits.csv')

@app.route('/export_deleted', methods=['GET'])
def export_deleted():
    subreddits = Subreddit.query.filter_by(deleted=True).all()
    return export_to_csv(subreddits, 'deleted_subreddits.csv')

def export_to_csv(subreddits, filename):
    si = []
    si.append(['Name', 'Title', 'Rank', 'VIP', 'Free', 'RR', 'PP', 'AltAcct1', 'AltAcct2', 'Tags'])
    for subreddit in subreddits:
        si.append([subreddit.name, subreddit.title, subreddit.rank, subreddit.vip, subreddit.free, subreddit.rr, subreddit.pp, subreddit.alt_acct1, subreddit.alt_acct2, subreddit.tags])

    si = "\n".join([",".join(map(str, row)) for row in si])

    response = make_response(si)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-type'] = 'text/csv'
    logger.info(f"Exported data to {filename}")
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        check_deleted_users()
    app.run(debug=True)
