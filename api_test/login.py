import requests
import getpass

# REST API base URL
API_URL = "http://127.0.0.1:8000/api"

# Global variable to store the authentication token
auth_token = None

# Function to authenticate user and get a token
def authenticate_user():
    global auth_token
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    # Make a POST request to authenticate
    response = requests.post(
        f"{API_URL}/login",  # Replace with your actual login endpoint
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        print("Login successful!")
        # Extract the token from the response (adjust based on your API's response structure)
        auth_token = response.json().get("access_token")
        print(f"Auth token: {auth_token}")
        return True
    else:
        print("Invalid username or password.")
        return False

# Main script
if __name__ == "__main__":
    if authenticate_user():
        while True:
            print("\nMenu:")
            # print("1. Add OPC UA User")
            # print("2. List All OPC UA Users")
            # print("3. Get OPC UA User Details")
            # print("4. Edit OPC UA User")
            # print("5. Delete OPC UA User")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    else:
        print("Authentication failed. Exiting...")
