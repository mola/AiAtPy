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
            # The token is now stored in cookies, so the session will automatically send it
            return True
        print(f"Login failed: {response.status_code} - {response.text}")
        return False

    def test_protected(self):
        response = self.session.get(f"{self.base_url}/protected")

        if response.status_code == 200:
            print("Protected test successful!")
            print("Status:", response.status_code)
            print("Response JSON:", response.json())
            return True
        print(f"Test failed: {response.status_code} - {response.text}")
        return False

    def logout(self):
        response = self.session.post(f"{self.base_url}/logout")
        if response.status_code == 200:
            print("Logout successful!")
            return True
        print(f"Logout failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    client = AuthClient()

    if client.login():
        while True:
            print("\nMenu:")
            print("1. Test protected endpoint")
            print("2. Logout")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                client.test_protected()
            elif choice == "2":
                client.logout()
                break
            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")