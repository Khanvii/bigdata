from confluent_kafka import Producer

# Configuration for Kafka producer
conf = {
    'bootstrap.servers': 'localhost:39092',  # Replace with your Kafka broker(s)
    'client.id': 'python-producer'
}

# Create Producer instance
producer = Producer(conf)

# Define a delivery callback function
def delivery_callback(err, msg):
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Produce messages
for i in range(10):
    message = f"Hello Kafka! Message {i}"
    
    # Send message to Kafka
    producer.produce('my_topic', key=str(i), value=message, callback=delivery_callback)
    
    # Poll to handle delivery reports
    producer.poll(0)

# Flush remaining messages in the buffer
producer.flush()

print("Finished producing messages to Kafka.")
