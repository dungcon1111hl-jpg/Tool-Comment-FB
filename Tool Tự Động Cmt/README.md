# 🚀 Tool Comment Bài Viết Mới Nhất Theo Từ Khóa Tìm Kiếm v4.0

Tool tự động tìm kiếm bài viết mới nhất trên Facebook theo từ khóa và comment tự động.

## 📋 Yêu cầu hệ thống

- **Python** 3.10+
- **Google Chrome** đã cài đặt trên máy
- **Windows** 10/11

## ⚡ Cài đặt

```bash
# 1. Clone hoặc download project
cd "e:\Tool Tự Động Cmt"

# 2. Cài đặt thư viện
pip install -r requirements.txt
```

## 🏃 Cách chạy

```bash
python main.py
```

## 📖 Hướng dẫn sử dụng

### Bước 1: Chuẩn bị Cookie Facebook
1. Đăng nhập Facebook trên trình duyệt
2. Nhấn **F12** → Tab **Application** → **Cookies** → `https://www.facebook.com`
3. Copy toàn bộ cookie (format: `key1=value1; key2=value2; ...`)
4. Mỗi tài khoản = 1 dòng cookie

### Bước 2: Cấu hình Tool
1. Mở tool → Tab **⚙ Cấu hình**
2. **🍪 Cookie**: Dán cookie (mỗi dòng 1 tài khoản)
3. **🔍 Từ khóa**: Nhập từ khóa tìm kiếm (mỗi dòng 1 từ khóa)
4. **💬 Comment**: Nhập nội dung comment (mỗi dòng 1 comment, random chọn)
5. **📁 Ảnh**: Chọn thư mục chứa ảnh muốn đính kèm (tùy chọn)
6. **⏱ Thời gian**: Cấu hình delay, số bài, vòng lặp
7. Nhấn **💾 LƯU CẤU HÌNH**

### Bước 3: Chạy Tool
1. Quay lại Tab **🏠 Main**
2. Nhấn **START** để bắt đầu
3. Nhấn **STOP** để dừng bất cứ lúc nào

## 🗂️ Cấu trúc Project

```
Tool Tự Động Cmt/
├── main.py                      # GUI + Entry point
├── requirements.txt             # Thư viện cần cài
├── README.md                    # Hướng dẫn
├── core/
│   ├── __init__.py
│   ├── facebook_automation.py   # Engine tự động Facebook
│   ├── database_manager.py      # SQLite chống trùng
│   └── utils.py                 # Hàm tiện ích
├── data/
│   ├── history.db               # Database lịch sử (tự tạo)
│   └── config.json              # Cấu hình đã lưu (tự tạo)
└── photos/                      # Thư mục ảnh mặc định
```

## ⚙️ Tính năng

| # | Tính năng | Mô tả |
|---|-----------|-------|
| 1 | 🔍 Tìm kiếm từ khóa | Tìm bài viết mới nhất theo từ khóa trên Facebook |
| 2 | 💬 Comment tự động | Random chọn nội dung comment từ danh sách |
| 3 | 🖼️ Đính kèm ảnh | Tự động đính kèm ảnh random từ thư mục |
| 4 | 👥 Đa tài khoản | Hỗ trợ nhiều cookie Facebook |
| 5 | 🛡️ Chống trùng | SQLite database lưu lịch sử, không comment lại |
| 6 | 🔄 Chạy 24/7 | Vòng lặp tự động với delay tùy chỉnh |
| 7 | 🤖 Anti-detect | undetected-chromedriver tránh bị Facebook quét |
| 8 | ⏱️ Smart delay | Random delay 3-7s giữa mỗi thao tác |
| 9 | 🚨 Error handling | Try-catch mọi thao tác, không crash |
| 10 | 💾 Lưu cấu hình | Tự động load lại khi mở tool |

## ⚠️ Lưu ý

- Tool sử dụng Chrome, đảm bảo đã cài Google Chrome
- Cookie có thể hết hạn, cần cập nhật định kỳ
- Không nên chạy quá nhiều tài khoản cùng lúc
- Delay hợp lý (30s+) để tránh bị Facebook hạn chế
