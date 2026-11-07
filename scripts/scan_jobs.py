import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# THÊM ĐOẠN NÀY ĐỂ PYTHON TÌM ĐƯỢC THƯ MỤC 'app'
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Nạp file .env
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

from app.services.alert_service import scan_and_alert_jobs
from app.services.database import get_alerts, get_all_jobs, save_jobs
from app.main import PROFILE
from app.services.repository import load_jobs_from_fixture


async def main():
    print("=" * 60)
    print("FREELANCE JOB FIT RADAR - SCANNER & DEDUPLICATION DEMO")
    print("=" * 60)

    # 1. Nạp dữ liệu từ fixture vào SQLite (tự động lọc trùng)
    fixture_jobs = load_jobs_from_fixture()
    print(f"-> Đọc {len(fixture_jobs)} job từ data/jobs.json...")
    inserted = save_jobs(fixture_jobs)
    print(f"-> Lưu vào SQLite (radar.db): {inserted} job mới được thêm (đã lọc trùng).")

    total_in_db = len(get_all_jobs())
    print(f"-> Tổng số job hiện có trong cơ sở dữ liệu: {total_in_db}")

    # 2. Quét các job chưa từng gửi thông báo
    print("\n-> Đang kiểm tra các job chưa gửi thông báo...")
    result = await scan_and_alert_jobs(profile=PROFILE, min_fit_score=70)

    print("\nKẾT QUẢ QUÉT:")
    print(f"- Số job chưa gửi cần kiểm tra : {result['unalerted_scanned']}")
    print(f"- Số thông báo đã gửi qua bot  : {result['alerts_sent']}")
    print(f"- Số job bỏ qua (điểm < 70%)   : {result['skipped_low_score']}")
    print(f"- Số thông báo gửi lỗi        : {result['alerts_failed']}")

    # 3. Hiển thị lịch sử alerts trong SQLite
    alerts = get_alerts()
    print(f"\n-> Tổng số bản ghi trong bảng alerts: {len(alerts)}")
    for a in alerts[:5]:
        print(f"   [ID {a['id']}] Job: {a['job_id']} | Trạng thái: {a['status']} | Lúc: {a['sent_at']}")

    print("\n" + "=" * 60)
    print("LƯU Ý VỀ CHỐNG SPAM (DEDUPLICATION):")
    print("Nếu bạn chạy lại script này ngay bây giờ, hệ thống sẽ tự động")
    print("bỏ qua các job đã gửi và KHÔNG bắn lại tin nhắn trùng lặp lên Telegram!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

