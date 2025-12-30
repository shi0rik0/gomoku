import logging
import subprocess
from pathlib import Path

import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
ROOT_DIR = Path(__file__).resolve().parent.parent


def main():
    result = subprocess.run(
        ["uv", "run", "alembic", "check"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
    )
    if result.stdout.find("FAILED: New upgrade operations detected: ") != -1:
        logger.warning(
            "Database migrations are out of date. Please run 'alembic upgrade head' to update the database schema."
        )
    logger.info("Starting development server...")
    subprocess.run(
        [
            "uv",
            "run",
            "uvicorn",
            "gomoku.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--log-config",
            str(ROOT_DIR / "log_config.json"),
        ],
        cwd=ROOT_DIR / "src",
    )


if __name__ == "__main__":
    main()
