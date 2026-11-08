"""
TOOL COMMENT BÀI VIẾT MỚI NHẤT THEO TỪ KHÓA TÌM KIẾM v4.0
─────────────────────────────────────────────────────────────
Giao diện: customtkinter (dark theme)
Engine:    undetected-chromedriver + Selenium
Database:  SQLite3 chống trùng
─────────────────────────────────────────────────────────────
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time
import random
import os
import sys

from core.facebook_automation import FacebookAutomation
from core.database_manager import DatabaseManager
from core.utils import (
    generate_machine_id, get_timestamp,
    ConfigManager, random_delay
)

# ==================== THEME ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Bảng màu theo screenshot
C = {
    "bg":           "#2B2D42",   # Nền chính (dark navy)
    "bg_card":      "#33354A",   # Nền card/frame
    "header_bg":    "#1B1D30",   # Nền header
    "section_bg":   "#3D4070",   # Nền thanh section header
    "section_text": "#FFFFFF",   # Text section header
    "text":         "#E0E0E0",   # Text chính
    "text_dim":     "#9E9EAF",   # Text phụ
    "text_accent":  "#8B8FFF",   # Text accent (ver 4.0)
    "input_bg":     "#FFFFFF",   # Nền ô nhập
    "input_fg":     "#1a1a1a",   # Text ô nhập
    "btn_start":    "#4CAF50",   # Nút START
    "btn_start_h":  "#388E3C",   # START hover
    "btn_stop":     "#9E9E9E",   # Nút STOP
    "btn_stop_h":   "#757575",
    "btn_stop_on":  "#F44336",   # STOP khi đang chạy
    "btn_stop_on_h":"#D32F2F",
    "btn_blue":     "#3D5AFE",   # Nút xanh (COPY, SAVE)
    "btn_blue_h":   "#304FFE",
    "border":       "#4A4C6A",
    "success":      "#4CAF50",
    "warning":      "#FF9800",
    "error":        "#F44336",
    "info":         "#42A5F5",
    "log_bg":       "#1E1F30",   # Nền log
}


class App(ctk.CTk):
    """Ứng dụng chính - Tool Comment Facebook."""

    def __init__(self):
        super().__init__()

        # ── Window ──
        self.title("Tool Comment Bài Viết Mới Nhất Theo Từ Khóa Tìm Kiếm")
        self.geometry("630x750")
        self.minsize(610, 700)
        self.configure(fg_color=C["bg"])

        # ── State ──
        self.is_running = False
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.worker_thread = None
        self.config_mgr = ConfigManager()
        self.machine_id = generate_machine_id()
        self.db = DatabaseManager()

        # ── Build UI ──
        self._build_header()
        self._build_tabs()
        self._build_footer()

        # ── Load config ──
        self._load_config()

        # ── Log consumer ──
        self._tick_log()

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                         HEADER                              ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["header_bg"], corner_radius=0, height=65)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr,
            text="TOOL COMMENT BÀI VIẾT MỚI NHẤT THEO TỪ KHÓA TÌM KIẾM",
            font=ctk.CTkFont("Arial", 15, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(15, 0))

        ctk.CTkLabel(
            hdr, text="ver 4.0",
            font=ctk.CTkFont("Arial", 11),
            text_color=C["text_accent"]
        ).pack(anchor="e", padx=18)

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                          TABS                               ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self, fg_color=C["bg_card"],
            segmented_button_fg_color=C["bg"],
            segmented_button_selected_color=C["section_bg"],
            segmented_button_selected_hover_color="#4D5090",
            segmented_button_unselected_color=C["bg"],
            segmented_button_unselected_hover_color=C["border"],
            corner_radius=8,
        )
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(4, 4))

        tab_main = self.tabs.add("🏠 Main")
        tab_cfg  = self.tabs.add("⚙ Cấu hình")

        self._build_tab_main(tab_main)
        self._build_tab_config(tab_cfg)

    # ─────────────── Tab Main ───────────────
    def _build_tab_main(self, parent):
        # Thống kê
        stat = ctk.CTkFrame(parent, fg_color="transparent")
        stat.pack(fill="x", padx=8, pady=(4, 2))

        self.lbl_stats = ctk.CTkLabel(
            stat,
            text=f"📊 Tổng đã comment: {self.db.get_count()} bài",
            font=ctk.CTkFont("Arial", 11),
            text_color=C["text_dim"]
        )
        self.lbl_stats.pack(anchor="w")

        # Label
        ctk.CTkLabel(
            parent, text="Lịch sử chạy tool:",
            font=ctk.CTkFont("Arial", 13, "bold"),
            text_color=C["text"]
        ).pack(anchor="w", padx=10, pady=(4, 2))

        # Log area (tk.Text cho scroll mượt)
        log_frame = ctk.CTkFrame(parent, fg_color=C["border"], corner_radius=6)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.log_text = tk.Text(
            log_frame, wrap="word",
            font=("Consolas", 10),
            bg=C["log_bg"], fg=C["text"],
            insertbackground=C["text"],
            relief="flat", bd=6,
            state="disabled", cursor="arrow",
            selectbackground="#4A4C6A",
        )
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.log_text.pack(fill="both", expand=True, padx=2, pady=2)

        # Tag màu
        self.log_text.tag_configure("INFO",    foreground=C["info"])
        self.log_text.tag_configure("SUCCESS", foreground=C["success"])
        self.log_text.tag_configure("WARNING", foreground=C["warning"])
        self.log_text.tag_configure("ERROR",   foreground=C["error"])
        self.log_text.tag_configure("TS",      foreground=C["text_dim"])

        # Buttons
        bf = ctk.CTkFrame(parent, fg_color="transparent")
        bf.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_start = ctk.CTkButton(
            bf, text="START",
            font=ctk.CTkFont("Arial", 14, "bold"),
            fg_color=C["btn_start"], hover_color=C["btn_start_h"],
            text_color="white", height=42, corner_radius=6,
            command=self._on_start,
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_stop = ctk.CTkButton(
            bf, text="STOP",
            font=ctk.CTkFont("Arial", 14, "bold"),
            fg_color=C["btn_stop"], hover_color=C["btn_stop_h"],
            text_color="white", height=42, corner_radius=6,
            command=self._on_stop, state="disabled",
        )
        self.btn_stop.pack(side="right", expand=True, fill="x", padx=(4, 0))

    # ─────────────── Tab Cấu hình ───────────────
    def _build_tab_config(self, parent):
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=C["border"],
        )
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # ── 🍪 Cookie ──
        self._section(scroll, "🍪 COOKIE FACEBOOK")
        ctk.CTkLabel(
            scroll, text="Nhập cookie Facebook (mỗi cookie 1 dòng):",
            font=ctk.CTkFont(size=11), text_color=C["text_dim"]
        ).pack(anchor="w", padx=10, pady=(0, 3))

        self.txt_cookies = ctk.CTkTextbox(
            scroll, height=90,
            font=ctk.CTkFont("Consolas", 10),
            fg_color=C["input_bg"], text_color=C["input_fg"],
            border_color=C["border"], border_width=1, corner_radius=6,
        )
        self.txt_cookies.pack(fill="x", padx=10, pady=(0, 8))

        # ── 🔍 Từ khóa ──
        self._section(scroll, "🔍 TỪ KHÓA TÌM KIẾM")
        ctk.CTkLabel(
            scroll, text="Nhập từ khóa tìm kiếm (mỗi từ khóa một dòng):",
            font=ctk.CTkFont(size=11), text_color=C["text_dim"]
        ).pack(anchor="w", padx=10, pady=(0, 3))

        self.txt_keywords = ctk.CTkTextbox(
            scroll, height=80,
            font=ctk.CTkFont("Consolas", 10),
            fg_color=C["input_bg"], text_color=C["input_fg"],
            border_color=C["border"], border_width=1, corner_radius=6,
        )
        self.txt_keywords.pack(fill="x", padx=10, pady=(0, 8))

        # ── 💬 Nội dung Comment ──
        self._section(scroll, "💬 NỘI DUNG COMMENT")
        ctk.CTkLabel(
            scroll, text="Nhập nội dung comment (mỗi dòng 1 comment, sẽ random chọn):",
            font=ctk.CTkFont(size=11), text_color=C["text_dim"]
        ).pack(anchor="w", padx=10, pady=(0, 3))

        self.txt_comments = ctk.CTkTextbox(
            scroll, height=80,
            font=ctk.CTkFont("Consolas", 10),
            fg_color=C["input_bg"], text_color=C["input_fg"],
            border_color=C["border"], border_width=1, corner_radius=6,
        )
        self.txt_comments.pack(fill="x", padx=10, pady=(0, 4))

        # Thư mục ảnh
        photo_row = ctk.CTkFrame(scroll, fg_color="transparent")
        photo_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(
            photo_row, text="📁 Thư mục ảnh (để trống nếu không dùng):",
            font=ctk.CTkFont(size=11), text_color=C["text_dim"]
        ).pack(anchor="w")

        pf = ctk.CTkFrame(photo_row, fg_color="transparent")
        pf.pack(fill="x", pady=(2, 0))

        self.entry_photo_dir = ctk.CTkEntry(
            pf, font=ctk.CTkFont("Consolas", 10),
            fg_color=C["input_bg"], text_color=C["input_fg"],
            border_color=C["border"], corner_radius=6,
        )
        self.entry_photo_dir.pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            pf, text="Chọn", width=60, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=C["btn_blue"], hover_color=C["btn_blue_h"],
            corner_radius=4,
            command=self._browse_photo_dir,
        ).pack(side="right")

        # ── ⏱ Cài đặt thời gian ──
        self._section(scroll, "⏱ CÀI ĐẶT THỜI GIAN")

        time_f = ctk.CTkFrame(scroll, fg_color="transparent")
        time_f.pack(fill="x", padx=10, pady=(0, 8))

        self.entry_filter_h    = self._setting_row(time_f, "Lọc bài viết trong (giờ):", "24")
        self.entry_delay       = self._setting_row(time_f, "Delay giữa các comment (giây):", "30")
        self.entry_loop_delay  = self._setting_row(time_f, "Delay giữa các vòng lặp (phút):", "5")
        self.entry_max_posts   = self._setting_row(time_f, "Số bài tối đa / từ khóa:", "10")

        # ── 🚀 Tùy chọn ──
        self._section(scroll, "🚀 TÙY CHỌN")

        opt_f = ctk.CTkFrame(scroll, fg_color="transparent")
        opt_f.pack(fill="x", padx=10, pady=(0, 8))

        self.var_headless = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_f, text="Chạy ẩn trình duyệt (Headless)",
            variable=self.var_headless,
            font=ctk.CTkFont(size=12), text_color=C["text"],
            fg_color=C["section_bg"], hover_color="#4D5090",
            corner_radius=4,
        ).pack(anchor="w", pady=2)

        self.var_loop = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_f, text="Chạy lặp lại 24/7",
            variable=self.var_loop,
            font=ctk.CTkFont(size=12), text_color=C["text"],
            fg_color=C["section_bg"], hover_color="#4D5090",
            corner_radius=4,
        ).pack(anchor="w", pady=2)

        # Nút lưu
        ctk.CTkButton(
            scroll, text="💾 LƯU CẤU HÌNH",
            font=ctk.CTkFont("Arial", 13, "bold"),
            fg_color=C["btn_blue"], hover_color=C["btn_blue_h"],
            text_color="white", height=38, corner_radius=6,
            command=self._save_config,
        ).pack(fill="x", padx=10, pady=(4, 10))

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                         FOOTER                              ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _build_footer(self):
        ft = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=0, height=70)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)

        row = ctk.CTkFrame(ft, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            row, text="MÃ MÁY:",
            font=ctk.CTkFont("Arial", 11, "bold"),
            text_color=C["text"]
        ).pack(side="left")

        self.entry_mid = ctk.CTkEntry(
            row, font=ctk.CTkFont("Consolas", 10),
            fg_color=C["log_bg"], text_color=C["text_dim"],
            border_color=C["border"], corner_radius=4,
        )
        self.entry_mid.pack(side="left", fill="x", expand=True, padx=6)
        self.entry_mid.insert(0, self.machine_id)
        self.entry_mid.configure(state="disabled")

        ctk.CTkButton(
            row, text="COPY", width=60, height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C["btn_blue"], hover_color=C["btn_blue_h"],
            corner_radius=4,
            command=self._copy_mid,
        ).pack(side="right")

        ctk.CTkLabel(
            ft,
            text="Tool Comment Bài Viết Mới Nhất Theo Từ Khóa Tìm Kiếm v4.0",
            font=ctk.CTkFont(size=10), text_color=C["text_dim"]
        ).pack(pady=(0, 6))

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                    UI HELPER METHODS                        ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _section(self, parent, text):
        """Tạo thanh section header màu xanh."""
        bar = ctk.CTkFrame(parent, fg_color=C["section_bg"], corner_radius=4, height=32)
        bar.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(
            bar, text=f"  {text}",
            font=ctk.CTkFont("Arial", 12, "bold"),
            text_color=C["section_text"]
        ).pack(anchor="w", padx=6, pady=5)

    def _setting_row(self, parent, label, default):
        """Tạo 1 dòng setting: label + entry."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row, text=label,
            font=ctk.CTkFont(size=12), text_color=C["text"]
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row, width=70,
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], text_color=C["input_fg"],
            border_color=C["border"], corner_radius=6,
            justify="center",
        )
        entry.pack(side="right")
        entry.insert(0, default)
        return entry

    def _browse_photo_dir(self):
        """Mở hộp thoại chọn thư mục ảnh."""
        d = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if d:
            self.entry_photo_dir.delete(0, "end")
            self.entry_photo_dir.insert(0, d)

    def _copy_mid(self):
        """Copy mã máy vào clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.machine_id)
        self._log("📋 Đã copy mã máy!", "SUCCESS")

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                    LOG SYSTEM                               ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _log(self, msg, level="INFO"):
        """Thread-safe log."""
        self.log_queue.put((get_timestamp(), msg, level))

    def _tick_log(self):
        """Xử lý log queue mỗi 100ms."""
        try:
            while not self.log_queue.empty():
                ts, msg, lvl = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", f"[{ts}] ", "TS")
                self.log_text.insert("end", f"{msg}\n", lvl)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass
        self.after(100, self._tick_log)

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                 CONFIG SAVE / LOAD                          ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _save_config(self):
        cfg = {
            "cookies":       self.txt_cookies.get("1.0", "end-1c").strip(),
            "keywords":      self.txt_keywords.get("1.0", "end-1c").strip(),
            "comments":      self.txt_comments.get("1.0", "end-1c").strip(),
            "photo_dir":     self.entry_photo_dir.get().strip(),
            "filter_hours":  self.entry_filter_h.get().strip(),
            "delay":         self.entry_delay.get().strip(),
            "loop_delay":    self.entry_loop_delay.get().strip(),
            "max_posts":     self.entry_max_posts.get().strip(),
            "headless":      self.var_headless.get(),
            "loop":          self.var_loop.get(),
        }
        self.config_mgr.save(cfg)
        self._log("✅ Đã lưu cấu hình!", "SUCCESS")

    def _load_config(self):
        cfg = self.config_mgr.load()
        if not cfg:
            return

        def _set_text(widget, val):
            if val:
                widget.insert("1.0", val)

        def _set_entry(widget, val):
            if val:
                widget.delete(0, "end")
                widget.insert(0, val)

        _set_text(self.txt_cookies,  cfg.get("cookies", ""))
        _set_text(self.txt_keywords, cfg.get("keywords", ""))
        _set_text(self.txt_comments, cfg.get("comments", ""))
        _set_entry(self.entry_photo_dir, cfg.get("photo_dir", ""))
        _set_entry(self.entry_filter_h,  cfg.get("filter_hours", "24"))
        _set_entry(self.entry_delay,     cfg.get("delay", "30"))
        _set_entry(self.entry_loop_delay,cfg.get("loop_delay", "5"))
        _set_entry(self.entry_max_posts, cfg.get("max_posts", "10"))

        if "headless" in cfg:
            self.var_headless.set(cfg["headless"])
        if "loop" in cfg:
            self.var_loop.set(cfg["loop"])

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                  START / STOP LOGIC                         ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _validate(self):
        """Kiểm tra đầu vào trước khi chạy."""
        cookies = self.txt_cookies.get("1.0", "end-1c").strip()
        keywords = self.txt_keywords.get("1.0", "end-1c").strip()
        comments = self.txt_comments.get("1.0", "end-1c").strip()

        if not cookies:
            messagebox.showwarning("Thiếu Cookie", "Vui lòng nhập ít nhất 1 cookie Facebook!")
            self.tabs.set("⚙ Cấu hình")
            return False
        if not keywords:
            messagebox.showwarning("Thiếu từ khóa", "Vui lòng nhập ít nhất 1 từ khóa tìm kiếm!")
            self.tabs.set("⚙ Cấu hình")
            return False
        if not comments:
            messagebox.showwarning("Thiếu comment", "Vui lòng nhập ít nhất 1 nội dung comment!")
            self.tabs.set("⚙ Cấu hình")
            return False

        try:
            int(self.entry_delay.get())
            int(self.entry_loop_delay.get())
            int(self.entry_max_posts.get())
        except ValueError:
            messagebox.showwarning("Lỗi", "Delay, vòng lặp, số bài phải là số nguyên!")
            self.tabs.set("⚙ Cấu hình")
            return False

        return True

    def _on_start(self):
        if self.is_running:
            return
        if not self._validate():
            return

        self._save_config()

        self.is_running = True
        self.stop_event.clear()

        self.btn_start.configure(state="disabled", fg_color=C["text_dim"])
        self.btn_stop.configure(
            state="normal",
            fg_color=C["btn_stop_on"],
            hover_color=C["btn_stop_on_h"]
        )

        self._log("═" * 50, "INFO")
        self._log("🚀 BẮT ĐẦU CHẠY TOOL", "SUCCESS")
        self._log("═" * 50, "INFO")

        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _on_stop(self):
        if not self.is_running:
            return

        self._log("⛔ Đang dừng tool...", "WARNING")
        self.stop_event.set()
        self.is_running = False

        self.btn_start.configure(state="normal", fg_color=C["btn_start"])
        self.btn_stop.configure(
            state="disabled",
            fg_color=C["btn_stop"],
            hover_color=C["btn_stop_h"]
        )
        self._log("🛑 Đã dừng tool.", "WARNING")

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                   WORKER THREAD                             ║
    # ╚══════════════════════════════════════════════════════════════╝
    def _worker(self):
        """Worker thread chính - chạy toàn bộ workflow."""
        try:
            # Parse inputs
            cookie_lines = [
                l.strip() for l in
                self.txt_cookies.get("1.0", "end-1c").strip().split("\n")
                if l.strip()
            ]
            keywords = [
                l.strip() for l in
                self.txt_keywords.get("1.0", "end-1c").strip().split("\n")
                if l.strip()
            ]
            comments = [
                l.strip() for l in
                self.txt_comments.get("1.0", "end-1c").strip().split("\n")
                if l.strip()
            ]
            photo_dir    = self.entry_photo_dir.get().strip() or None
            delay_sec    = int(self.entry_delay.get())
            loop_delay_m = int(self.entry_loop_delay.get())
            max_posts    = int(self.entry_max_posts.get())
            headless     = self.var_headless.get()
            do_loop      = self.var_loop.get()

            self._log(f"📋 Cookies: {len(cookie_lines)} | "
                      f"Từ khóa: {len(keywords)} | "
                      f"Comments: {len(comments)}", "INFO")
            self._log(f"⏱ Delay: {delay_sec}s | "
                      f"Max bài/keyword: {max_posts} | "
                      f"Lặp: {'Có' if do_loop else 'Không'}", "INFO")

            loop_count = 0

            while not self.stop_event.is_set():
                loop_count += 1
                self._log(f"\n{'═'*45}", "INFO")
                self._log(f"🔄 VÒNG LẶP #{loop_count}", "SUCCESS")
                self._log(f"{'═'*45}", "INFO")

                # Xử lý từng cookie (tài khoản)
                for idx, cookie in enumerate(cookie_lines):
                    if self.stop_event.is_set():
                        break

                    self._log(f"\n👤 ─── TÀI KHOẢN #{idx + 1}/{len(cookie_lines)} ───", "INFO")

                    fb = FacebookAutomation(
                        cookie_string=cookie,
                        headless=headless,
                        log_callback=self._log,
                    )

                    try:
                        # Bước 0: Khởi tạo browser
                        if not fb.start_browser():
                            continue

                        # Bước 1: Đăng nhập
                        if not fb.login_with_cookie():
                            fb.close()
                            continue

                        # Bước 2-5: Chạy full cycle
                        commented = fb.run_full_cycle(
                            keywords=keywords,
                            comments=comments,
                            photo_dir=photo_dir,
                            max_posts_per_keyword=max_posts,
                            delay_between_comments=delay_sec,
                            stop_event=self.stop_event,
                        )

                        self._log(
                            f"📊 Tài khoản #{idx+1} đã comment {commented} bài",
                            "SUCCESS"
                        )

                    except Exception as e:
                        self._log(f"❌ Lỗi tài khoản #{idx+1}: {e}", "ERROR")
                    finally:
                        fb.close()

                # Cập nhật stats
                self.after(0, self._update_stats)

                if not do_loop or self.stop_event.is_set():
                    break

                # Chờ trước vòng lặp tiếp theo
                self._log(
                    f"\n⏳ Chờ {loop_delay_m} phút trước vòng lặp tiếp...",
                    "WARNING"
                )
                for _ in range(loop_delay_m * 60):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

            self._log("\n🏁 Tool đã hoàn thành.", "SUCCESS")

        except Exception as e:
            self._log(f"❌ Lỗi nghiêm trọng: {e}", "ERROR")
        finally:
            self.after(0, self._reset_ui)

    def _update_stats(self):
        """Cập nhật thống kê trên UI."""
        count = self.db.get_count()
        self.lbl_stats.configure(text=f"📊 Tổng đã comment: {count} bài")

    def _reset_ui(self):
        """Reset UI về trạng thái ban đầu."""
        self.is_running = False
        self.btn_start.configure(state="normal", fg_color=C["btn_start"])
        self.btn_stop.configure(
            state="disabled",
            fg_color=C["btn_stop"],
            hover_color=C["btn_stop_h"]
        )
        self._update_stats()

    # ╔══════════════════════════════════════════════════════════════╗
    # ║                    WINDOW CLOSE                             ║
    # ╚══════════════════════════════════════════════════════════════╝
    def on_closing(self):
        if self.is_running:
            if messagebox.askokcancel(
                "Thoát", "Tool đang chạy. Dừng và thoát?"
            ):
                self.stop_event.set()
                self.is_running = False
                time.sleep(1)
                self.destroy()
        else:
            self.destroy()


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
