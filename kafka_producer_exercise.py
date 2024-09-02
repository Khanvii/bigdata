import requests
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka configuration
KAFKA_BROKER = 'broker:39092'
KAFKA_TOPIC = 'sports_bet'

# Function to serialize data to JSON
def json_serializer(data):
    return json.dumps(data).encode('utf-8')

# Create Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=json_serializer
)

# Replace with the API URL you want to request data from
api_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?apiKey=9aecab910fb22f6b30ba13beb2619600&regions=us&markets=h2h,spreads&oddsFormat=american"

try:
    # Send a GET request to the API
    response = requests.get(api_url)
    
    # Check if the request was successful (status code 200)
    response.raise_for_status()
    
    # Parse the response as JSON
    data = response.json()
    
    # Function to send data to Kafka
    def send_data_to_kafka(data):
        """Send individual JSON objects to Kafka."""
        for json_object in data:
            try:
                # Send each JSON object as a separate Kafka message
                future = producer.send(KAFKA_TOPIC, json_object)
                
                # Asynchronously wait for the send to complete
                future.get(timeout=10)
                
                logging.info(f"Sent data to Kafka: {json_object}")
            except KafkaError as e:
                logging.error(f"Failed to send message: {e}")

    # Send data to Kafka
    send_data_to_kafka(data)

except requests.exceptions.HTTPError as http_err:
    logging.error(f"HTTP error occurred: {http_err}")
except Exception as err:
    logging.error(f"An error occurred: {err}")
finally:
    # Close the producer
    producer.close()

