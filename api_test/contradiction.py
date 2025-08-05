import requests
import getpass
import time
from pprint import pprint

# REST API base URL
API_URL = "http://127.0.0.1:8000/api"

# Default values for testing
DEFAULT_CUSTOM_PROMPT = """ماده24ـ جهت تسريع در امر اكتشاف و بهره برداري از معادن ، دستگاههاي اجرائي و متوليان قانوني مربوط مكلفند حداكثر ظرف دو ماه نسبت به استعلام وزارت صنعت ، معدن و تجارت جهت صدور پروانه اكتشاف در موارد ذيل اعلام نظر نمايند : <br> الف ـ حريم قانوني راهها و راه آهن <br> ب ـ داخل شهر ها و حريم قانوني آنها <br> پ ـ حريم قانوني سدها و شبكه هاي توزيع آب و حوضچه هاي سدها و قنوات <br> ت ـ داخل جنگلها و مراتع <br> ث ـ حريم اماكن مقدسه و ابنيه تاريخي <br> ج ـ حريم پادگانها و محل استقرار نيروهاي مسلح <br> چ ـ مناطقي با عنوان پارك ملي ، آثار طبيعي ملي ، پناهگاه حيات وحش و حفاظت شده <br> ح ـ حوزه هاي داراي مواد پرتوزا بيش از حد مجاز <br> استعلام از دستگاههاي اجرائي ذي ربط ، توسط وزارت صنعت ، معدن و تجارت و فقط يك بار براي صدور پروانه اكتشاف انجام مي گيرد . پروانه اكتشاف توسط وزارت صنعت ، معدن و تجارت حداكثر سه ماه پس از استعلام صادر مي شود . اعلام نظر بايد براي كل محدوده مورد تقاضا صورت گيرد و عدم اعلام نظر در مهلت مقرر به منزله موافقت دستگاههاي مذكور تلقي مي شود ."""
DEFAULT_LAW_ID = 84208
DEFAULT_SECTION_NO = 24
DEFAULT_CHECK_LAW_ID = 184557
DEFAULT_PROMPT_TITLE = "Custom Mining Law Analysis"

# Create a session to maintain cookies
session = requests.Session()

# Function to authenticate user and get a token
def authenticate_user():
    username = "admin"
    password = "admin"

    response = session.post(
        f"{API_URL}/login",
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        print("Login successful!")
        return True
    else:
        print("Invalid username or password.")
        return False

def analyze_custom_prompt(prompt_text, check_law_id, prompt_title=None, system_prompt=None):
    payload = {
        "prompt": prompt_text,
        "check_law_id": check_law_id
    }
    
    if prompt_title:
        payload["prompt_title"] = prompt_title
    if system_prompt:
        payload["system_prompt"] = system_prompt
    
    response = session.post(
        f"{API_URL}/analyze",
        json=payload
    )

    if response.status_code == 202:
        task_id = response.json().get("task_id")
        print(f"Analysis started successfully. Task ID: {task_id}")
        return task_id
    else:
        print(f"Error starting analysis. HTTP status: {response.status_code}")
        return None

def analyze_existing_law(law_id, section_no, check_law_id):
    response = session.post(
        f"{API_URL}/analyze_rules",
        json={
            "law_id": law_id,
            "section_no": section_no,
            "check_law_id": check_law_id
        }
    )

    if response.status_code == 202:
        task_id = response.json().get("task_id")
        print(f"Analysis started successfully. Task ID: {task_id}")
        return task_id
    else:
        print(f"Error starting analysis. HTTP status: {response.status_code}")
        return None

def get_task_status(task_id, since_timestamp=None):
    params = {}
    if since_timestamp is not None:
        params['since'] = since_timestamp
    
    response = session.get(
        f"{API_URL}/task/{task_id}",
        params=params
    )

    if response.status_code == 200:
        task_data = response.json()
        print(f"\nTask Status (ID: {task_data['task_id']}):")
        print(f"Status: {task_data['status']}")
        print(f"Created At: {task_data['created_at']}")
        
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

def get_all_tasks():
    response = session.get(f"{API_URL}/tasks")
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"\nFound {len(tasks)} tasks:")
        for task in tasks:
            print(f"\nTask ID: {task['task_id']}")
            print(f"Type: {task['type']}")
            print(f"Title: {task['title']}")
            print(f"Status: {task['status']}")
            print(f"Created At: {task['created_at']}")
            print(f"Finished At: {task['finished_at']}")
            print(f"Check Law ID: {task['check_law_id']}")
            print(f"Compare All: {task['compare_all']}")
        return tasks
    else:
        print(f"Error getting tasks: HTTP status {response.status_code}")
        return None

