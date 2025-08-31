import asyncio
import websockets
import json
import requests
import getpass
from urllib.parse import urlparse
import ssl

class WebSocketTester:
    def __init__(self):
        self.base_url = "https://127.0.0.1:8000/api"
        self.ws_url = "wss://127.0.0.1:8000/ws"
        self.session = requests.Session()
        self.token = None
        
        # Disable SSL verification for testing
        self.session.verify = False
        requests.packages.urllib3.disable_warnings()

        # Configure session
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def login(self):
        """Login and get authentication token"""
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")

        try:
            # Try JSON login endpoint first
            response = self.session.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                print("✓ Login successful!")
                print(f"✓ Token: {self.token[:20]}...")  # Show first 20 chars
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to server. Make sure FastAPI is running on port 8000")
            return False
        except Exception as e:
            print(f"✗ Login error: {str(e)}")
            return False

    def test_hello_endpoint(self):
        """Test the sample HTTP endpoint"""
        try:
            response = requests.get("https://127.0.0.1:8000/sample-function", verify=False)
            if response.status_code == 200:
                print("✓ Hello endpoint test successful!")
                print(f"✓ Response: {response.json()}")
                return True
            else:
                print(f"✗ Hello endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Hello endpoint error: {str(e)}")
            return False

    async def test_websocket_connection(self):
        """Test WebSocket connection with authentication"""
        if not self.token:
            print("✗ No token available. Please login first.")
            return False

        try:
            print(f"✓ Connecting to WebSocket with token: {self.token[:20]}...")
            
            # Disable SSL verification for testing (remove in production)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Connect to WebSocket with token as query parameter
            async with websockets.connect(f"{self.ws_url}?token={self.token}", ssl=ssl_context) as websocket:
                print("✓ WebSocket connection established!")
                
                # Test sending and receiving messages
                test_messages = [
                    "Hello WebSocket!",
                    "Test message 2",
                    "How are you?",
                    "ping"
                ]
                
                for i, message in enumerate(test_messages):
                    print(f"\n→ Sending: {message}")
                    await websocket.send(message)
                    
                    try:
                        # Wait for response with timeout
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"← Received: {response}")
                        
                        # Parse JSON if possible
                        try:
                            json_response = json.loads(response)
                            print(f"   JSON parsed: {json_response}")
                        except:
                            pass
                            
                    except asyncio.TimeoutError:
                        print("← Timeout waiting for response")
                    
                    await asyncio.sleep(1)  # Small delay between messages
                
                # Test receiving ping messages (server should send them periodically)
                print("\n✓ Waiting for server ping messages (timeout: 35 seconds)...")
                try:
                    for i in range(3):  # Try to get a few pings
                        response = await asyncio.wait_for(websocket.recv(), timeout=35.0)
                        print(f"← Server message: {response}")
                        if "ping" in response.lower():
                            print("✓ Received ping from server!")
                except asyncio.TimeoutError:
                    print("← No ping received within timeout")
                
                return True
                
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"✗ WebSocket connection failed: {e.status_code}")
            if e.status_code == 403:
                print("✗ Authentication failed - invalid token")
            return False
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"✗ WebSocket connection closed: {e}")
            return False
        except Exception as e:
            print(f"✗ WebSocket error: {str(e)}")
            return False

    async def interactive_websocket_chat(self):
        """Interactive WebSocket chat mode"""
        if not self.token:
            print("✗ No token available. Please login first.")
            return

        try:
            print(f"✓ Starting interactive WebSocket chat...")
            print("✓ Type 'exit' to quit, 'ping' to test, or any other message to send")
            print("✓ Press Ctrl+C to stop")
            
            # Disable SSL verification for testing (same as in test_websocket_connection)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE


            async with websockets.connect(f"{self.ws_url}?token={self.token}", ssl=ssl_context) as websocket:
                print("✓ Connected! Start typing messages:")
                
                # Start a task to receive messages
                receive_task = asyncio.create_task(self.receive_messages(websocket))
                
                # Send messages from user input
                try:
                    while True:
                        message = await asyncio.get_event_loop().run_in_executor(
                            None, input, "→ "
                        )
                        
                        if message.lower() == 'exit':
                            break
                            
                        await websocket.send(message)
                        
                except (KeyboardInterrupt, EOFError):
                    print("\n✓ Exiting...")
                finally:
                    receive_task.cancel()
                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        pass
                        
        except Exception as e:
            print(f"✗ Interactive chat error: {str(e)}")

    async def receive_messages(self, websocket):
        """Background task to receive messages"""
        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"\n← {message}\n→ ", end='', flush=True)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n✗ Receive error: {str(e)}")

    def test_protected_endpoint(self):
        """Test protected HTTP endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/protected")
            if response.status_code == 200:
                print("✓ Protected endpoint test successful!")
                print(f"✓ Response: {response.json()}")
                return True
            else:
                print(f"✗ Protected endpoint failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Protected endpoint error: {str(e)}")
            return False

async def main():
    tester = WebSocketTester()
    
    print("🔌 WebSocket and API Tester")
    print("=" * 40)
    
    # Test hello endpoint first (no auth required)
    print("\n1. Testing hello endpoint...")
    tester.test_hello_endpoint()
    
    # Login to get token
    print("\n2. Logging in...")
    if not tester.login():
        return
    
    # Test protected endpoint
    print("\n3. Testing protected endpoint...")
    tester.test_protected_endpoint()
    
    # Test WebSocket connection
    print("\n4. Testing WebSocket connection...")
    success = await tester.test_websocket_connection()
    
    if success:
        # Start interactive mode if WebSocket test was successful
        print("\n5. Starting interactive WebSocket chat...")
        start_chat = input("Start interactive chat? (y/n): ").lower().strip()
        if start_chat == 'y':
            await tester.interactive_websocket_chat()
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    # Install websockets package if not already installed
    try:
        import websockets
    except ImportError:
        print("Please install websockets package: pip install websockets")
        exit(1)
    
    asyncio.run(main())