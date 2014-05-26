from django.db import models

from uuid import uuid1, UUID
import random
from datetime import datetime

from cassandra.cluster import Cluster

cluster = Cluster()
session = cluster.connect('mikiapp')
session.execute("USE mikiapp")

# Prepared statements, need to reuse as much as possible by binding new values
mikis_query = None
userline_query = None
timeline_query = None
reading_query = None
readers_query = None
remove_friends_query = None
remove_followers_query = None
add_user_query = None
get_mikis_query = None
get_usernames_query = None
get_followers_query = None
get_friends_query = None

# Not scalable, need to change
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

def _get_line(table, username, start, limit):
    """
    Gets a timeline or a userline given a username, a start, and a limit.
    """
    global get_mikis_query
    if get_mikis_query is None:
        get_mikis_query = session.prepare("""
            SELECT * FROM mikis WHERE mikiid=?
            """)


    # First we need to get the raw timeline (in the form of tweet ids)
    query = "SELECT time, mikiid FROM {table} WHERE username=%s {time_clause} LIMIT %s"

    # See if we need to start our page at the beginning or further back
    if not start:
        time_clause = ''
        params = (username, limit)
    else:
        time_clause = 'AND time < %s'
        params = (username, UUID(start), limit)

    query = query.format(table=table, time_clause=time_clause)

    results = session.execute(query, params)
    if not results:
        return [], None

    # If we didn't get to the end, return a starting point for the next page
    if len(results) == limit:
        # Find the oldest ID
        oldest_timeuuid = min(row.time for row in results)

        # Present the string version of the oldest_timeuuid for the UI
        next_timeuuid = oldest_timeuuid.urn[len('urn:uuid:'):]
    else:
        next_timeuuid = None

    # Now we fetch the tweets themselves
    futures = []
    for row in results:
        futures.append(session.execute_async(
            get_mikis_query, (row.mikiid, )))

    mikis = [f.result()[0] for f in futures]
    return (mikis, next_timeuuid)


def get_user_by_username(username):
    """
    Given a username, this gets the user record.
    """
    global get_usernames_query
    if get_usernames_query is None:
        get_usernames_query = session.prepare("""
            SELECT * FROM users WHERE username=?
            """)

    rows = session.execute(get_usernames_query, (username,))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]

def get_reading_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people that the user is
    reading.
    """
    global get_reading_query
    if get_reading_query is None:
        get_reading_query = session.prepare("""
            SELECT readed FROM reading WHERE username=? LIMIT ?
            """)


    rows = session.execute(get_reading_query, (username, count))
    return [row.readed for row in rows]

def get_readers_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people reading that user.
    """
    global get_readers_query
    if get_readers_query is None:
        get_readers_query = session.prepare("""
            SELECT reading FROM readers WHERE username=? LIMIT ?
        """)

    rows = session.execute(get_readers_query, (username, count))
    return [row.reading for row in rows]


def get_users_for_usernames(usernames):
    """
    Given a list of usernames, this gets the associated user object for each
    one.
    """
    global get_usernames_query
    if get_usernames_query is None:
        get_usernames_query = session.prepare("""
            SELECT * FROM users WHERE username=?
            """)

    futures = []
    for user in usernames:
        future = session.execute_async(get_usernames_query, (user, ))
        futures.append(future)

    users = []
    for user, future in zip(usernames, futures):
        results = future.result()
        if not results:
            raise NotFound('User %s not found' % (user,))
        users.append(results[0])

    return users


def get_reading(username, count=5000):
    """
    Given a username, gets the people that the user is following.
    """
    reading_usernames = get_reading_usernames(username, count=count)
    return get_users_for_usernames(reading_usernames)


def get_readers(username, count=5000):
    """
    Given a username, gets the people following that user.
    """
    readers_usernames = get_readers_usernames(username, count=count)
    return get_users_for_usernames(readers_usernames)


def get_timeline(username, start=None, limit=None):
    """
    Given a username, get their miki timeline (their and users they reading mikis).
    """
    return _get_line("timeline", username, start, limit)

def get_userline(username, start=None, limit=40):
    """
    Given a username, get their userline (their mikis).
    """
    return _get_line("userline", username, start, limit)

def get_profile(username):
    """
    Given a username, get user profile info - name, about, pic, url
    """
    cursor.execute("SELECT name, about, pic, url FROM users WHERE username = :username", dict(username=username))

    profile = []

    for row in cursor:
        profile.append({"name": row[0], "about": row[1], "pic": row[2], "url": row[3]})

    return profile

def get_miki(mikiid):
    """
    Given a miki id, this gets the entire miki record.
    """
    global get_mikis_query
    if get_mikis_query is None:
        get_mikis_query = session.prepare("""
            SELECT * FROM mikis WHERE mikiid=?
            """)

    results = session.execute(get_mikis_query, (mikiid, ))
    if not results:
        raise NotFound('Miki %s not found' % (mikiid,))
    else:
        return results[0]


