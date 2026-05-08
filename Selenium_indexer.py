import os
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

# ====== CẤU HÌNH (CONFIG) ======
CHROME_PROFILE_PATH = r"D:\chrome-selenium\index-ketsatsg"
PROFILE_NAME = "Default"
PROPERTY_URL = "https://search.google.com/search-console?resource_id=https://ketsatsaigon.vn/"
URL_FILE_NAME = "urls.txt"


# ===============================

def start_driver():
    """Khởi động Chrome"""
    print("🔌 Đang khởi động Driver...")
    try:
        options = Options()
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
        options.add_argument(f"--profile-directory={PROFILE_NAME}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        print(f"❌ Không thể mở Chrome: {e}")
        return None


def load_urls(filename):
    if not os.path.exists(filename): return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def inspect_and_request_index(driver, url, index_num):
    wait = WebDriverWait(driver, 30)
    print(f"\n==================================================")
    print(f"🚀 Xử lý: {url}")

    # 1. RESET TRANG (Bắt buộc để xóa các bảng lỗi cũ)
    try:
        driver.get(PROPERTY_URL)
        time.sleep(5)
    except:
        raise Exception("Mất kết nối khi tải trang")

    # 2. CLICK MỒI & NHẬP LIỆU
    try:
        try:
            search_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='search']")))
        except:
            search_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label]")

        driver.execute_script("arguments[0].click();", search_input)
        time.sleep(1)
        driver.execute_script("arguments[0].value = '';", search_input)
        driver.execute_script(f"arguments[0].value = '{url}';", search_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
        time.sleep(1)
        search_input.send_keys(Keys.ENTER)
        print("⌨️ Đã nhập link...")
    except Exception as e:
        print(f"⚠️ Lỗi nhập liệu: {e}")
        return

    # 3. CHỜ KẾT QUẢ KIỂM TRA
    print("⏳ Đang đợi Google tải dữ liệu...")
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'URL')]")))
        print("✅ Đã hiện kết quả kiểm tra URL!")
    except:
        print("❌ Timeout: Google không phản hồi.")
        return

    time.sleep(3)

    # 4. BẤM NÚT INDEX & CHỜ KẾT QUẢ
    if "quota" in driver.page_source.lower() or "hạn mức" in driver.page_source.lower():
        print("🚫 CẢNH BÁO: HẾT QUOTA NGAY TỪ ĐẦU!")
        return

    request_clicked = False

    # --- GIAI ĐOẠN 1: BẤM NÚT "YÊU CẦU" ---
    try:
        btns = driver.find_elements(By.XPATH,
                                    "//span[contains(text(),'Yêu cầu lập chỉ mục') or contains(text(),'Request indexing')]/ancestor::div[@role='button'] | //div[text()='Yêu cầu lập chỉ mục']")

        if len(btns) > 0:
            btn = btns[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(2)

            wait_btn = 0
            while "aria-disabled=\"true\"" in btn.get_attribute("outerHTML") and wait_btn < 10:
                print(f"⏳ Nút đang khóa... đợi {wait_btn + 1}s")
                time.sleep(1)
                wait_btn += 1
                btns = driver.find_elements(By.XPATH,
                                            "//span[contains(text(),'Yêu cầu lập chỉ mục') or contains(text(),'Request indexing')]/ancestor::div[@role='button'] | //div[text()='Yêu cầu lập chỉ mục']")
                if len(btns) > 0: btn = btns[0]

            driver.execute_script("arguments[0].click();", btn)
            print("👉 Đã bấm nút 'Yêu cầu'. Đang chờ kết quả...")
            request_clicked = True
        else:
            print(f"⚠️ Không thấy nút Index (Có thể đã index rồi).")
            return

    except Exception as e:
        print(f"⚠️ Lỗi bấm nút: {e}")
        return

    # --- GIAI ĐOẠN 2: CHỜ KẾT QUẢ (LOOP 5 PHÚT) ---
    if request_clicked:
        start_wait = time.time()
        max_wait_seconds = 300
        finished_successfully = False

        while time.time() - start_wait < max_wait_seconds:
            elapsed = int(time.time() - start_wait)
            if elapsed % 10 == 0:
                print(f"⏳ Đang đợi Google Test Live... ({elapsed}s)")

            try:
                page_src = driver.page_source

                # --- A. PHÁT HIỆN LỖI "RẤT TIẾC / SỰ CỐ" (ƯU TIÊN XỬ LÝ) ---
                if "Rất tiếc" in page_src or "xảy ra sự cố" in page_src or "Something went wrong" in page_src:
                    print(f"❌ [LỖI] Google Server Error ('Rất tiếc...').")

                    # Thử tìm và bấm nút loại bỏ (Dùng bộ chọn siêu rộng)
                    try:
                        # Tìm mọi thẻ span có chữ Loại bỏ/Dismiss/OK/Đóng
                        dismiss_btns = driver.find_elements(By.XPATH,
                                                            "//span[contains(text(),'Loại bỏ') or contains(text(),'Dismiss') or contains(text(),'OK') or contains(text(),'Đóng')]")
                        if len(dismiss_btns) > 0:
                            driver.execute_script("arguments[0].click();", dismiss_btns[0])
                            print("🧹 Đã bấm nút đóng bảng lỗi.")
                        else:
                            print("⚠️ Không tìm thấy nút đóng, sẽ bỏ qua để reset trang.")
                    except:
                        pass

                    # QUAN TRỌNG: NGẮT VÒNG LẶP NGAY LẬP TỨC
                    # Coi như xong link này (dù thất bại) để chuyển sang link kế tiếp
                    finished_successfully = True
                    break

                    # --- B. PHÁT HIỆN THÀNH CÔNG HOẶC TỪ CHỐI THƯỜNG ---
                dismiss_btns = driver.find_elements(By.XPATH,
                                                    "//span[contains(text(),'Loại bỏ') or contains(text(),'Got it') or contains(text(),'Dismiss')]/ancestor::div[@role='button']")

                if len(dismiss_btns) > 0:
                    if "Đã yêu cầu lập chỉ mục" in page_src or "Indexing requested" in page_src:
                        print(f"🎉 [THÀNH CÔNG] Đã gửi yêu cầu Index!")
                    elif "bị từ chối" in page_src or "rejected" in page_src:
                        print(f"❌ [THẤT BẠI] Google từ chối (Lỗi Web).")
                    else:
                        print("ℹ️ Đã hiện bảng thông báo kết quả.")

                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", dismiss_btns[0])
                    print("🧹 Đã bấm 'Loại bỏ' -> Xong link này.")
                    finished_successfully = True
                    break

                    # --- C. XỬ LÝ CÁC TRƯỜNG HỢP KHÁC ---
                # Popup xác nhận lần 2
                confirm_btns = driver.find_elements(By.XPATH,
                                                    "//div[@role='dialog']//span[contains(text(),'Yêu cầu')]/ancestor::div[@role='button']")
                if len(confirm_btns) > 0:
                    confirm_btns[0].click()
                    print("👆 Đã xác nhận popup phụ...")
                    time.sleep(2)

                # Check Quota
                if "quota" in page_src.lower() and "quota exceeded" in page_src.lower():
                    print("🚫 HẾT QUOTA (Dừng chương trình).")
                    driver.save_screenshot(f"quota_error_{index_num}.png")
                    exit()

            except Exception as e:
                pass

            time.sleep(1)

        if not finished_successfully:
            print("⚠️ Hết giờ chờ (5 phút). Chụp ảnh lỗi...")
            driver.save_screenshot(f"timeout_error_{index_num}.png")

    print("--------------------------------------------------")
    time.sleep(10)


# ====== MAIN ======
if __name__ == "__main__":
    urls = load_urls(URL_FILE_NAME)
    if not urls:
        print("⚠️ File urls.txt rỗng!")
        exit()

    driver = start_driver()

    for i, link in enumerate(urls):
        print(f"▶️ Link {i + 1}/{len(urls)}")

        if driver is None: driver = start_driver()
        try:
            _ = driver.title
        except:
            print("☠️ Chrome Crash! Restarting...")
            try:
                driver.quit()
            except:
                pass
            driver = start_driver()
            if driver is None: break

        try:
            inspect_and_request_index(driver, link, i + 1)
        except Exception as e:
            print(f"❌ Lỗi hệ thống: {e}")
            try:
                driver.quit()
            except:
                pass
            driver = None

    print("\n🏁 HOÀN TẤT!")
    if driver: driver.quit()
    input("Nhấn Enter để thoát...")