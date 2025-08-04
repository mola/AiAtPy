import requests
import getpass

# REST API base URL
API_URL = "http://127.0.0.1:8000/api"

# Create a session to maintain cookies
session = requests.Session()

# Function to authenticate user and get a token
def authenticate_user():
    global auth_token
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

def check_contradiction():
    global auth_token

    text = """ماده24ـ جهت تسريع در امر اكتشاف و بهره برداري از معادن ، دستگاههاي اجرائي و متوليان قانوني مربوط مكلفند حداكثر ظرف دو ماه نسبت به استعلام وزارت صنعت ، معدن و تجارت جهت صدور پروانه اكتشاف در موارد ذيل اعلام نظر نمايند : <br> الف ـ حريم قانوني راهها و راه آهن <br> ب ـ داخل شهر ها و حريم قانوني آنها <br> پ ـ حريم قانوني سدها و شبكه هاي توزيع آب و حوضچه هاي سدها و قنوات <br> ت ـ داخل جنگلها و مراتع <br> ث ـ حريم اماكن مقدسه و ابنيه تاريخي <br> ج ـ حريم پادگانها و محل استقرار نيروهاي مسلح <br> چ ـ مناطقي با عنوان پارك ملي ، آثار طبيعي ملي ، پناهگاه حيات وحش و حفاظت شده <br> ح ـ حوزه هاي داراي مواد پرتوزا بيش از حد مجاز <br> استعلام از دستگاههاي اجرائي ذي ربط ، توسط وزارت صنعت ، معدن و تجارت و فقط يك بار براي صدور پروانه اكتشاف انجام مي گيرد . پروانه اكتشاف توسط وزارت صنعت ، معدن و تجارت حداكثر سه ماه پس از استعلام صادر مي شود . اعلام نظر بايد براي كل محدوده مورد تقاضا صورت گيرد و عدم اعلام نظر در مهلت مقرر به منزله موافقت دستگاههاي مذكور تلقي مي شود ."""

    # Make a POST request to add the user with the authentication token
    response = session.post(
        f"{API_URL}/analyze",
        json={
            "prompt": text,
            "check_law_id":184557
        }
    )
    # cookies=auth_token

    if response.status_code == 202:
        print("successfully.")
    else:
        print(f"HTTP status: {response.status_code}")

def check_contradiction_old_law():
    global auth_token

    law_id = 84208
    law_section_no = 24
    check_law_id = 184557

    # Make a POST request to add the user with the authentication token
    response = session.post(
        f"{API_URL}/analyze_rules",
        json={"law_id":law_id,"section_no":law_section_no, "check_law_id":check_law_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # cookies=auth_token

    if response.status_code == 202:
        print("successfully.")
    else:
        print(f"HTTP status: {response.status_code}")

# Main script
if __name__ == "__main__":
    if authenticate_user():
        while True:
            print("\nMenu:")
            print("1. check contradiction")
            print("2. check contradiction old law")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                check_contradiction()
            if choice == "2":
                check_contradiction_old_law()
            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    else:
        print("Authentication failed. Exiting...")
