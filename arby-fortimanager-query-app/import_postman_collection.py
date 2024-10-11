from postman import PostmanCollection
import requests

# Load your Postman collection JSON file
postman_collection_file = 'path_to_your_postman_collection.json'

# Initialize the collection
collection = PostmanCollection(postman_collection_file)

# Iterate over requests in the collection
for item in collection.items:
    # Assuming this is a simple GET request example
    if item.method == 'GET':
        url = item.url
        headers = {h['key']: h['value'] for h in item.headers}

        response = requests.get(url, headers=headers)
        print(f"Response from {url}: {response.status_code}")
        print(response.json())
