from cassandra.cluster import Cluster
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        # Create Cassandra connection and obtain a session
        cluster = Cluster(['127.0.0.1'])
        session = cluster.connect()

        rows = session.execute(
            "SELECT * FROM system.schema_keyspaces WHERE keyspace_name='mikiapp'")

        if rows:
            msg = ' It looks like you already have a mikiapp keyspace.\nDo you '
            msg += 'want to delete it and recreate it? All current data will '
            msg += 'be deleted! (y/n): '
            resp = raw_input(msg)
            if not resp or resp[0] != 'y':
                print "Ok, then we're done here."
                return
            session.execute("DROP KEYSPACE mikiapp")

        print "Creating keyspace..."
        session.execute("""
            CREATE KEYSPACE mikiapp
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace("mikiapp")

        print "Creating users columnfamily..."
        session.execute("""
            CREATE TABLE users (
                username text PRIMARY KEY,
                password text,
            )
        """)
#name text,
#about text,
#pic blob,
#url text,

        print "Creating reading columnfamily..."
        session.execute("""
            CREATE TABLE reading (
                username text,
                readed text,
                since timestamp,
                PRIMARY KEY(username, readed)
            )
        """)

        print "Creating readers columnfamily..."
        session.execute("""
            CREATE TABLE readers (
                username text,
                reading text,
                since timestamp,
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
                username text,
                time timeuuid,
                mikiid uuid,
                PRIMARY KEY (username, time)
            ) WITH CLUSTERING ORDER BY (time DESC)
            """)

        print "Creating timeline columnfamily..."
        session.execute("""
            CREATE TABLE timeline (
                username text,
                time timeuuid,
                mikiid uuid,
                PRIMARY KEY (username, time)
            ) WITH CLUSTERING ORDER BY (time DESC)
            """)

        print 'All done!'


