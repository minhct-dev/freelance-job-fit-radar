# Freelance Job Fit Radar

Portfolio MVP: Rank freelance jobs against a skills profile, explain the match, and send Telegram push notifications with persistent SQLite storage and deduplication (anti-spam).

> The included job records are synthetic portfolio fixtures. This project does not currently connect to live Upwork APIs without explicit authorization or credentials.

## Requirements

- Python 3.12+
- `uv`

## Setup (Windows PowerShell)

1. Cài đặt dependencies:
   ```powershell
   uv sync
   ```

2. Tạo file `.env` từ `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Điền `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` vào file `.env`.

3. Khởi chạy server FastAPI:
   ```powershell
   uv run uvicorn app.main:app --reload
   ```
   Mở trình duyệt: <http://127.0.0.1:8000/docs>

## Cơ chế SQLite & Chống trùng lặp (Deduplication)

Hệ thống sử dụng SQLite (`radar.db`) với 2 bảng:
- **`jobs`**: Lưu thông tin công việc (`id` là khóa chính). Khi quét job mới, lệnh `INSERT OR IGNORE` đảm bảo các job có `id` đã tồn tại sẽ bị bỏ qua, không gây trùng lặp dữ liệu.
- **`alerts`**: Lưu lịch sử thông báo (`job_id`, `sent_at`, `status`, `error_message`). Khi quét định kỳ, hệ thống chỉ lọc những job chưa từng có trạng thái `sent` để gửi tin nhắn Telegram. Nhờ đó, người dùng không bao giờ nhận thông báo lặp lại cho cùng một job.

## Scripts tiện ích

- **Thử kết nối Telegram:**
  ```powershell
  uv run python scripts/test_alert.py
  ```

- **Chạy quét job & kiểm tra chống trùng:**
  ```powershell
  uv run python scripts/scan_jobs.py
  ```

## Endpoints API

- `GET /health` — Kiểm tra trạng thái hoạt động của server.
- `GET /jobs` — Lấy danh sách job từ SQLite và xếp hạng theo Profile kỹ năng.
- `POST /jobs` — Nhập danh sách job mới (tự động bỏ qua job trùng lặp).
- `GET /alerts` — Xem toàn bộ lịch sử các thông báo đã gửi trong SQLite.
- `POST /alerts/scan?min_score=70` — Kích hoạt quét các job chưa gửi và bắn thông báo Telegram cho các job đạt ngưỡng điểm.

## Tests & Lint

```powershell
uv run pytest -q
uv run ruff check .
```
