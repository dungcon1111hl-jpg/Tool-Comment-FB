"""
DatabaseManager - SQLite3 chống trùng comment
Bảng: commented_posts (post_url TEXT PRIMARY KEY, commented_at DATETIME)
"""

import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    """Quản lý lịch sử comment bằng SQLite3 để chống trùng."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "history.db"
            )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """Tạo connection mới (thread-safe)."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Tạo bảng commented_posts nếu chưa có."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commented_posts (
                    post_url TEXT PRIMARY KEY,
                    keyword TEXT DEFAULT '',
                    account TEXT DEFAULT '',
                    comment_text TEXT DEFAULT '',
                    commented_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def is_commented(self, url):
        """Kiểm tra bài viết đã được comment chưa.
        
        Args:
            url: URL bài viết
            
        Returns:
            bool: True nếu đã comment
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM commented_posts WHERE post_url = ? LIMIT 1",
                (self._normalize_url(url),)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def save_commented(self, url, keyword="", account="", comment_text=""):
        """Lưu bài viết đã comment vào DB.
        
        Args:
            url: URL bài viết
            keyword: Từ khóa tìm kiếm
            account: Tên tài khoản
            comment_text: Nội dung đã comment
        """
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO commented_posts 
                   (post_url, keyword, account, comment_text, commented_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (self._normalize_url(url), keyword, account,
                 comment_text, datetime.now().isoformat())
            )
            conn.commit()
        finally:
            conn.close()

    def get_count(self):
        """Đếm tổng số bài đã comment."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM commented_posts")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_recent(self, limit=50):
        """Lấy danh sách bài comment gần đây.
        
        Args:
            limit: Số lượng tối đa
            
        Returns:
            list: Danh sách tuple (post_url, keyword, account, commented_at)
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """SELECT post_url, keyword, account, commented_at 
                   FROM commented_posts 
                   ORDER BY commented_at DESC LIMIT ?""",
                (limit,)
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def clear_all(self):
        """Xóa toàn bộ lịch sử."""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM commented_posts")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _normalize_url(url):
        """Chuẩn hóa URL để so sánh chính xác."""
        url = url.strip()
        # Bỏ tracking params
        if "?" in url:
            base = url.split("?")[0]
            return base
        return url