def run_test_cases():
    print("\n=== Running All Test Cases with Default Values ===")
    
    # Test 1: Analyze custom prompt against specific law
    print("\nTest 1: Analyze custom prompt against specific law")
    task1_id = analyze_custom_prompt(
        prompt_text=DEFAULT_CUSTOM_PROMPT,
        check_law_id=DEFAULT_CHECK_LAW_ID,
        prompt_title=DEFAULT_PROMPT_TITLE
    )
    
    # Test 2: Analyze custom prompt against all laws
    print("\nTest 2: Analyze custom prompt against all laws")
    task2_id = analyze_custom_prompt(
        prompt_text=DEFAULT_CUSTOM_PROMPT,
        check_law_id="*",
        prompt_title=DEFAULT_PROMPT_TITLE + " (All Laws)"
    )
    
    # Test 3: Analyze existing law against specific law
    print("\nTest 3: Analyze existing law against specific law")
    task3_id = analyze_existing_law(
        law_id=DEFAULT_LAW_ID,
        section_no=DEFAULT_SECTION_NO,
        check_law_id=DEFAULT_CHECK_LAW_ID
    )
    
    # Test 4: Analyze existing law against all laws
    print("\nTest 4: Analyze existing law against all laws")
    task4_id = analyze_existing_law(
        law_id=DEFAULT_LAW_ID,
        section_no=DEFAULT_SECTION_NO,
        check_law_id="*"
    )
    
    # Wait a bit for tasks to process
    print("\nWaiting 5 seconds for tasks to start...")
    time.sleep(5)
    
    # Test 5: Get task status
    print("\nTest 5: Get task status")
    if task1_id:
        get_task_status(task1_id)
    
    # Test 6: Get all tasks
    print("\nTest 6: Get all tasks")
    all_tasks = get_all_tasks()
    
    # Test 7: Get task status with timestamp filter
    print("\nTest 7: Get task status with timestamp filter")
    if task1_id and all_tasks:
        timestamp = all_tasks[0]['created_at']
        get_task_status(task1_id, since_timestamp=timestamp)
    
    print("\n=== Test Cases Completed ===")

# Helper function to get input with default
def input_with_default(prompt, default_value):
    user_input = input(f"{prompt} [Default: {default_value}]: ")
    return user_input if user_input else default_value

# Main script
if __name__ == "__main__":
    if authenticate_user():
        while True:
            print("\nMenu:")
            print("1. Analyze custom prompt (specific law)")
            print("2. Analyze custom prompt (all laws)")
            print("3. Analyze existing law (specific law)")
            print("4. Analyze existing law (all laws)")
            print("5. Get task status")
            print("6. Get task status timestamp filter")
            print("7. Get all tasks")
            print("8. Run all test cases with defaults")
            print("9. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                prompt = input_with_default("Enter custom prompt text", DEFAULT_CUSTOM_PROMPT)
                law_id = input_with_default("Enter law ID to check against", str(DEFAULT_CHECK_LAW_ID))
                title = input_with_default("Enter prompt title (optional)", DEFAULT_PROMPT_TITLE)
                analyze_custom_prompt(prompt, law_id, title)
            elif choice == "2":
                prompt = input_with_default("Enter custom prompt text", DEFAULT_CUSTOM_PROMPT)
                title = input_with_default("Enter prompt title (optional)", DEFAULT_PROMPT_TITLE)
                analyze_custom_prompt(prompt, "*", title)
            elif choice == "3":
                law_id = input_with_default("Enter law ID to analyze", str(DEFAULT_LAW_ID))
                section_no = input_with_default("Enter section number", str(DEFAULT_SECTION_NO))
                check_law_id = input_with_default("Enter law ID to check against", str(DEFAULT_CHECK_LAW_ID))
                analyze_existing_law(law_id, section_no, check_law_id)
            elif choice == "4":
                law_id = input_with_default("Enter law ID to analyze", str(DEFAULT_LAW_ID))
                section_no = input_with_default("Enter section number", str(DEFAULT_SECTION_NO))
                analyze_existing_law(law_id, section_no, "*")
            elif choice == "5":
                task_id = input("Enter task ID to check: ")
                get_task_status(int(task_id))
            elif choice == "6":
                task_id = input("Enter task ID to check: ")
                timestamp = input("Enter timestamp to check: ")
                get_task_status(int(task_id),timestamp)
            elif choice == "7":
                get_all_tasks()
            elif choice == "8":
                run_test_cases()
            elif choice == "9":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    else:
        print("Authentication failed. Exiting...")