def get_mikis_for_mikiids(mikiids):
    """
    Given a list of miki ids, this gets the associated miki object for each
    one.
    """
    global get_mikis_query
    if get_mikis_query is None:
        get_mikis_query = session.prepare("""
            SELECT * FROM mikis WHERE mikiid=?
            """)

    futures = []
    for mikiid in mikiids:
        futures.append(session.execute_async(get_mikis_query, (mikiid,)))

    mikis = []
    for mikiid, future in zip(mikiid, futures):
        result = future.result()
        if not result:
            raise NotFound('Miki %s not found' % (mikiid,))
        else:
            mikis.append(result[0])

    return mikis


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
    global add_user_query
    if add_user_query is None:
        add_user_query = session.prepare("""
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """)

    session.execute(add_user_query, (username, password))


def _timestamp_to_uuid(time_arg):
    # TODO: once this is in the python Cassandra driver, use that
    microseconds = int(time_arg * 1e6)
    timestamp = int(microseconds * 10) + 0x01b21dd213814000L

    time_low = timestamp & 0xffffffffL
    time_mid = (timestamp >> 32L) & 0xffffL
    time_hi_version = (timestamp >> 48L) & 0x0fffL

    rand_bits = random.getrandbits(8 + 8 + 48)
    clock_seq_low = rand_bits & 0xffL
    clock_seq_hi_variant = 0b10000000 | (0b00111111 & ((rand_bits & 0xff00L) >> 8))
    node = (rand_bits & 0xffffffffffff0000L) >> 16
    return UUID(
        fields=(time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node),
        version=1)


def save_profile(username, password, name, about, pic, url):
    """
    Saves the user profile settings.
    """
    session.execute("INSERT INTO users (username, password, name, about, pic , url) VALUES (%s,%s,%s,%s,%s,%s)", (username, password, name, about, pic, url))


def save_miki(mikiid, username, body, timestamp=None):
    """
    Saves the miki record.
    """

    global tweets_query
    global userline_query
    global timeline_query

    # Prepare the statements required for adding the tweet into the various timelines
    # Initialise only once, and then re-use by binding new values
    if mikis_query is None:
        mikis_query = session.prepare("""
            INSERT INTO mikis (mikiid, username, body)
            VALUES (?, ?, ?)
            """)

    if userline_query is None:
        userline_query = session.prepare("""
            INSERT INTO userline (username, time, mikiid)
            VALUES (?, ?, ?)
            """)

    if timeline_query is None:
        timeline_query = session.prepare("""
            INSERT INTO timeline (username, time, mikiid)
            VALUES (?, ?, ?)
            """)

    if timestamp is None:
        now = uuid1()
    else:
        now = _timestamp_to_uuid(timestamp)

    # Insert into mikis, then into the user's timeline, then into the public one
    session.execute(miki_query, (mikiid, username, body))

    session.execute(userline_query, (username, now, mikiid))

    session.execute(userline_query, (PUBLIC_USERLINE_KEY, now, mikiid))

    # Get the user's followers, and insert the tweet into all of their streams
    futures = []
    readers_usernames = [username] + get_readers_usernames(username)
    for reader_username in readers_usernames:
        futures.append(session.execute_async(timeline_query, (reader_username, now, mikiid)))

    for future in futures:
        future.result()


def delete_miki(mikiid):
    """
    Given miki id deletes that miki from everywhere
    """
    global delete_mikis_query
    global delete_userline_query
    global delete_timeline_query

    # Prepare the statements required for deleting the miki from the various timelines
    if delete_mikis_query is None:
        delete_miki_query = session.prepare("""
        DELETE FROM mikis WHERE mikiid=?
        """)

    if delete_userline_query is None:
        delete_userline_query = session.prepare("""
        DELETE FROM userline WHERE mikiid=?
        """)

    if delete_timeline_query is None:
        delete_timeline_query = session.prepare("""
        DELETE FROM timeline WHERE mikiid=?
        """)

    session.execute(delete_mikis_query, (mikiid))
    session.execute(delete_userline_query, (mikiid))
    session.execute(delete_timeline_query, (mikiid))


def read(from_username, to_usernames):
    """
    Adds a read relationship from one user to others.
    """
    global reading_query
    global readers_query

    if reading_query is None:
        reading_query = session.prepare("""
            INSERT INTO reading (username, readed, since)
            VALUES (?, ?, ?)
            """)

    if readers_query is None:
        readers_query = session.prepare("""
            INSERT INTO readers (username, reading, since)
            VALUES (?, ?, ?)
            """)

    now = datetime.utcnow()
    futures = []
    for to_username in to_usernames:
        futures.append(session.execute_async(reading_query, (from_username, to_username, now)))

        futures.append(session.execute_async(readers_query, (to_username, from_username, now)))

    for future in futures:
        future.result()


def unread(from_username, to_usernames):
    """
    Removes a read relationship from one user to others.
    """
    global remove_reading_query
    global remove_readers_query

    if remove_reading_query is None:
        remove_reading_query = session.prepare("""
            DELETE FROM reading WHERE username=? AND readed=?
            """)
    if remove_readers_query is None:
        remove_readers_query = session.prepare("""
            DELETE FROM readers WHERE username=? AND reading=?
            """)

    futures = []
    for to_username in to_usernames:
        futures.append(session.execute_async(remove_reading_query,
            (from_username, to_username)))

        futures.append(session.execute_async(remove_readers_query,
            (to_username, from_username)))

    for future in futures:
        future.result()
