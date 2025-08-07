import requests
import getpass

# REST API base URL
API_URL = "http://127.0.0.1:8000/api"

# Create a session to maintain cookies
session = requests.Session()

# Function to authenticate user and get a token
def authenticate_user():
    global session
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    # Make a POST request to authenticate
    response = session.post(
        f"{API_URL}/login",  # Replace with your actual login endpoint
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        print("Login successful!")
        return True
    else:
        print("Invalid username or password.")
        return False

# Function to add a new OPC UA user
def get_law():
    global session
    law_id = input("Enter law ID: ")

    # Make a POST request to add the user with the authentication token
    response = session.get(
        f"{API_URL}/laws/{law_id}",
    )
    # cookies=auth_token

    if response.status_code == 200:
        print(response.json())
        print("successfully.")
    else:
        print(f"HTTP status: {response.status_code}")


def search_laws():
    global session
    search_text = input("Enter search text: ")
    limit = input("Enter limit (default 10): ") or "10"
    # topic_ids_input = input("Enter topic IDs as a comma-separated list: ")
    # topic_ids = [int(id.strip()) for id in topic_ids_input.split(",")]
    topic_ids = [1,2]
    # Make a POST request to search laws
    payload = {
        "q": search_text,
        "limit": limit,
        "topic_ids": topic_ids
    }

    response = session.post(
        f"{API_URL}/laws/search",
        json=payload  # Send the data as JSON in the body
    )

    if response.status_code == 200:
        laws = response.json()
        print("\nSearch Results:")
        for law in laws:
            print(f"ID: {law['id']}")
            print(f"Caption: {law['caption']}")
            print(f"Law No: {law['law_no']}")
            print(f"Approve Date: {law['approve_date']}")
            print("-" * 30)
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_law_section():
    global session
    id = input("Enter law id: ")

    # Make a GET request to search laws
    response = session.get(
        f"{API_URL}/laws/{id}/sections"
    )

    if response.status_code == 200:
        laws = response.json()
        print("\nSearch Results:")
        print(laws)
        # for law in laws:
        #     print(law)
        print("-" * 30)
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_law_section_by_no():
    global session
    id = input("Enter law id: ")
    ids = input("Enter section id: ")

    # Make a GET request to search laws
    response = session.get(
        f"{API_URL}/laws/{id}/sections/{ids}"
    )

    if response.status_code == 200:
        laws = response.json()
        print("\nSearch Results:")
        print(laws)
        # for law in laws:
        #     print(law)
        print("-" * 30)
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_section():
    global session
    ids = input("Enter section id: ")

    # Make a GET request to search laws
    response = session.get(
        f"{API_URL}/sections/{ids}"
    )

    if response.status_code == 200:
        laws = response.json()
        print("\nSearch Results:")
        print(laws)
        # for law in laws:
        #     print(law)
        print("-" * 30)
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Function to get the topics
def get_topics():
    global session

    # Make a GET request to get the topics tree
    response = session.get(f"{API_URL}/topics")

    if response.status_code == 200:
        topic_tree = response.json()
        print("\nTopic Tree:")
        print(topic_tree)  # You can format this as needed for better readability
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Main script
if __name__ == "__main__":
    if authenticate_user():
        while True:
            print("\nMenu:")
            print("1. Get Law")
            print("2. Search Laws")
            print("3. Law Section")
            print("4. Law Section No.")
            print("5. Section")
            print("6. Get Topics Tree")
            print("7. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                get_law()
            elif choice == "2":
                search_laws()
            elif choice == "3":
                get_law_section()
            elif choice == "4":
                get_law_section_by_no()
            elif choice == "5":
                get_section()
            elif choice == "6":
                get_topics()  # This will call the new function to get topics
            elif choice == "7":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    else:
        print("Authentication failed. Exiting...")