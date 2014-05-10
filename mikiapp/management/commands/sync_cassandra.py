
#import cql
from cassandra.cluster import Cluster

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Create Cassandra connection and obtain a cursor.
        #conn = cql.connect("localhost", cql_version="3.0.0")
        #cursor = conn.cursor()
        cluster = Cluster()
        session = cluster.connect()

        # This can result in data loss, so prompt the user first.
        print
        print "Warning:  This will drop any existing keyspace named \"mikiapp\","
        print "and delete any data contained within."
        print

        if not raw_input("Are you sure? (y/n) ").lower() in ('y', "yes"):
            print "Ok, then we're done here."
            return

        print "Dropping existing keyspace..."
        try: session.execute("DROP KEYSPACE mikiapp")
        except: pass

        print "Creating keyspace..."
        session.execute("""
            CREATE KEYSPACE mikiapp
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.execute("USE mikiapp")

        print "Creating users columnfamily..."
        session.execute("""
            CREATE TABLE users (
                username text PRIMARY KEY,
                password text,
                name text,
                about text,
                pic blob,
                url text,
            )
        """)

        print "Creating reading columnfamily..."
        session.execute("""
            CREATE TABLE reading (
                username text,
                readed text,
                PRIMARY KEY(username, readed)
            )
        """)

        print "Creating readers columnfamily..."
        session.execute("""
            CREATE TABLE readers (
                username text,
                reading text,
                PRIMARY KEY(username, reading)
            )
        """)


        print "Creating mikis columnfamily..."
        session.execute("""
            CREATE TABLE mikis (
                mikiid uuid PRIMARY KEY,
                username text,
                body text
            )
        """)

        print "Creating userline columnfamily..."
        session.execute("""
            CREATE TABLE userline (
                mikiid timeuuid,
                username text,
                body text,
                PRIMARY KEY(username, mikiid)
            )
        """)

        print "Creating timeline columnfamily..."
        session.execute("""
            CREATE TABLE timeline (
                mikiid timeuuid,
                username text,
                posted_by text,
                body text,
                PRIMARY KEY(username, mikiid)
            )
        """)

        print 'All done!'


