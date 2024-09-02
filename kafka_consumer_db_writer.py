from kafka import KafkaConsumer
from cockroach_connect import getConnection
import logging
from datetime import datetime
# Get mandatory connection
conn = getConnection(True)
# Define how to write to database
def cockroachWrite(event):
    try:
        conn.autocommit = True
        # Here we are using raw SQL, You can also use ORMs like SQLAlchemy.
        # For cockroachdb datatypes, see https://www.cockroachlabs.com/docs/stable/data-types# Readoff the data from event
        #Kafka seems to use 13digit epoch time, so we need to convert to equivalent of 10 digit by dividing by 1000
        timestamp = int(event.timestamp/1000)
        eventTimestamp = datetime.fromtimestamp(timestamp) #convert event.timestamp from epoch to datetime
        eventValue = (event.value).decode()
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS quickstart_events (id SERIAL PRIMARY KEY, timestamp TIMESTAMP, value STRING)")
            logging.debug("create_accounts(): status message: %s", cur.statusmessage)
        #Write to database
        if eventTimestamp and eventValue:
            cur.execute("INSERT INTO quickstart_events (timestamp, value) VALUES (%s, %s)", (eventTimestamp, eventValue))
            conn.commit()
        else:
            logging.debug("Can't add or create table.")  

    except Exception as e:
        logging.error("Problem writing to database: {}".format(e))



consumer = KafkaConsumer("connect-file-pulse-raw-logs", bootstrap_servers=['broker:29092'])
    #Let's consume as they are published, by removing auto_offset_reset='earliest'
#consumer = KafkaConsumer('quickstart-events', bootstrap_servers=['cockroach:26257'])
for msg in consumer:
    # write to database.
    cockroachWrite(msg)
    logging.debug("Msg seen.") 