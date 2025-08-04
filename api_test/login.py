import requests
import getpass
from urllib.parse import urlparse

class AuthClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://127.0.0.1:8000/api"
        self.domain = urlparse(self.base_url).netloc.split(':')[0]

        # Configure session to handle cookies properly
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def login(self):
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")

        response = self.session.post(
            f"{self.base_url}/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            print("Login successful!")
            print("Received cookies:", self.session.cookies.get_dict())
            return True
        print(f"Login failed: {response.status_code} - {response.text}")
        return False

    def test_protected(self):
        response = self.session.get(f"{self.base_url}/protected")

        if response.status_code == 200:
            print("Protected test successful!")
            print("Response:", response.json())
            return True
        print(f"Test failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    client = AuthClient()

    if client.login():
        while True:
            print("\nMenu:")
            print("1. Test")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                client.test_protected()
            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
