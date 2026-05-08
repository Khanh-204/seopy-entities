from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# --- CẤU HÌNH Y HỆT MAIN.PY ---
# Bạn copy đúng đường dẫn mà bạn đang để trong Selenium_indexer.py sang đây
CHROME_PROFILE_PATH = r"D:\chrome-selenium\index-ketsatsg"
PROFILE_NAME = "Default"
PROPERTY_URL = "https://search.google.com/search-console?resource_id=https://ketsatsaigon.vn/"

options = Options()
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument(f"--profile-directory={PROFILE_NAME}")
options.add_argument("--disable-blink-features=AutomationControlled")

# Mở trình duyệt
driver = webdriver.Chrome(options=options)
driver.get(PROPERTY_URL)

# Treo máy ở đây để bạn làm việc
print("👉 TRÌNH DUYỆT ĐANG MỞ!")
print("1. Hãy đăng nhập Google (nếu chưa).")
print("2. Hãy bấm chọn đúng Property Két Sắt Sài Gòn.")
print("3. Đảm bảo nhìn thấy Dashboard có biểu đồ và ô tìm kiếm.")
print("👉 SAU KHI XONG HẾT thì quay lại đây nhấn Enter để lưu Profile.")

input("Nhấn Enter để thoát và lưu...")
driver.quit()