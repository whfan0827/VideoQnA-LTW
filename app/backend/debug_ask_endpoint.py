
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"  # Default Flask port
ASK_ENDPOINT = f"{BASE_URL}/ask"
INDEXES_ENDPOINT = f"{BASE_URL}/indexes"

# The question to ask
QUESTION = "What is this tutorial about?"

# The problematic index
PROBLEMATIC_INDEX = "vi-mechanicalreinstallationtutorial-index"

def get_other_index(exclude_index):
    """Gets another available index to test against."""
    try:
        response = requests.get(INDEXES_ENDPOINT)
        response.raise_for_status()
        indexes = response.json()
        print(f"Available indexes: {indexes}")
        
        for index in indexes:
            if index != exclude_index:
                return index
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching indexes: {e}")
        return None

def test_ask_endpoint(index_name, question):
    """Sends a request to the /ask endpoint and prints the response."""
    payload = {
        "question": question,
        "approach": "rrrv",
        "overrides": {
            "index": index_name
        }
    }
    
    print(f"--- Testing index: {index_name} ---")
    try:
        response = requests.post(ASK_ENDPOINT, json=payload)
        response.raise_for_status()
        
        print("Status Code:", response.status_code)
        response_json = response.json()
        print("Answer:", response_json.get("answer"))
        
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        if e.response:
            print("Response body:", e.response.text)
    print("-" * (len(index_name) + 18))
    print("\\n")

if __name__ == "__main__":
    # 1. Get another index to compare with
    other_index = get_other_index(PROBLEMATIC_INDEX)
    
    # 2. Test the problematic index
    test_ask_endpoint(PROBLEMATIC_INDEX, QUESTION)
    
    # 3. Test the other index
    if other_index:
        test_ask_endpoint(other_index, QUESTION)
    else:
        print("Could not find another index to test against. Only testing the problematic one.")

