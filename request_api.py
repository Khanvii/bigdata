import requests
import re

# Replace with the API URL you want to request data from
url = "https://api.trace.moe/search?cutBorders&url=https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg"

try:
    # Send a GET request to the API
    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    response.raise_for_status()

    # Parse the response as JSON
    data = response.json()

    # Convert the JSON data to a string
    data_str = str(data)
    
    # Define a regex pattern to match only the JSON content
    json_pattern = re.compile(r'(\{.*\})', re.DOTALL)
    
    # Use the regex pattern to find the JSON content in the response string
    json_match = json_pattern.search(data_str)
    
    if json_match:
        # Extract the matched JSON content
        clean_data = json_match.group(1)
        print(clean_data)
    else:
        print("No JSON content found in the response.")
        
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
except Exception as err:
    print(f"An error occurred: {err}")
