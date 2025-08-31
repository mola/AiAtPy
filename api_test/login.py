import requests
import getpass
from urllib.parse import urlparse
import ssl
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AuthClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://127.0.0.1:8000/api"
        self.domain = urlparse(self.base_url).netloc.split(':')[0]

        # Disable SSL verification for self-signed certificates
        self.session.verify = False
        
        # Configure session
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'AuthClient/1.0'
        })
        
        # Set timeout for all requests
        self.timeout = 30
        
        # Disable SSL warnings for this session
        self.session.trust_env = False

    def _make_request(self, method, endpoint, **kwargs):
        """Helper method for making requests with better error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
            
        try:
            # For GET requests, use requests.get directly to avoid session issues
            if method.__name__ == 'get' and endpoint == "/sample-function":
                response = requests.get(url, verify=False, timeout=self.timeout, **kwargs)
            else:
                response = method(url, **kwargs)
                
            response.raise_for_status()  # Raise exception for bad status codes
            return response
            
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("This is expected for self-signed certificates in development.")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: {e}")
            print("Make sure the server is running on https://127.0.0.1:8000")
            return None
        except requests.exceptions.Timeout as e:
            print(f"Timeout Error: {e}")
            print("The request took too long to complete.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            if hasattr(e, 'response'):
                return e.response  # Return response even for HTTP errors
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None

    def login(self):
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")

        print("Attempting login...")
        
        response = self._make_request(
            self.session.post,
            "/login",
            json={"username": username, "password": password}
        )

        if response and response.status_code == 200:
            print("✓ Login successful!")
            print(f"Status: {response.status_code}")
            
            # Check if token is in response
            data = response.json()
            if 'access_token' in data:
                print(f"Token received: {data['access_token'][:20]}...")
            
            # Check cookies
            cookies = self.session.cookies.get_dict()
            if cookies:
                print("Cookies set:", cookies)
            else:
                print("No cookies set in session")
                
            return True
            
        elif response:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
        else:
            print("✗ Login failed: No response received")
            
        return False

    def test_protected(self):
        print("Testing protected endpoint...")
        
        response = self._make_request(self.session.get, "/protected")
        
        if response and response.status_code == 200:
            print("✓ Protected test successful!")
            print(f"Status: {response.status_code}")
            print("Response:", response.json())
            return True
        elif response:
            print(f"✗ Protected test failed: {response.status_code} - {response.text}")
        else:
            print("✗ Protected test failed: No response received")
            
        return False

    def logout(self):
        print("Attempting logout...")
        
        response = self._make_request(self.session.post, "/logout")
        
        if response and response.status_code == 200:
            print("✓ Logout successful!")
            print(f"Status: {response.status_code}")
            
            # Clear session cookies
            self.session.cookies.clear()
            print("Session cookies cleared")
            return True
        elif response:
            print(f"✗ Logout failed: {response.status_code} - {response.text}")
        else:
            print("✗ Logout failed: No response received")
            
        return False

    def test_hello_endpoint(self):
        """Test the sample hello endpoint"""
        print("Testing hello endpoint...")
        
        # Use direct requests.get for hello endpoint to avoid session SSL issues
        try:
            response = requests.get(
                "https://127.0.0.1:8000/sample-function", 
                verify=False, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                print("✓ Hello endpoint test successful!")
                print(f"Status: {response.status_code}")
                print("Response:", response.json())
                return True
            else:
                print(f"✗ Hello endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Hello endpoint error: {e}")
            return False

    def get_session_info(self):
        """Display current session information"""
        print("\nSession Information:")
        print(f"Base URL: {self.base_url}")
        print(f"Cookies: {dict(self.session.cookies)}")
        print(f"Headers: {dict(self.session.headers)}")
        print(f"Timeout: {self.timeout} seconds")
        print(f"SSL Verification: {'Enabled' if self.session.verify else 'Disabled'}")

if __name__ == "__main__":
    # Create a custom SSL context that doesn't verify certificates
    ssl._create_default_https_context = ssl._create_unverified_context
    
    client = AuthClient()
    
    print("🔐 Secure Auth Client")
    print("=" * 40)
    print("Note: SSL verification is disabled for self-signed certificates")
    client.get_session_info()

    if client.login():
        while True:
            print("\nMenu:")
            print("1. Test protected endpoint")
            print("2. Test hello endpoint")
            print("3. Show session info")
            print("4. Logout")
            print("5. Exit")
            
            try:
                choice = input("Choose an option: ").strip()
                
                if choice == "1":
                    client.test_protected()
                elif choice == "2":
                    client.test_hello_endpoint()
                elif choice == "3":
                    client.get_session_info()
                elif choice == "4":
                    if client.logout():
                        break
                elif choice == "5":
                    print("Exiting...")
                    break
                else:
                    print("Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")