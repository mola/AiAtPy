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

def check_contradiction():
    global auth_token

    text = """ماده 14 - با توجه به نیازهای فوری و خاص وزارت فرهنگ در تأمین معلمان، این وزارتخانه مجاز است به جای برگزاری مسابقه و استخدام معلمان از میان فارغ‌التحصیلان و افراد واجد شرایط، به طور مستقیم و بدون هیچ‌گونه شرط و ضوابط خاصی، افرادی که حداقل یک دوره آموزشی مربوط به تدریس را گذرانده‌اند، از هر رشته و زمینه تحصیلی، به عنوان معلم استخدام نماید. این اقدام باید طی مدت حداکثر شش ماه بعد از تصویب این قانون صورت گیرد و بدون هیچ‌گونه محدودیتی از اعتبار محل‌های رسمی یا پیمانی پرداخت گردد. در این مورد، سوابق آموزشی و تحصیلی افراد نیز نادیده گرفته خواهد شد و ملاک استخدام، صرفاً گذراندن دوره آموزشی مذکور خواهد بود."""

    # Make a POST request to add the user with the authentication token
    response = requests.post(
        f"{API_URL}/analyze",
        json={"prompt": text, "category":"آموزش", },
        headers={"Authorization": f"Bearer {auth_token}"}
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
    response = requests.post(
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
