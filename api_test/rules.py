import requests
import getpass
from urllib.parse import urlparse
import ssl
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RulesClient:
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
            'User-Agent': 'RulesClient/1.0'
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
            return True
        elif response:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
        else:
            print("✗ Login failed: No response received")
            
        return False

    def get_law(self):
        law_id = input("Enter law ID: ")

        response = self._make_request(
            self.session.get,
            f"/laws/{law_id}"
        )

        if response and response.status_code == 200:
            law_data = response.json()
            print("\nLaw Details:")
            print(f"ID: {law_data.get('id')}")
            print(f"Caption: {law_data.get('caption')}")
            print(f"Law No: {law_data.get('law_no')}")
            print(f"Approve Date: {law_data.get('approve_date')}")
            print("✓ Successfully retrieved law.")
            return law_data
        elif response:
            print(f"✗ Failed to get law: {response.status_code} - {response.text}")
        else:
            print("✗ Failed to get law: No response received")
            
        return None

    def search_laws(self):
        search_text = input("Enter search text: ")
        limit = input("Enter limit (default 10): ") or "10"
        
        # For simplicity, using fixed topic IDs as in original code
        topic_ids = [1, 2]
        
        payload = {
            "q": search_text,
            "limit": int(limit),
            "topic_ids": topic_ids
        }

        response = self._make_request(
            self.session.post,
            "/laws/search",
            json=payload
        )

        if response and response.status_code == 200:
            laws = response.json()
            print(f"\n✓ Found {len(laws)} laws:")
            for law in laws:
                print(f"\nID: {law.get('id')}")
                print(f"Caption: {law.get('caption')}")
                print(f"Law No: {law.get('law_no')}")
                print(f"Approve Date: {law.get('approve_date')}")
                print("-" * 30)
            return laws
        elif response:
            print(f"✗ Search failed: {response.status_code} - {response.text}")
        else:
            print("✗ Search failed: No response received")
            
        return None

    def get_law_sections(self):
        law_id = input("Enter law ID: ")

        response = self._make_request(
            self.session.get,
            f"/laws/{law_id}/sections"
        )

        if response and response.status_code == 200:
            sections = response.json()
            print(f"\n✓ Found {len(sections)} sections for law {law_id}:")
            for section in sections:
                print(f"\nSection ID: {section.get('id')}")
                print(f"Title: {section.get('title')}")
                print(f"Content: {section.get('content', '')[:100]}...")
                print("-" * 30)
            return sections
        elif response:
            print(f"✗ Failed to get sections: {response.status_code} - {response.text}")
        else:
            print("✗ Failed to get sections: No response received")
            
        return None

    def get_law_section_by_no(self):
        law_id = input("Enter law ID: ")
        section_id = input("Enter section ID: ")

        response = self._make_request(
            self.session.get,
            f"/laws/{law_id}/sections/{section_id}"
        )

        if response and response.status_code == 200:
            section = response.json()
            print("\n✓ Section Details:")
            print(f"ID: {section.get('id')}")
            print(f"Title: {section.get('title')}")
            print(f"Content: {section.get('content')}")
            return section
        elif response:
            print(f"✗ Failed to get section: {response.status_code} - {response.text}")
        else:
            print("✗ Failed to get section: No response received")
            
        return None

    def get_section(self):
        section_id = input("Enter section ID: ")

        response = self._make_request(
            self.session.get,
            f"/sections/{section_id}"
        )

        if response and response.status_code == 200:
            section = response.json()
            print("\n✓ Section Details:")
            print(f"ID: {section.get('id')}")
            print(f"Title: {section.get('title')}")
            print(f"Content: {section.get('content')}")
            return section
        elif response:
            print(f"✗ Failed to get section: {response.status_code} - {response.text}")
        else:
            print("✗ Failed to get section: No response received")
            
        return None

    def get_topics(self):
        response = self._make_request(
            self.session.get,
            "/topics"
        )

        if response and response.status_code == 200:
            topics = response.json()
            print("\n✓ Topic Tree:")
            self._print_topic_tree(topics, 0)
            return topics
        elif response:
            print(f"✗ Failed to get topics: {response.status_code} - {response.text}")
        else:
            print("✗ Failed to get topics: No response received")
            
        return None

    def _print_topic_tree(self, topics, level):
        """Recursively print topic tree with indentation"""
        indent = "  " * level
        for topic in topics:
            print(f"{indent}• {topic.get('name')} (ID: {topic.get('id')})")
            if topic.get('children'):
                self._print_topic_tree(topic['children'], level + 1)

    def get_session_info(self):
        """Display current session information"""
        print("\nSession Information:")
        print(f"Base URL: {self.base_url}")
        print(f"Cookies: {dict(self.session.cookies)}")
        print(f"Headers: {dict(self.session.headers)}")
        print(f"Timeout: {self.timeout} seconds")
        print(f"SSL Verification: {'Enabled' if self.session.verify else 'Disabled'}")

    def main_menu(self):
        """Main menu for the rules client"""
        while True:
            print("\n📚 Rules Client Menu:")
            print("1. Get Law")
            print("2. Search Laws")
            print("3. Get Law Sections")
            print("4. Get Law Section by Number")
            print("5. Get Section")
            print("6. Get Topics Tree")
            print("7. Show Session Info")
            print("8. Exit")
            
            try:
                choice = input("Choose an option: ").strip()
                
                if choice == "1":
                    self.get_law()
                elif choice == "2":
                    self.search_laws()
                elif choice == "3":
                    self.get_law_sections()
                elif choice == "4":
                    self.get_law_section_by_no()
                elif choice == "5":
                    self.get_section()
                elif choice == "6":
                    self.get_topics()
                elif choice == "7":
                    self.get_session_info()
                elif choice == "8":
                    print("Exiting...")
                    break
                else:
                    print("Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Create a custom SSL context that doesn't verify certificates
    ssl._create_default_https_context = ssl._create_unverified_context
    
    client = RulesClient()
    
    print("📚 Rules Client")
    print("=" * 40)
    print("Note: SSL verification is disabled for self-signed certificates")
    client.get_session_info()

    if client.login():
        client.main_menu()
    else:
        print("Authentication failed. Exiting...")