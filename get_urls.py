import requests
import xml.etree.ElementTree as ET
import os

# ====== CẤU HÌNH ======
DOMAIN = "https://ketsatsaigon.vn"
OUTPUT_FILE = "urls.txt"  # File để chạy Index hôm nay
HISTORY_FILE = "history.txt"  # File lưu danh sách ĐÃ TỪNG CHẠY
BATCH_SIZE = 200  # Mỗi ngày chỉ lấy 200 link


# ======================

def get_xml_content(url):
    """Tải nội dung XML (Giả lập trình duyệt)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        print(f"⚠️ Lỗi kết nối: {e}")
        return None


def find_correct_sitemap(domain):
    """Tự động dò tìm link sitemap"""
    possible_urls = [
        f"{domain}/sitemap_index.xml",
        f"{domain}/sitemap.xml",
        f"{domain}/wp-sitemap.xml",
    ]
    print("🕵️ Đang dò tìm sitemap...")
    for url in possible_urls:
        content = get_xml_content(url)
        if content:
            print(f"✅ Đã tìm thấy: {url}")
            return url
    return None


def parse_sitemap(url, all_urls):
    """Đọc sitemap đệ quy"""
    if not url: return
    content = get_xml_content(url)
    if not content: return

    try:
        root = ET.fromstring(content)
        if '}' in root.tag:
            ns_url = root.tag.split('}')[0] + '}'
        else:
            ns_url = ''

        # 1. Tìm sitemap con
        sub_sitemaps = root.findall(f'{ns_url}sitemap')
        if sub_sitemaps:
            for sm in sub_sitemaps:
                loc = sm.find(f'{ns_url}loc').text
                parse_sitemap(loc, all_urls)
        else:
            # 2. Tìm link bài viết
            urls = root.findall(f'{ns_url}url')
            for u in urls:
                loc_node = u.find(f'{ns_url}loc')
                if loc_node is not None:
                    link = loc_node.text.strip()
                    if link not in all_urls:
                        all_urls.append(link)
    except Exception as e:
        pass


def load_history():
    """Đọc danh sách link đã từng chạy"""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def append_to_history(new_links):
    """Ghi thêm link mới vào lịch sử"""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        for link in new_links:
            f.write(link + "\n")


if __name__ == "__main__":
    print(f"🚀 TOOL LẤY URL THÔNG MINH (Batch: {BATCH_SIZE}/ngày)")
    print("------------------------------------------------")

    # 1. Tìm và quét Sitemap
    sitemap_url = find_correct_sitemap(DOMAIN)

    if sitemap_url:
        print(f"⏳ Đang quét toàn bộ website (Vui lòng đợi)...")
        all_online_urls = []
        parse_sitemap(sitemap_url, all_online_urls)
        print(f"✅ Tổng số link trên web: {len(all_online_urls)}")

        # 2. Đọc lịch sử
        history_urls = load_history()
        print(f"📚 Đã từng chạy trước đây: {len(history_urls)} link")

        # 3. Lọc ra link CHƯA chạy (Link mới - Lịch sử)
        pending_urls = [url for url in all_online_urls if url not in history_urls]
        print(f"🆕 Số link CẦN chạy tiếp: {len(pending_urls)}")

        if not pending_urls:
            print("\n🎉 CHÚC MỪNG! BẠN ĐÃ INDEX HẾT SẠCH LINK TRÊN WEB RỒI.")
            print("👉 Không còn link nào mới để chạy hôm nay.")
            # Xóa file urls.txt để tránh chạy nhầm
            if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)

        else:
            # 4. Cắt lô 200 link
            batch_urls = pending_urls[:BATCH_SIZE]

            # Ghi vào urls.txt
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for url in batch_urls:
                    f.write(url + "\n")

            # 5. Cập nhật ngay vào History (Để mai không lấy lại nữa)
            append_to_history(batch_urls)

            print("------------------------------------------------")
            print(f"💾 Đã xuất {len(batch_urls)} link mới vào file '{OUTPUT_FILE}'")
            print(f"📝 Đã đánh dấu {len(batch_urls)} link này vào '{HISTORY_FILE}'")
            print(f"👉 Còn lại {len(pending_urls) - len(batch_urls)} link cho các ngày sau.")
            print("\n🚀 BÂY GIỜ HÃY CHẠY: python api_indexer.py")

    else:
        print("\n❌ Không tìm thấy sitemap!")

    input("\nNhấn Enter để thoát...")