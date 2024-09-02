import logging
import psycopg

# Define connection to your CockroachDB cluster
def init_conn():
    db_url = (
        "postgresql://localhost:26257/defaultdb"
        "?sslrootcert=C:/Users/SST-LAB/Desktop/Tireni/cockroachdb1/certs/ca.crt"
        "&sslkey=C:/Users/SST-LAB/Desktop/Tireni/cockroachdb1/certs/client.tireni.key.pk8"
        "&sslcert=C:/Users/SST-LAB/Desktop/Tireni/cockroachdb1/certs/client.tireni.crt"
        "&sslmode=verify-full"
        "&user=Tireni"
        "&password=cockroach"
    )

    conn = psycopg.connect(db_url, application_name="kafka-cockroach illustration")
    return conn

# Get connection
def getConnection(mandatory):
    try:
        conn = init_conn()
        return conn
    except Exception as e:
        logging.fatal("Database connection failed: {}".format(e))
        if mandatory:
            exit(1)  # Database connection must succeed to proceed.
