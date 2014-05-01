from django.db import models

import uuid
import time
from datetime import datetime
import threading
import cql

local = threading.local()
try:
    cursor = local.cursor
except AttributeError:
    connection = cql.connect("localhost", cql_version="3.0.0")
    cursor = local.cursor = connection.cursor()
    cursor.execute("USE mikiapp")

__all__ = [
    'get_user_by_username', 'get_reading_usernames', 'get_readers_usernames', 'get_timeline',
    'get_userline', 'get_miki', 'save_user', 'save_miki', 'add_friends', 'remove_friend',
    'DatabaseError', 'NotFound', 'InvalidDictionary', 'PUBLIC_TIMELINE_KEY'
]


PUBLIC_TIMELINE_KEY = '!PUBLIC!'


# EXCEPTIONS

class DatabaseError(Exception):
    """
    The base error that functions in this module will raise when things go
    wrong.
    """
    pass

class NotFound(DatabaseError):
    pass
class InvalidDictionary(DatabaseError):
    pass


# QUERYING APIs

def get_user_by_username(username):
    """
    Given a username, this gets the user record.
    """
    cursor.execute("SELECT password FROM users WHERE username = :user", dict(user=username))
    if not (cursor.rowcount > 0):
        raise NotFound('User %s not found' % (username,))
    return dict(password=cursor.fetchone()[0])

def get_reading_usernames(username):
    """
    Given a username, gets the usernames of the people that the user is
    reading.
    """
    cursor.execute("SELECT readed FROM reading WHERE username = :user", dict(user=username))
    return [row[0] for row in cursor if cursor.rowcount > 0]

def get_readers_usernames(username):
    """
    Given a username, gets the usernames of the people reading that user.
    """
    cursor.execute("SELECT reading FROM readers WHERE username = :user", dict(user=username))
    return [row[0] for row in cursor if cursor.rowcount > 0]

def get_timeline(username, start=None, limit=None):
    """
    Given a username, get their miki timeline (their and users they reading mikis).
    """
    if start:
        posted_at_start = str(start)
    else:
        posted_at_start = "now()"

    query = """
        SELECT mikiid, posted_by, body, unixTimestampOf(mikiid) FROM timeline
        WHERE username = :username AND mikiid < %s ORDER BY mikiid DESC LIMIT %d
    """
    cursor.execute(query % (posted_at_start, limit+1), dict(username=username))

    nextid = None
    mikis = []

    for row in cursor:
        mikis.append({"id": row[0], "username": row[1], "body": row[2], "time": row[3]})

    if len(mikis) > limit:
        nextid = mikis.pop()["id"]

    return (mikis, nextid)

def get_userline(username, start=None, limit=40):
    """
    Given a username, get their userline (their mikis).
    """
    if start:
        posted_at_start = str(start)
    else:
        posted_at_start = "now()"

    query = """
        SELECT mikiid, body, unixTimestampOf(mikiid) FROM userline
        WHERE username = :username AND mikiid < %s ORDER BY mikiid DESC LIMIT %d
    """
    cursor.execute(query % (posted_at_start, limit+1), dict(username=username))

    nextid = None
    mikis = []

    for row in cursor:
        mikis.append({"id": row[0], "username": username, "body": row[1], "time": row[2]})

    if len(mikis) > limit:
        nextid = mikis.pop()["id"]

    return (mikis, nextid)

def get_profile(username):
    """
    Given a username, get user profile info - name, about, pic, url
    """
    cursor.execute("SELECT name, about, pic, url FROM users WHERE username = :username", dict(username=username))

    profile = []

    for row in cursor:
        profile.append({"name": row[0], "about": row[1], "pic": row[2], "url": row[3]})

    return profile

def get_miki(miki_id):
    """
    Given a miki id, this gets the entire miki record.
    """
    cursor.execute("SELECT username, body FROM mikis WHERE mikiid = :uuid", dict(uuid=miki_id))
    if not (cursor.rowcount > 0):
        raise NotFound('Miki %s not found' % (miki_id,))
    row = cursor.fetchone()
    return {'username': row[0], 'body': row[1].decode('utf-8')}

