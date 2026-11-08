"""
FacebookAutomation - Core engine tự động comment Facebook
Sử dụng undetected-chromedriver, WebDriverWait, ActionChains
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    WebDriverException,
)
import time
import random
import re
import os
import urllib.parse

from core.database_manager import DatabaseManager
from core.utils import random_delay, parse_cookies, get_random_image

# ======================== XPATH CONSTANTS ========================
# Bước 2: Ô tìm kiếm "Bài viết mới nhất" trên trang search
XPATH_LATEST_FILTER = (
    '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]'
    '/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div[1]/div[2]/div[1]'
    '/div/div[2]/div/input'
)

# Bước 4: Nút "Bình luận" trên bài viết
XPATH_COMMENT_BTN = (
    '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]'
    '/div/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div'
    '/div/div/div/div[13]/div/div/div[4]/div/div/div[1]/div/div/div/div[2]'
    '/div/div[1]/div[1]'
)

# Bước 4: Ô nhập comment (contenteditable <p>)
XPATH_COMMENT_INPUT = (
    '/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div'
    '/div/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div[2]'
    '/div/div/div/div[2]/form/div/div[1]/div/div/div[1]/div/div[1]/p'
)

# Bước 4: Nút thêm ảnh vào comment
XPATH_IMAGE_BTN = (
    '/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div'
    '/div/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div[2]'
    '/div/div/div/div[2]/form/div/div[2]/div/div[1]/div/ul/li[3]/span/div/div'
)

# Bước 4: Nút gửi comment
XPATH_SUBMIT_BTN = (
    '/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div'
    '/div/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div[2]'
    '/div/div/div/div[2]/form/div/div[2]/div/div[2]/div/div/div/span/div/div'
)

# Bước 5: Click ra ngoài để đóng popup comment
XPATH_CLOSE_POPUP = (
    '/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div'
    '/div/div/div/div/div[1]/div/div[3]/div/div'
)


class FacebookAutomation:
    """Class tự động hóa comment Facebook."""

    FACEBOOK_URL = "https://www.facebook.com"

    def __init__(self, cookie_string, headless=True, log_callback=None):
        """Khởi tạo engine.
        
        Args:
            cookie_string: Cookie Facebook dạng chuỗi
            headless: Chạy ẩn trình duyệt
            log_callback: Hàm callback để ghi log (message, level)
        """
        self.cookie_string = cookie_string
        self.headless = headless
        self.log = log_callback or (lambda msg, lvl="INFO": print(f"[{lvl}] {msg}"))
        self.driver = None
        self.wait = None
        self.actions = None
        self.db = DatabaseManager()
        self.account_name = "N/A"

    # ======================== BROWSER SETUP ========================
    def start_browser(self):
        """Khởi tạo trình duyệt undetected-chromedriver."""
        try:
            options = uc.ChromeOptions()

            if self.headless:
                options.add_argument("--headless=new")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-infobars")
            options.add_argument("--lang=vi-VN")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")

            # Random user-agent
            agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            ]
            options.add_argument(f"--user-agent={random.choice(agents)}")

            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(3)
            self.wait = WebDriverWait(self.driver, 15)
            self.actions = ActionChains(self.driver)

            self.log("Đã khởi tạo trình duyệt thành công", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Lỗi khởi tạo trình duyệt: {e}", "ERROR")
            return False

    # ======================== BƯỚC 1: ĐĂNG NHẬP COOKIE ========================
    def login_with_cookie(self):
        """Đăng nhập Facebook bằng cookie.
        
        Returns:
            bool: True nếu đăng nhập thành công
        """
        try:
            self.log("Đang nạp cookie vào trình duyệt...", "INFO")

            # Truy cập Facebook để set domain
            self.driver.get(self.FACEBOOK_URL)
            self._wait_page_loaded()

            # Xóa cookie cũ
            self.driver.delete_all_cookies()

            # Parse cookie string
            cookies = parse_cookies(self.cookie_string)
            if not cookies:
                self.log("Cookie rỗng hoặc không hợp lệ!", "ERROR")
                return False

            self.log(f"Đã parse {len(cookies)} cookie", "INFO")

            # Nạp từng cookie
            for cookie in cookies:
                try:
                    self.driver.add_cookie({
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": ".facebook.com",
                        "path": "/",
                        "secure": True,
                    })
                except Exception:
                    continue

            # Reload để áp dụng cookie
            self.driver.get(self.FACEBOOK_URL)
            self._wait_page_loaded()

            # Đóng popup nếu có
            self._dismiss_popups()

            # Kiểm tra đăng nhập
            if self._is_logged_in():
                self._fetch_account_name()
                self.log(f"Đăng nhập thành công! Tài khoản: {self.account_name}", "SUCCESS")
                return True
            else:
                self.log("Đăng nhập thất bại! Cookie hết hạn hoặc không hợp lệ.", "ERROR")
                return False

        except Exception as e:
            self.log(f"Lỗi đăng nhập: {e}", "ERROR")
            return False

    def _is_logged_in(self):
        """Kiểm tra đã đăng nhập thành công chưa."""
        try:
            url = self.driver.current_url
            if "/login" in url or "/checkpoint" in url or "recover" in url:
                return False

            # Tìm thanh tìm kiếm (chỉ xuất hiện khi đã đăng nhập)
            search_selectors = [
                (By.CSS_SELECTOR, 'input[placeholder="Tìm kiếm trên Facebook"]'),
                (By.CSS_SELECTOR, 'input[placeholder="Search Facebook"]'),
                (By.CSS_SELECTOR, 'input[type="search"]'),
                (By.CSS_SELECTOR, '[aria-label="Tìm kiếm trên Facebook"]'),
                (By.CSS_SELECTOR, '[aria-label="Search Facebook"]'),
                (By.CSS_SELECTOR, '[role="search"]'),
            ]
            for by, sel in search_selectors:
                try:
                    elem = self.driver.find_element(by, sel)
                    if elem:
                        return True
                except NoSuchElementException:
                    continue

            # Kiểm tra cookie c_user (Facebook set khi đăng nhập)
            for c in self.driver.get_cookies():
                if c.get("name") == "c_user" and c.get("value"):
                    return True

            return False

        except Exception:
            return False

    def _fetch_account_name(self):
        """Lấy tên tài khoản đang đăng nhập."""
        try:
            # Thử lấy từ profile link
            selectors = [
                (By.CSS_SELECTOR, '[aria-label="Trang cá nhân của bạn"] span'),
                (By.CSS_SELECTOR, '[aria-label="Your profile"] span'),
                (By.XPATH, '//div[@role="navigation"]//a[contains(@href,"/profile")]//span'),
                (By.XPATH, '//a[contains(@href,"/me/")]//span'),
            ]
            for by, sel in selectors:
                try:
                    elem = self.driver.find_element(by, sel)
                    if elem and elem.text.strip():
                        self.account_name = elem.text.strip()
                        return
                except NoSuchElementException:
                    continue

            # Fallback: lấy từ c_user cookie
            for c in self.driver.get_cookies():
                if c.get("name") == "c_user":
                    self.account_name = f"UID:{c['value']}"
                    return

        except Exception:
            pass

    # ======================== BƯỚC 2: TÌM KIẾM TỪ KHÓA ========================
    def search_keyword(self, keyword):
        """Tìm kiếm từ khóa trên Facebook và lọc bài mới nhất.
        
        Args:
            keyword: Từ khóa tìm kiếm
            
        Returns:
            bool: True nếu tìm kiếm thành công
        """
        try:
            encoded = urllib.parse.quote(keyword)
            search_url = f"{self.FACEBOOK_URL}/search/posts/?q={encoded}"

            self.log(f"Đang tìm kiếm: \"{keyword}\"", "INFO")
            self.driver.get(search_url)
            self._wait_page_loaded()
            self._dismiss_popups()

            random_delay(2, 4)

            # Click bộ lọc "Bài viết mới nhất"
            self._click_latest_filter()

            random_delay(2, 4)
            return True

        except Exception as e:
            self.log(f"Lỗi tìm kiếm \"{keyword}\": {e}", "ERROR")
            return False

    def _click_latest_filter(self):
        """Click vào bộ lọc 'Bài viết mới nhất'."""
        try:
            # Thử XPath chính xác của user
            try:
                elem = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_LATEST_FILTER))
                )
                elem.click()
                self.log("Đã click bộ lọc 'Bài viết mới nhất' (XPath chính)", "SUCCESS")
                return
            except (TimeoutException, NoSuchElementException):
                pass

            # Fallback 1: Tìm tab "Bài viết" / "Posts"
            fallbacks = [
                (By.XPATH, '//a[contains(@href, "/search/posts")]'),
                (By.XPATH, '//span[text()="Bài viết"]'),
                (By.XPATH, '//span[text()="Posts"]'),
                (By.XPATH, '//div[@role="tab"]//span[contains(text(), "Bài viết")]'),
                (By.XPATH, '//input[@aria-label="Bài viết mới nhất"]'),
            ]
            for by, sel in fallbacks:
                try:
                    elem = self.wait.until(EC.element_to_be_clickable((by, sel)))
                    elem.click()
                    self.log("Đã click bộ lọc (fallback)", "SUCCESS")
                    return
                except (TimeoutException, NoSuchElementException):
                    continue

            self.log("Không tìm thấy bộ lọc, tiếp tục với kết quả hiện tại", "WARNING")

        except Exception as e:
            self.log(f"Lỗi click bộ lọc: {e}", "WARNING")

    # ======================== BƯỚC 3: LẤY LINK BÀI VIẾT ========================
    def get_post_links(self, max_posts=10):
        """Lấy danh sách link bài viết từ trang tìm kiếm.
        
        Args:
            max_posts: Số bài tối đa cần lấy
            
        Returns:
            list[str]: Danh sách URL bài viết
        """
        post_urls = []
        try:
            self.log("Đang quét link bài viết...", "INFO")

            # Cuộn xuống vài lần để load thêm bài
            for scroll in range(3):
                self.driver.execute_script("window.scrollBy(0, 800)")
                random_delay(1.5, 3)

            # Tìm tất cả thẻ <a> chứa link bài viết
            all_links = self.driver.find_elements(By.TAG_NAME, "a")

            seen = set()
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue

                    # Lọc link bài viết hợp lệ
                    if self._is_post_url(href):
                        # Chuẩn hóa URL
                        clean_url = self._clean_post_url(href)
                        if clean_url and clean_url not in seen:
                            seen.add(clean_url)
                            post_urls.append(clean_url)

                            if len(post_urls) >= max_posts:
                                break
                except StaleElementReferenceException:
                    continue

            self.log(f"Tìm thấy {len(post_urls)} link bài viết", "INFO")

        except Exception as e:
            self.log(f"Lỗi lấy link bài viết: {e}", "ERROR")

        return post_urls

    @staticmethod
    def _is_post_url(url):
        """Kiểm tra URL có phải link bài viết không."""
        if not url:
            return False
        patterns = [
            r'/posts/',
            r'story_fbid=',
            r'/permalink/',
            r'/photos/',
            r'/videos/',
            r'fbid=',
        ]
        return any(re.search(p, url) for p in patterns)

    @staticmethod
    def _clean_post_url(url):
        """Chuẩn hóa URL bài viết."""
        if not url:
            return None
        # Bỏ tracking params nhưng giữ story_fbid
        if "?" in url:
            base, params = url.split("?", 1)
            # Giữ lại story_fbid nếu có
            important = {}
            for p in params.split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    if k in ("story_fbid", "id", "fbid"):
                        important[k] = v
            if important:
                return base + "?" + "&".join(f"{k}={v}" for k, v in important.items())
            return base
        return url

    # ======================== BƯỚC 4: THỰC HIỆN COMMENT ========================
    def comment_on_post(self, post_url, comment_text, photo_dir=None, stop_event=None):
        """Comment vào một bài viết.
        
        Args:
            post_url: URL bài viết
            comment_text: Nội dung comment
            photo_dir: Thư mục chứa ảnh (optional)
            stop_event: Threading event để dừng
            
        Returns:
            bool: True nếu comment thành công
        """
        if stop_event and stop_event.is_set():
            return False

        try:
            # Kiểm tra đã comment chưa (chống trùng)
            if self.db.is_commented(post_url):
                self.log(f"⏭ Bỏ qua (đã comment): {post_url[:60]}...", "WARNING")
                return False

            self.log(f"Đang mở bài viết: {post_url[:60]}...", "INFO")

            # Truy cập bài viết
            self.driver.get(post_url)
            self._wait_page_loaded()
            self._dismiss_popups()
            random_delay(2, 4)

            # Click nút "Bình luận"
            if not self._click_comment_button():
                self.log("Lỗi: Không tìm thấy nút Bình luận, bỏ qua bài này", "ERROR")
                return False

            random_delay(2, 4)

            # Nhập nội dung comment
            if not self._type_comment(comment_text):
                self.log("Lỗi: Không thể nhập comment, bỏ qua bài này", "ERROR")
                return False

            random_delay(1, 3)

            # Thêm ảnh nếu có
            if photo_dir:
                image_path = get_random_image(photo_dir)
                if image_path:
                    self._attach_image(image_path)
                    random_delay(2, 4)

            # Nhấn nút Gửi
            if not self._click_submit():
                self.log("Lỗi: Không thể gửi comment, bỏ qua bài này", "ERROR")
                return False

            random_delay(2, 4)

            # Đóng popup comment
            self._close_comment_popup()

            # Lưu vào DB
            self.db.save_commented(
                url=post_url,
                keyword="",
                account=self.account_name,
                comment_text=comment_text
            )

            self.log(f"✅ Comment thành công: \"{comment_text[:40]}...\"", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Lỗi comment bài {post_url[:40]}...: {e}", "ERROR")
            return False

    def _click_comment_button(self):
        """Click nút 'Bình luận' trên bài viết."""
        try:
            # Thử XPath chính xác
            try:
                elem = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_COMMENT_BTN))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                random_delay(0.5, 1)
                elem.click()
                self.log("Đã click nút Bình luận (XPath chính)", "INFO")
                return True
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                pass

            # Fallback selectors
            fallbacks = [
                # Aria-label
                (By.CSS_SELECTOR, '[aria-label="Viết bình luận"]'),
                (By.CSS_SELECTOR, '[aria-label="Write a comment"]'),
                (By.CSS_SELECTOR, '[aria-label="Leave a comment"]'),
                (By.CSS_SELECTOR, '[aria-label="Bình luận"]'),
                (By.CSS_SELECTOR, '[aria-label="Comment"]'),
                # Text content
                (By.XPATH, '//span[text()="Bình luận"]'),
                (By.XPATH, '//span[text()="Comment"]'),
                # Placeholder trực tiếp (ô comment có sẵn trên bài)
                (By.CSS_SELECTOR, '[contenteditable="true"][role="textbox"]'),
                (By.CSS_SELECTOR, 'div[role="textbox"][aria-label*="comment" i]'),
                (By.CSS_SELECTOR, 'div[role="textbox"][aria-label*="bình luận" i]'),
                (By.CSS_SELECTOR, 'p[data-lexical-text="true"]'),
            ]
            for by, sel in fallbacks:
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, sel))
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", elem
                    )
                    random_delay(0.3, 0.8)
                    elem.click()
                    self.log("Đã click nút Bình luận (fallback)", "INFO")
                    return True
                except (TimeoutException, NoSuchElementException,
                        ElementClickInterceptedException):
                    continue

            return False

        except Exception as e:
            self.log(f"Lỗi click nút Bình luận: {e}", "ERROR")
            return False

    def _type_comment(self, text):
        """Nhập nội dung comment vào ô contenteditable.
        
        Dùng ActionChains vì đây là thẻ <p> contenteditable.
        
        Args:
            text: Nội dung comment
            
        Returns:
            bool: True nếu nhập thành công
        """
        try:
            comment_box = None

            # Thử XPath chính xác
            try:
                comment_box = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, XPATH_COMMENT_INPUT))
                )
            except (TimeoutException, NoSuchElementException):
                pass

            # Fallback selectors
            if not comment_box:
                fallbacks = [
                    (By.CSS_SELECTOR,
                     'form [contenteditable="true"][role="textbox"]'),
                    (By.CSS_SELECTOR,
                     'div[role="textbox"][aria-label*="comment" i]'),
                    (By.CSS_SELECTOR,
                     'div[role="textbox"][aria-label*="bình luận" i]'),
                    (By.CSS_SELECTOR,
                     'div[role="textbox"][aria-label*="Viết bình luận" i]'),
                    (By.CSS_SELECTOR,
                     'form div[contenteditable="true"]'),
                    (By.CSS_SELECTOR,
                     '[data-lexical-editor="true"]'),
                    (By.XPATH,
                     '//form//div[@contenteditable="true"]'),
                    (By.XPATH,
                     '//div[contains(@class,"notranslate")][@contenteditable="true"][@role="textbox"]'),
                ]
                for by, sel in fallbacks:
                    try:
                        comment_box = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((by, sel))
                        )
                        if comment_box:
                            break
                    except (TimeoutException, NoSuchElementException):
                        continue

            if not comment_box:
                return False

            # Click vào ô comment trước
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", comment_box
            )
            random_delay(0.3, 0.7)

            # Dùng ActionChains để click và nhập text
            self.actions.reset_actions()
            self.actions.click(comment_box).perform()
            random_delay(0.3, 0.7)

            # Gõ từng ký tự với delay ngẫu nhiên (giả lập người thật)
            for char in text:
                self.actions.reset_actions()
                self.actions.send_keys(char).perform()
                time.sleep(random.uniform(0.03, 0.12))

            self.log(f"Đã nhập comment: \"{text[:50]}...\"", "INFO")
            return True

        except Exception as e:
            self.log(f"Lỗi nhập comment: {e}", "ERROR")
            return False

    def _attach_image(self, image_path):
        """Đính kèm ảnh vào comment.
        
        Ưu tiên dùng input[type=file].send_keys().
        Fallback dùng pyautogui cho hộp thoại Windows.
        
        Args:
            image_path: Đường dẫn tuyệt đối tới file ảnh
        """
        try:
            abs_path = os.path.abspath(image_path)

            # Phương pháp 1: Tìm input[type="file"] ẩn và send_keys
            try:
                file_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, 'input[type="file"][accept*="image"]'
                )
                if not file_inputs:
                    file_inputs = self.driver.find_elements(
                        By.CSS_SELECTOR, 'input[type="file"]'
                    )
                if file_inputs:
                    # Dùng input cuối cùng (thường là của comment form)
                    file_inputs[-1].send_keys(abs_path)
                    self.log(f"Đã đính kèm ảnh (send_keys): {os.path.basename(image_path)}", "INFO")
                    random_delay(2, 4)
                    return
            except Exception:
                pass

            # Phương pháp 2: Click nút ảnh rồi dùng pyautogui
            try:
                # Click nút thêm ảnh
                img_btn = None
                try:
                    img_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, XPATH_IMAGE_BTN))
                    )
                except (TimeoutException, NoSuchElementException):
                    # Fallback: tìm nút camera/ảnh
                    fallbacks = [
                        (By.CSS_SELECTOR, '[aria-label="Đính kèm ảnh hoặc video"]'),
                        (By.CSS_SELECTOR, '[aria-label="Attach a photo or video"]'),
                        (By.CSS_SELECTOR, 'form li:nth-child(3) div[role="button"]'),
                    ]
                    for by, sel in fallbacks:
                        try:
                            img_btn = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((by, sel))
                            )
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                if img_btn:
                    img_btn.click()
                    random_delay(1.5, 3)

                    # Dùng pyautogui để xử lý hộp thoại chọn file Windows
                    try:
                        import pyautogui
                        pyautogui.sleep(1)
                        pyautogui.typewrite(abs_path, interval=0.02)
                        pyautogui.press('enter')
                        self.log(
                            f"Đã đính kèm ảnh (pyautogui): {os.path.basename(image_path)}",
                            "INFO"
                        )
                        random_delay(2, 4)
                        return
                    except ImportError:
                        self.log("pyautogui chưa cài, bỏ qua ảnh", "WARNING")

            except Exception as e:
                self.log(f"Không thể đính kèm ảnh: {e}", "WARNING")

        except Exception as e:
            self.log(f"Lỗi đính kèm ảnh: {e}", "WARNING")

    def _click_submit(self):
        """Click nút Gửi comment."""
        try:
            # Thử XPath chính xác
            try:
                elem = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_SUBMIT_BTN))
                )
                elem.click()
                self.log("Đã click nút Gửi (XPath chính)", "INFO")
                return True
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                pass

            # Fallback selectors
            fallbacks = [
                (By.CSS_SELECTOR, 'form div[aria-label="Bình luận"]'),
                (By.CSS_SELECTOR, 'form div[aria-label="Comment"]'),
                (By.CSS_SELECTOR, 'form [aria-label="Bình luận"][role="button"]'),
                (By.CSS_SELECTOR, 'form [aria-label="Comment"][role="button"]'),
                (By.XPATH, '//form//div[@aria-label="Bình luận" and @role="button"]'),
                (By.XPATH, '//form//div[@aria-label="Comment" and @role="button"]'),
                # Submit button type
                (By.CSS_SELECTOR, 'form button[type="submit"]'),
                (By.CSS_SELECTOR, 'form input[type="submit"]'),
            ]
            for by, sel in fallbacks:
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, sel))
                    )
                    elem.click()
                    self.log("Đã click nút Gửi (fallback)", "INFO")
                    return True
                except (TimeoutException, NoSuchElementException,
                        ElementClickInterceptedException):
                    continue

            # Fallback cuối: Enter
            try:
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.RETURN)
                self.log("Đã gửi comment (Enter key)", "INFO")
                return True
            except Exception:
                pass

            return False

        except Exception as e:
            self.log(f"Lỗi gửi comment: {e}", "ERROR")
            return False

    # ======================== BƯỚC 5: ĐÓNG POPUP & CUỘN ========================
    def _close_comment_popup(self):
        """Đóng popup/overlay comment sau khi gửi."""
        try:
            random_delay(1.5, 3)

            # Thử XPath chính xác
            try:
                elem = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_CLOSE_POPUP))
                )
                elem.click()
                self.log("Đã đóng popup comment (XPath chính)", "INFO")
                return
            except (TimeoutException, NoSuchElementException):
                pass

            # Fallback: Tìm nút Close/Đóng
            close_selectors = [
                (By.CSS_SELECTOR, '[aria-label="Đóng"]'),
                (By.CSS_SELECTOR, '[aria-label="Close"]'),
                (By.CSS_SELECTOR, 'div[role="dialog"] [aria-label="Đóng"]'),
                (By.CSS_SELECTOR, 'div[role="dialog"] [aria-label="Close"]'),
            ]
            for by, sel in close_selectors:
                try:
                    elem = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, sel))
                    )
                    elem.click()
                    self.log("Đã đóng popup (fallback)", "INFO")
                    return
                except (TimeoutException, NoSuchElementException):
                    continue

            # Fallback: Nhấn Escape
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass

        except Exception as e:
            self.log(f"Lỗi đóng popup: {e}", "WARNING")

    def scroll_down(self, pixels=800):
        """Cuộn trang xuống để load thêm bài viết.
        
        Args:
            pixels: Số pixel cuộn xuống
        """
        try:
            self.driver.execute_script(f"window.scrollBy(0, {pixels})")
            random_delay(1.5, 3)
        except Exception:
            pass

    # ======================== HELPER METHODS ========================
    def _dismiss_popups(self):
        """Tự động đóng các popup chặn (thông báo, đăng nhập, v.v.)."""
        try:
            popup_selectors = [
                # Nút "Đóng" / "Close"
                (By.CSS_SELECTOR, '[aria-label="Đóng"]'),
                (By.CSS_SELECTOR, '[aria-label="Close"]'),
                # Popup thông báo
                (By.CSS_SELECTOR, '[aria-label="Không phải bây giờ"]'),
                (By.CSS_SELECTOR, '[aria-label="Not Now"]'),
                (By.CSS_SELECTOR, '[aria-label="Bỏ qua"]'),
                (By.CSS_SELECTOR, '[aria-label="Dismiss"]'),
                (By.CSS_SELECTOR, '[aria-label="Block"]'),
                # Cookie consent
                (By.CSS_SELECTOR, '[data-cookiebanner="accept_button"]'),
                (By.XPATH, '//button[contains(text(), "Cho phép")]'),
                (By.XPATH, '//button[contains(text(), "Allow")]'),
                (By.XPATH, '//button[contains(text(), "Đồng ý")]'),
                # Popup login overlay
                (By.XPATH, '//div[@role="dialog"]//div[@aria-label="Đóng" or @aria-label="Close"]'),
            ]

            for by, sel in popup_selectors:
                try:
                    elems = self.driver.find_elements(by, sel)
                    for elem in elems:
                        if elem.is_displayed():
                            elem.click()
                            random_delay(0.3, 0.8)
                except Exception:
                    continue

        except Exception:
            pass

    def _wait_page_loaded(self, timeout=15):
        """Chờ trang load xong bằng WebDriverWait (không dùng time.sleep cố định)."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            self.log("Trang load quá lâu, tiếp tục...", "WARNING")

    def close(self):
        """Đóng trình duyệt."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.log("Đã đóng trình duyệt", "INFO")
        except Exception:
            pass

    def __del__(self):
        self.close()

    # ======================== WORKFLOW CHÍNH ========================
    def run_full_cycle(self, keywords, comments, photo_dir=None,
                       max_posts_per_keyword=5, delay_between_comments=30,
                       stop_event=None):
        """Chạy toàn bộ workflow: tìm kiếm → lọc → comment.
        
        Args:
            keywords: Danh sách từ khóa
            comments: Danh sách nội dung comment
            photo_dir: Thư mục ảnh (optional)
            max_posts_per_keyword: Số bài tối đa mỗi từ khóa
            delay_between_comments: Delay giữa các comment (giây)
            stop_event: Threading event để dừng
            
        Returns:
            int: Số bài đã comment thành công
        """
        total_commented = 0

        for keyword in keywords:
            if stop_event and stop_event.is_set():
                break

            self.log(f"\n{'='*40}", "INFO")
            self.log(f"🔍 Từ khóa: \"{keyword}\"", "INFO")
            self.log(f"{'='*40}", "INFO")

            # Bước 2: Tìm kiếm
            if not self.search_keyword(keyword):
                continue

            # Bước 3: Lấy link bài viết
            post_urls = self.get_post_links(max_posts=max_posts_per_keyword)

            if not post_urls:
                self.log(f"Không tìm thấy bài viết cho \"{keyword}\"", "WARNING")
                continue

            # Lọc bài chưa comment
            new_posts = [url for url in post_urls if not self.db.is_commented(url)]
            self.log(
                f"📊 {len(post_urls)} bài tìm thấy, {len(new_posts)} bài chưa comment",
                "INFO"
            )

            # Bước 4: Comment từng bài
            for idx, post_url in enumerate(new_posts):
                if stop_event and stop_event.is_set():
                    break

                # Random chọn nội dung comment
                comment_text = random.choice(comments)

                self.log(
                    f"\n--- Bài {idx + 1}/{len(new_posts)} ---",
                    "INFO"
                )

                success = self.comment_on_post(
                    post_url=post_url,
                    comment_text=comment_text,
                    photo_dir=photo_dir,
                    stop_event=stop_event
                )

                if success:
                    total_commented += 1

                # Delay giữa các comment
                if idx < len(new_posts) - 1 and not (stop_event and stop_event.is_set()):
                    actual_delay = delay_between_comments + random.randint(-5, 10)
                    actual_delay = max(5, actual_delay)
                    self.log(f"⏳ Chờ {actual_delay}s trước bài tiếp...", "WARNING")
                    for sec in range(actual_delay):
                        if stop_event and stop_event.is_set():
                            break
                        time.sleep(1)

            # Cuộn xuống sau mỗi keyword
            self.scroll_down(1000)

        return total_commented
