import streamlit as st
import pandas as pd
from kafka import KafkaConsumer
import json
import re

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'dog_breed',
    bootstrap_servers=['broker:39092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Streamlit UI
st.title('Breed Data Filter')

# Streamlit interactive filters
min_life = st.slider("Minimum Life Expectancy (years)", 0, 30, 12)
max_life = st.slider("Maximum Life Expectancy (years)", 0, 30, 16)
min_weight = st.slider("Minimum Weight (kg)", 0, 100, 20)
max_weight = st.slider("Maximum Weight (kg)", 0, 100, 40)

# Function to sanitize text
def sanitize_text(text):
    """Sanitize text by removing non-printable characters."""
    if text is None:
        return None
    return re.sub(r'[^\x20-\x7E]', '', text)

# Initialize a list to store breed data
breed_data_list = []

# Fetch and filter breed data from Kafka
for msg in consumer:
    try:
        event_data = msg.value
        breed_data = {
            'Type': event_data.get('type'),
            'Name': sanitize_text(event_data['attributes'].get('name')),
            'Description': sanitize_text(event_data['attributes'].get('description')),
            'Life Min': event_data['attributes'].get('life', {}).get('min'),
            'Life Max': event_data['attributes'].get('life', {}).get('max'),
            'Male Weight Min': event_data['attributes'].get('male_weight', {}).get('min'),
            'Male Weight Max': event_data['attributes'].get('male_weight', {}).get('max'),
            'Female Weight Min': event_data['attributes'].get('female_weight', {}).get('min'),
            'Female Weight Max': event_data['attributes'].get('female_weight', {}).get('max'),
            'Hypoallergenic': event_data['attributes'].get('hypoallergenic', False),
            'Group ID': event_data['relationships']['group']['data'].get('id')
        }

        # Append breed data to the list
        breed_data_list.append(breed_data)

        # Convert to DataFrame
        df = pd.DataFrame(breed_data_list)
        
        # Apply filters
        filtered_df = df[
            (df['Life Min'] >= min_life) & (df['Life Max'] <= max_life) &
            (df['Male Weight Min'] >= min_weight) & (df['Male Weight Max'] <= max_weight) &
            (df['Female Weight Min'] >= min_weight) & (df['Female Weight Max'] <= max_weight)
        ]
        
        # Display filtered DataFrame as table
        st.write("### Filtered Breeds")
        st.dataframe(filtered_df)

        # Display descriptions
        if not filtered_df.empty:
            st.subheader('Breed Descriptions')
            for _, row in filtered_df.iterrows():
                st.write(f"**Name**: {row['Name']}")
                st.write(f"**Description**: {row['Description']}")
                st.write(f"**Life Expectancy**: {row['Life Min']} - {row['Life Max']} years")
                st.write(f"**Male Weight**: {row['Male Weight Min']} - {row['Male Weight Max']} kg")
                st.write(f"**Female Weight**: {row['Female Weight Min']} - {row['Female Weight Max']} kg")
                st.write("---")

        # Break after the first fetch for demo purposes
        break

    except Exception as e:
        st.error(f"Error processing message: {e}")
        break
