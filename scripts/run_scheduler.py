import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure root dir is in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Load .env
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

from app.services.scheduler import scheduler
from app.utils.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler_runner")


async def main() -> None:
    print("=" * 65)
    print("FREELANCE JOB FIT RADAR - AUTOMATIC BACKGROUND SCHEDULER")
    print("=" * 65)
    print(f"Chu ky quet tu dong : Moi {settings.scan_interval_minutes} phut ({scheduler.interval_seconds}s)")
    print(f"Diem nguong fit_score: >= {settings.min_fit_score}%")
    print(f"Database             : {settings.database_url}")
    print("Nhan Ctrl + C de dung tien trinh bat cu luc nao.")
    print("=" * 65 + "\n")

    scheduler.start()

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nNhan tin hieu dung, dang tat scheduler an toan...")
        await scheduler.stop()
        print("Scheduler da dung an toan.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
