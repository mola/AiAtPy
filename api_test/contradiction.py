import requests
import getpass

# REST API base URL
API_URL = "http://127.0.0.1:8000/api"

# Create a session to maintain cookies
session = requests.Session()

# Function to authenticate user and get a token
def authenticate_user():
    # username = input("Enter username: ")
    username = "admin"
    # password = getpass.getpass("Enter password: ")
    password = "admin"

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

def check_contradiction():

    text = "test_prompt"
    # Make a POST request to add the user with the authentication token
    response = session.post(
        f"{API_URL}/analyze",
        json={"prompt": text, "check_law_id":86601}
    )
    # cookies=auth_token

    if response.status_code == 202:
        print("successfully.")
    else:
        print(f"HTTP status: {response.status_code}")

def check_contradiction_old_law():

    law_id = 84208
    law_section_no = 24
    check_law_id = 184557

    # Make a POST request to add the user with the authentication token
    response = session.post(
        f"{API_URL}/analyze_rules",
        json={"law_id":law_id,"section_no":law_section_no, "check_law_id":check_law_id}
    )
    # cookies=auth_token

    if response.status_code == 202:
        print("successfully.")
    else:
        print(f"HTTP status: {response.status_code}")


def get_task_status(task_id, since_timestamp=None):
    """
    Get task status and results, optionally filtered by timestamp
    
    Args:
        task_id (int): ID of the task to check
        since_timestamp (int, optional): Only return results newer than this timestamp
    
    Returns:
        dict: Task data including status and results, or None if error occurs
    """
    params = {}
    if since_timestamp is not None:
        params['since'] = since_timestamp
    
    response = session.get(
        f"{API_URL}/task/{task_id}",
        params=params
    )

    if response.status_code == 200:
        task_data = response.json()
        print(f"\nTask Status:")
        print(f"ID: {task_data['task_id']}")
        print(f"Status: {task_data['status']}")
        print(f"Created At: {task_data['created_at']}")
        
        # Print results summary
        results = task_data.get('results', [])
        print(f"\nFound {len(results)} comparison results:")
        for result in results:
            print(f"- Section {result['first_section_id']}: "
                  f"Contradiction={result['contradiction']}")
        
        print(f"\nLatest timestamp: {task_data.get('latest_timestamp')}")
        return task_data
        
    elif response.status_code == 404:
        print("Task not found")
    else:
        print(f"Error checking task status: HTTP status {response.status_code}")
    return None

# Main script
if __name__ == "__main__":
    if authenticate_user():
        while True:
            print("\nMenu:")
            print("1. check contradiction")
            print("2. check contradiction old law")
            print("3. get task status")
            print("4. get task status timestamp filter")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                check_contradiction()
            elif choice == "2":
                check_contradiction_old_law()
            elif choice == "3":
                task_id = input("Enter task ID to check: ")
                get_task_status(int(task_id))
            elif choice == "4":
                task_id = input("Enter task ID to check: ")
                timestamp = input("Enter timestamp to check: ")
                get_task_status(int(task_id) , timestamp)
            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    else:
        print("Authentication failed. Exiting...")