def get_miki_time(mikiid):
    """
    Given a miki id, gets the time miki was created.
    """
    cursor.execute("SELECT WRITETIME (body) FROM timeline WHERE mikiid = :mikiid ALLOW FILTERING", dict(mikiid=mikiid))
    miki_time = cursor.fetchone()
    return miki_time

def search(query):
    """
    Basic search
    """
    search_results=[]


# INSERTING APIs

def save_user(username, password):
    """
    Saves the user record.
    """
    cursor.execute(
        "UPDATE users SET password = :password WHERE username = :user_id",
        dict(password=password, user_id=username))


def save_profile(username, password, name, about, pic, url):
    """
    Saves the user profile settings.
    """
    cursor.execute("SELECT ")
    cursor.execute("INSERT INTO users (username, password, name, about, pic , url) VALUES (:user_id, :password, :name, :about, :pic, :url)"
        "UPDATE users SET password = :password, name = :name, about = :about, pic = :pic , url = :url WHERE username = :user_id",
        dict(password=password, name=name, about=about, pic=pic, url=url, user_id=username))


def save_miki(username, body):
    """
    Saves the miki record.
    """
    # Create a type 1 UUID based on the current time.
    miki_id = uuid.uuid1()

    # Make sure the miki body is utf-8 encoded.
    body = body.encode('utf-8')
    # Insert the miki into mikis, then into the user's userline, then into the publicline.
    cursor.execute(
        "INSERT INTO mikis (mikiid, username, body) VALUES (:miki_id, :username, :body)",
        dict(miki_id=miki_id, username=username, body=body))
    cursor.execute(
        "INSERT INTO userline (username, mikiid, body) VALUES (:username, :posted_at, :body)",
        dict(username=username, posted_at=miki_id, body=body))
    cursor.execute(
        """INSERT INTO timeline (username, mikiid, posted_by, body)
           VALUES (:username, :posted_at, :posted_by, :body)""",
        dict(username=PUBLIC_TIMELINE_KEY, posted_at=miki_id, posted_by=username, body=body))

    # Get the user's readers, and insert the miki into all of their feeds
    reader_usernames = [username] + get_readers_usernames(username)
    for reader_username in reader_usernames:
        cursor.execute(
            """INSERT INTO timeline (username, mikiid, posted_by, body)
               VALUES (:username, :posted_at, :posted_by, :body)""",
            dict(username=reader_username, posted_at=miki_id, posted_by=username, body=body))


def delete_miki(mikiid):
    """
    Given miki id deletes that miki from everywhere
    """
    cursor.execute(
        "DELETE FROM mikis WHERE mikiid = :mikiid", dict(mikiid=mikiid)
    )
    cursor.execute(
        "DELETE FROM userline WHERE mikiid = :mikiid", dict(mikiid=mikiid)
    )
    cursor.execute(
        "DELETE FROM timeline WHERE mikiid = :mikiid", dict(mikiid=mikiid)
    )


def read(from_username, to_usernames):
    """
    Adds a read relationship from one user to others.
    """

    for to_username in to_usernames:
        cursor.execute(
            "INSERT INTO reading (username, readed) VALUES (:from_username, :to_username)",
            dict(from_username=from_username, to_username=to_username))
        cursor.execute(
            "INSERT INTO readers (username, reading) VALUES (:to_username, :from_username)",
            dict(from_username=from_username, to_username=to_username))

def unread(from_username, to_usernames):
    """
    Removes a read relationship from one user to others.
    """

    for to_username in to_usernames:
        cursor.execute(
            "DELETE FROM reading WHERE username = :from_username AND readed = :to_username",
            dict(from_username=from_username, to_username=to_username))
        cursor.execute(
            "DELETE FROM readers WHERE username = :to_username AND reading = :from_username",
            dict(from_username=from_username, to_username=to_username))

