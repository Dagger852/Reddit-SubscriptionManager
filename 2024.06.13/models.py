from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Subreddit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    type = db.Column(db.String(64), nullable=False)  
    title = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256))
    rank = db.Column(db.String(64))
    vip = db.Column(db.String(64))
    free = db.Column(db.String(64))
    rr = db.Column(db.String(64))
    pp = db.Column(db.String(64))
    alt_acct1 = db.Column(db.String(64))
    alt_acct2 = db.Column(db.String(64))
    tags = db.Column(db.String(128))
    deleted = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Subreddit {self.name}>'

class ChangeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<ChangeLog {self.action} {self.name}>'
