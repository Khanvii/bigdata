from datetime import date
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from kafka import KafkaConsumer
import re
import plotly.express as px
import logging

# Initialize counter for limiting number of processed events
count = 0

# Function to sanitize text by removing non-printable characters
def sanitize_text(text):
    """Sanitize text by removing non-printable characters."""
    if text is None:
        return None
    return re.sub(r'[^\x20-\x7E]', '', text)

# Function to fetch and process data from Kafka event
def fetch_data(event):
    try:
        # Extract data from Kafka message
        event_data = event.value
        
        # Process the event data and organize it into a structured dictionary
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

    except Exception as e:
        logging.error(f"Problem writing to database: {e}")
        return None

# Initialize Kafka consumer for football betting events
consumer = KafkaConsumer(
    'sports_bet',  # Kafka topic for football events
    bootstrap_servers=['broker:39092'],  # Broker address
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Initialize an empty list to store fetched events
events_list = []

# Process Kafka messages, limit to 30 events
for msg in consumer:
    count += 1
    event_data = fetch_data(msg)

    print(msg.value)

    # Only append valid (non-None) events
    if event_data:
        events_list.append(event_data)

    # Break if more than 30 messages are processed
    if count > 30:
        break

# Convert the list of events into a pandas DataFrame
df = pd.DataFrame(events_list)

# Check if the DataFrame has any data
if not df.empty:
    # Streamlit App for visualizing betting data
    st.title('NFL Match Betting Data Visualization')

    # Loop through each event (row) in the DataFrame
    for index, row in df.iterrows():
        st.subheader(f"Match {index + 1}: {row['home_team']} vs {row['away_team']}")

        # Display Match Details
        match_details = {
            "Sport": row['sport_title'],
            "Commence Time": row['commence_time'],
            "Home Team": row['home_team'],
            "Away Team": row['away_team']
        }
        st.table(pd.DataFrame(match_details, index=[0]))

        # Process bookmaker and market data
        if 'bookmakers' in row and len(row['bookmakers']) > 0:
            bookmaker = row['bookmakers'][0]  # Extract the first bookmaker
            
            st.subheader(f"Odds provided by {bookmaker['title']} (Last Updated: {bookmaker['last_update']})")
            
            # Head-to-Head (H2H) Odds
            h2h_market = next((market for market in bookmaker['markets'] if market['key'] == 'h2h'), None)
            if h2h_market:
                h2h_outcomes = h2h_market['outcomes']
                h2h_df = pd.DataFrame(h2h_outcomes)
                fig_h2h = px.bar(h2h_df, x='name', y='price', title='Head-to-Head (H2H) Odds', labels={'name': 'Team', 'price': 'Odds'})
                st.plotly_chart(fig_h2h)
            
            # Point Spreads
            spread_market = next((market for market in bookmaker['markets'] if market['key'] == 'spreads'), None)
            if spread_market:
                spread_outcomes = spread_market['outcomes']
                spreads_df = pd.DataFrame(spread_outcomes)
                fig_spreads = px.bar(spreads_df, x='name', y='point', color='price', title='Point Spreads', 
                                     labels={'name': 'Team', 'point': 'Spread', 'price': 'Price'})
                st.plotly_chart(fig_spreads)
