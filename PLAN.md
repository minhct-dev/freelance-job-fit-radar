# Freelance Job Fit Radar — Kế hoạch MVP

## Mục tiêu

Xây một project cá nhân chạy được để nhận job từ dữ liệu mẫu hoặc nguồn được phép dùng, chấm mức độ phù hợp với profile bằng quy tắc minh bạch, giải thích lý do, rồi gửi thông báo Telegram. Đây là portfolio project, không phải dịch vụ đã triển khai cho khách hàng.

## Giả định và giới hạn

- Bắt đầu trên Windows với PowerShell; chọn Python vì phù hợp một MVP backend nhỏ. Nếu bạn đã quen TypeScript hơn, có thể đổi sang Node.js/Fastify trước khi bắt đầu.
- Người dùng đầu tiên là chính bạn; MVP chỉ cần một profile.
- Chưa xác minh API, điều khoản truy cập, hay các trường Upwork cung cấp. Vì vậy MVP **không phụ thuộc vào scraping hoặc kết nối Upwork**: dùng dữ liệu mẫu/nhập tay trước.
- Không giả định có trường “bid cao nhất hiện tại” hoặc đầy đủ thông tin khách hàng. Thiếu dữ liệu thì hiển thị “không có dữ liệu”, không suy đoán.
- Chưa có thông tin về thời gian rảnh/ngân sách; kế hoạch không ước lượng tiến độ hay chi phí.

## Tech stack

| Thành phần | Chọn cho MVP | Lý do |
|---|---|---|
| Python | 3.12 | Stack backend phổ biến, phù hợp MVP cá nhân |
| Môi trường/dependency | `uv` + `uv.lock` | Tái tạo môi trường và khóa phiên bản |
| API | FastAPI + Uvicorn | API thử được qua `/docs` |
| Validation/cấu hình | Pydantic + `pydantic-settings` | Kiểm tra dữ liệu, đọc cấu hình từ `.env` |
| Database | SQLite + SQLAlchemy 2.x | Dễ chạy local; chưa cần server DB riêng |
| Thông báo | Telegram Bot API + `python-telegram-bot` | Gửi cảnh báo đến chat cá nhân |
| Chất lượng | pytest + HTTPX + Ruff | Test logic/API và lint |
| Nguồn job ban đầu | JSON fixture / nhập thủ công | Có thể demo mà không phụ thuộc truy cập Upwork |

Chưa cần Docker, PostgreSQL, Redis, microservices, frontend hay LLM/Grok. Chỉ cân nhắc thêm sau khi MVP hoạt động và có nhu cầu cụ thể.

## 1. Cài đặt môi trường

Cài Python 3.12, Git, editor (ví dụ VS Code) và `uv` theo hướng dẫn chính thức của từng công cụ. Kiểm tra trong PowerShell:

```powershell
py -3.12 --version
git --version
uv --version
```

Tạo project:

```powershell
mkdir freelance-job-fit-radar
cd freelance-job-fit-radar
uv init --python 3.12
uv add fastapi "uvicorn[standard]" sqlalchemy pydantic-settings python-dotenv python-telegram-bot
uv add --dev pytest httpx ruff
New-Item -ItemType Directory -Force app, data, tests
New-Item -ItemType File -Force app/__init__.py
```

Giữ `pyproject.toml` và `uv.lock` trong Git. Khi dựng lại project, dùng `uv sync`.

## 2. Cấu trúc repo dự kiến

```text
freelance-job-fit-radar/
├── app/
│   ├── main.py             # FastAPI routes
│   ├── models.py           # Schema API/domain
│   ├── scoring.py          # Matching và giải thích
│   ├── repository.py       # Truy cập dữ liệu/SQLite
│   ├── settings.py         # Cấu hình môi trường
│   └── notifications.py    # Gửi Telegram
├── data/
│   └── jobs.json           # Dữ liệu demo, gắn nhãn rõ
├── tests/
│   ├── test_scoring.py
│   └── test_api.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── uv.lock
```

Có thể bắt đầu chỉ với `main.py`, `scoring.py`, `jobs.json` và test; thêm SQLite sau khi logic matching ổn.

## 3. Các mốc triển khai

### Mốc A — Job mẫu và matching

