import logging
import psycopg2
from psycopg2 import sql
import json
from kafka import KafkaConsumer
import re
from cockroach_connect import getConnection

# Setup logging
logging.basicConfig(level=logging.INFO)

# Attempt to establish a connection to CockroachDB
try:
    # Get mandatory connection
    conn = getConnection(True)
    logging.info("Successfully connected to CockroachDB.")
except Exception as e:
    logging.error(f"Failed to connect to CockroachDB: {e}")
    raise  # Re-raise the exception to exit if the connection cannot be established

def sanitize_text(text):
    """Sanitize text by removing non-printable characters."""
    if text is None:
        return None
    return re.sub(r'[^\x20-\x7E]', '', text)

def setup_database():
    """Create the table if it does not exist."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bet_events (
                    id SERIAL PRIMARY KEY,  
                    sport_key VARCHAR(100),  
                    sport_title VARCHAR(100),  
                    commence_time VARCHAR(100),  
                    home_team VARCHAR(200),  
                    away_team VARCHAR(200),  
                    bookmaker_key VARCHAR(100),  
                    bookmaker_title VARCHAR(100),   
                    market_key VARCHAR(100), 
                    market_last_update VARCHAR(100), 
                    outcome_name VARCHAR(100),  
                    price DECIMAL(10, 2)
                );
            """)
            conn.commit()
            logging.info("Table created or already exists.")
    except Exception as e:
        logging.error(f"Problem setting up the database: {e}")

def map_football_data(event_data):
    """Create a dictionary to map the data."""
    football_data = {
        'id': event_data.get('id'),
        'sport_key': event_data.get('sport_key'),
        'sport_title': sanitize_text(event_data.get('sport_title')),
        'commence_time': event_data.get('commence_time'),
        'home_team': sanitize_text(event_data.get('home_team')),
        'away_team': sanitize_text(event_data.get('away_team')),
        'bookmakers': [
            {
                'key': bookmaker.get('key'),
                'title': sanitize_text(bookmaker.get('title')),
                'last_update': bookmaker.get('last_update'),
                'markets': [
                    {
                        'key': market.get('key'),
                        'last_update': market.get('last_update'),
                        'outcomes': [
                            {
                                'name': sanitize_text(outcome.get('name')),
                                'price': outcome.get('price'),
                                'point': outcome.get('point', None)
                            }
                            for outcome in market.get('outcomes', [])
                        ]
                    }
                    for market in bookmaker.get('markets', [])
                ]
            }
            for bookmaker in event_data.get('bookmakers', [])
        ]
    }
    return football_data

def cockroach_write(event):
    """Write Kafka event to the database."""
    try:
        # Extract data from the Kafka message
        event_data = event.value
        football_data = map_football_data(event_data)

        # Insert into the database
        with conn.cursor() as cur:
            for bookmaker in football_data['bookmakers']:
                for market in bookmaker['markets']:
                    for outcome in market['outcomes']:
                        cur.execute('''
                            INSERT INTO bet_events (
                                sport_key, sport_title, commence_time, home_team, 
                                away_team, bookmaker_key, bookmaker_title, market_key, market_last_update,
                                outcome_name, price
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
                        ''', (
                            football_data['id'],
                            football_data['sport_key'],
                            football_data['sport_title'],
                            football_data['commence_time'],
                            football_data['home_team'],
                            football_data['away_team'],
                            bookmaker['key'],
                            bookmaker['title'],
                            market['key'],
                            outcome['name'],
                            outcome['price'],
                        ))
            conn.commit()

    except Exception as e:
        logging.error(f"Problem writing to database: {e}")

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'Betting',  # Use the correct Kafka topic for football events
    bootstrap_servers=['broker:39092'],  # Ensure this is the correct broker address
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Setup the database once
setup_database()

# Process messages
for msg in consumer:
    cockroach_write(msg)
