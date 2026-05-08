import os
import time
import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ====== CẤU HÌNH ======
KEY_FILE = "service_account.json"
URL_FILE = "urls.txt"
MAX_CONSECUTIVE_ERRORS = 5  # Số lần lỗi liên tiếp tối đa cho phép trước khi dừng
DAILY_LIMIT = 200  # Giới hạn cứng 200 link/ngày


# ======================

def get_service():
    if not os.path.exists(KEY_FILE):
        print(f"❌ Lỗi: Không tìm thấy file {KEY_FILE}")
        return None
    scopes = ["https://www.googleapis.com/auth/indexing"]
    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
        service = build("indexing", "v3", credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Lỗi xác thực: {e}")
        return None


def publish_url(service, url):
    """
    Trả về 3 trạng thái:
    - "OK": Thành công
    - "QUOTA": Hết hạn mức
    - "RATE": Quá nhanh (cần nghỉ)
    - "ERROR": Lỗi khác
    """
    endpoint = service.urlNotifications()
    body = {
        "url": url,
        "type": "URL_UPDATED"
    }
    try:
        endpoint.publish(body=body).execute()
        print(f"✅ [ĐÃ GỬI] {url}")
        return "OK"
    except HttpError as e:
        try:
            error_content = json.loads(e.content.decode())
            reason = error_content['error']['message']
        except:
            reason = str(e)

        status = e.resp.status

        if status == 403:
            print(f"⛔ [403] Bot chưa có quyền Owner.")
            return "ERROR"
        elif status == 429:
            # Phân biệt lỗi Quá nhanh (Rate limit) và Hết hạn mức (Quota)
            if "Quota" in reason or "quota" in reason:
                print(f"🚫 [HẾT QUOTA] Google báo: {reason}")
                return "QUOTA"
            else:
                print(f"⏳ [429] Quá nhanh...")
                return "RATE"
        else:
            print(f"❌ [LỖI {status}] {reason}")
            return "ERROR"
    except Exception as e:
        print(f"❌ [LỖI LẠ] {e}")
        return "ERROR"


def load_urls(filename):
    if not os.path.exists(filename): return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


if __name__ == "__main__":
    print("🚀 GOOGLE INDEXING API - V3 (AUTO STOP)")
    print("👉 Bấm 'Ctrl + C' để dừng thủ công bất cứ lúc nào.")
    print("-------------------------------------------------------")

    service = get_service()

    if service:
        urls = load_urls(URL_FILE)
        if urls:
            print(f"📂 Tìm thấy {len(urls)} link.")

            success_count = 0
            fail_count = 0
            consecutive_429 = 0  # Đếm số lần bị chặn liên tiếp

            try:
                for i, link in enumerate(urls):
                    # 1. Kiểm tra giới hạn ngày
                    if success_count >= DAILY_LIMIT:
                        print(f"\n🛑 ĐÃ ĐẠT GIỚI HẠN {DAILY_LIMIT} LINK/NGÀY. TỰ ĐỘNG DỪNG.")
                        break

                    print(f"▶️ {i + 1}/{len(urls)}: ", end="")

                    status = publish_url(service, link)

                    if status == "OK":
                        success_count += 1
                        consecutive_429 = 0  # Reset bộ đếm lỗi
                        time.sleep(1)  # Nghỉ 1s

                    elif status == "QUOTA":
                        print("\n🚫 PHÁT HIỆN HẾT QUOTA CỦA GOOGLE. DỪNG CHƯƠNG TRÌNH.")
                        fail_count += 1
                        break  # Thoát vòng lặp ngay lập tức

                    elif status == "RATE":
                        fail_count += 1
                        consecutive_429 += 1
                        time.sleep(2)  # Nghỉ lâu hơn xíu

                        # Nếu bị chặn 5 lần liên tiếp -> Nghi là hết Quota nhưng Google báo sai
                        if consecutive_429 >= MAX_CONSECUTIVE_ERRORS:
                            print(
                                f"\n🛑 BỊ CHẶN LIÊN TỤC {MAX_CONSECUTIVE_ERRORS} LẦN. TỰ ĐỘNG DỪNG ĐỂ BẢO VỆ TÀI KHOẢN.")
                            break
                    else:
                        fail_count += 1
                        consecutive_429 = 0
                        time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n🛑 NGƯỜI DÙNG BẤM DỪNG (Ctrl + C)!")
                print("Đang tổng kết dữ liệu...")

            print("-------------------------------------------------------")
            print(f"🏁 TỔNG KẾT:")
            print(f"✅ Đã gửi thành công: {success_count}")
            print(f"❌ Thất bại/Bỏ qua:   {fail_count}")
            print(f"📊 Tỉ lệ hoàn thành:  {i + 1}/{len(urls)} link trong danh sách.")

    input("\nNhấn Enter để thoát...")