- Tạo schema job gồm các trường cơ bản có thể thiếu: `id`, `title`, `description`, `url`, `skills`, `budget_min`, `budget_max`, `currency`, `posted_at`.
- Tạo một profile đơn giản gồm kỹ năng/từ khóa và tiêu chí lọc tùy chọn.
- Viết hàm chấm điểm xác định, trả về điểm, kỹ năng khớp/thiếu và lý do.
- API ban đầu: `GET /health`, `GET /jobs`; thêm `POST /jobs/import` nếu cần nhập dữ liệu.
- Điểm chỉ là mức độ khớp với luật đã đặt, không phải xác suất thắng job.

**Đạt khi:** job mẫu trả về điểm và lý do nhất quán; trường thiếu không gây lỗi hoặc bị bịa giá trị; có test cho job khớp, không khớp và profile rỗng.

### Mốc B — API và test

- Chạy local bằng `uv run uvicorn app.main:app --reload`.
- Thử routes tại `http://127.0.0.1:8000/docs`.
- Viết test scoring và API bằng pytest/HTTPX.
- Chạy `uv run pytest -q` và `uv run ruff check .`.

**Đạt khi:** health check thành công, endpoint trả dữ liệu demo hợp lệ và test/lint chạy được.

### Mốc C — Telegram

1. Tạo bot bằng BotFather, lấy token.
2. Nhắn `/start` cho bot và lấy chat ID.
3. Lưu `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` trong `.env`.
4. Thử lệnh `/start` hoặc gửi một tin test.
5. Gửi cảnh báo cho job phù hợp, gồm tiêu đề, điểm, lý do và link nếu nguồn có link.

Bot polling nên chạy như tiến trình riêng; không khởi động polling mỗi lần API nhận request. Không commit token và không ghi token vào log. Nếu token lộ, thu hồi/tạo token mới.

**Đạt khi:** có thể nhận tin test; lỗi gửi được thể hiện rõ; lần xử lý lại job không gửi cảnh báo trùng.

### Mốc D — SQLite và chống trùng

- Lưu job, profile, kết quả match và trạng thái thông báo bằng SQLite/SQLAlchemy.
- Khử trùng dựa trên ID nguồn khi có; nếu chưa có thì tạo fingerprint từ các trường ổn định và kiểm tra va chạm.
- Ghi nhận trạng thái thông báo để tránh gửi trùng; lỗi gửi có thể quan sát và retry có giới hạn.

**Đạt khi:** nhập lặp một job không tạo bản ghi/cảnh báo lặp; có thể xem trạng thái job và lần gửi.

### Mốc E — Nguồn dữ liệu thật (chỉ khi xác minh)

Trước khi viết connector, kiểm tra tài liệu API và điều khoản hiện hành: cách truy cập có được phép không, dữ liệu nào thực sự được trả về, giới hạn truy cập và quyền lưu/hiển thị. Nếu chưa xác minh được, giữ fixture/nhập tay hoặc chọn một nguồn khác đã được phép sử dụng. Không tìm cách né đăng nhập, CAPTCHA hay rate limit.

## 4. Cấu hình và bảo vệ bí mật

Tạo `.env.example`:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DATABASE_URL=sqlite:///./radar.db
```

Tạo `.env` cục bộ từ file mẫu:

```powershell
Copy-Item .env.example .env
```

Đảm bảo `.gitignore` gồm:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
*.db
```

`.env.example` chỉ chứa tên biến và giá trị trống; bí mật thật chỉ nằm trong `.env` cục bộ.

## 5. Tiêu chí chất lượng và demo portfolio

- Demo chạy end-to-end: nhập job mẫu → xem match và lý do → nhận thông báo Telegram.
- Tests cho trường thiếu, job trùng, profile rỗng, không khớp và lỗi Telegram.
- README có hướng dẫn cài/run/test, sơ đồ luồng, cấu hình Telegram và ví dụ response.
- Gắn nhãn dữ liệu tổng hợp/nhập tay; nói rõ nếu chưa có tích hợp live với Upwork.
- Case study ghi đây là project cá nhân; chỉ nêu các phép đo đã chạy thật, kèm dữ liệu và cách đo.
- Không tuyên bố “không bao giờ bỏ lỡ job”, tăng tỷ lệ thắng, có khách hàng, hay chạy production nếu chưa có bằng chứng.

## Thứ tự bắt đầu

1. Cài Python/uv và tạo repo theo bước 1.
2. Tạo `jobs.json`, schema đơn giản, hàm matching và test.
3. Thêm FastAPI routes và thử `/docs`.
4. Thiết lập Telegram, gửi tin test rồi nối với matching.
5. Thêm SQLite/deduplication.
6. Chỉ khảo sát và tích hợp nguồn job thật sau khi xác minh quyền truy cập/dữ liệu.
