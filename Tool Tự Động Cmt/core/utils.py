"""
Utility functions - Hàm tiện ích dùng chung
"""

import hashlib
import platform
import random
import time
import json
import os
import re
from datetime import datetime


def generate_machine_id(prefix="COMMENTPOSTBYKEYWORDSNEW"):
    """Tạo mã máy duy nhất dựa trên thông tin phần cứng."""
    info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    hash_hex = hashlib.md5(info.encode()).hexdigest()[:20]
    return f"{prefix}_{hash_hex}"


def get_timestamp():
    """Lấy timestamp hiện tại dạng chuỗi."""
    return datetime.now().strftime("%H:%M:%S %d/%m/%Y")


def random_delay(min_sec=3, max_sec=7):
    """Delay ngẫu nhiên giữa min và max giây để giả lập người dùng thật.
    
    Args:
        min_sec: Số giây tối thiểu
        max_sec: Số giây tối đa
        
    Returns:
        float: Số giây đã delay
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def parse_cookies(cookie_string):
    """Parse cookie string thành list dict.
    
    Hỗ trợ format:
    - key=value; key2=value2 (Netscape)
    - JSON array [{"name": "...", "value": "..."}]
    
    Args:
        cookie_string: Chuỗi cookie
        
    Returns:
        list[dict]: Danh sách cookie {name, value}
    """
    cookies = []
    cookie_string = cookie_string.strip()

    if not cookie_string:
        return cookies

    # Thử JSON format
    if cookie_string.startswith("["):
        try:
            parsed = json.loads(cookie_string)
            for item in parsed:
                if "name" in item and "value" in item:
                    cookies.append({
                        "name": item["name"],
                        "value": str(item["value"])
                    })
            return cookies
        except json.JSONDecodeError:
            pass

    # Format key=value; key2=value2
    parts = re.split(r';\s*', cookie_string)
    for part in parts:
        part = part.strip()
        if '=' in part:
            idx = part.index('=')
            name = part[:idx].strip()
            value = part[idx + 1:].strip()
            if name:
                cookies.append({"name": name, "value": value})

    return cookies


def get_random_image(photo_dir):
    """Lấy random 1 ảnh từ thư mục photos.
    
    Args:
        photo_dir: Đường dẫn thư mục chứa ảnh
        
    Returns:
        str or None: Đường dẫn tuyệt đối tới file ảnh, hoặc None
    """
    if not photo_dir or not os.path.isdir(photo_dir):
        return None

    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    images = [
        os.path.join(photo_dir, f)
        for f in os.listdir(photo_dir)
        if os.path.splitext(f)[1].lower() in image_exts
    ]

    if not images:
        return None

    return random.choice(images)


class ConfigManager:
    """Quản lý lưu/load cấu hình JSON."""

    def __init__(self):
        self.config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )
        self.config_file = os.path.join(self.config_dir, "config.json")
        os.makedirs(self.config_dir, exist_ok=True)

    def save(self, config):
        """Lưu config ra file JSON."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Lỗi lưu config: {e}")
            return False

    def load(self):
        """Load config từ file JSON."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Lỗi load config: {e}")
        return {}
