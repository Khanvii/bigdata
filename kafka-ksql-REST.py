import requests
url = 'http://ksqldb-server:8088/ksql'
headers = {
    'Accept' : 'application/vnd.ksql.v1+json',
    'Content-Type' : 'application/vnd.ksql.v1+json'
    }
body = {
  "ksql": "CREATE STREAM s3 AS SELECT * FROM s1 EMIT CHANGES;",
  "streamsProperties": {
    "ksql.streams.auto.offset.reset": "earliest"
  }
}
response = requests.post(
    url, 
    headers=headers,
    json=body
)

# Print the response
post_response_json = response.json()
print(post_response_json)
