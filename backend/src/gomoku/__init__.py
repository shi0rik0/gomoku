import logging

import colorlog

logger = logging.getLogger(__name__)
uvicorn_logger = logging.getLogger("uvicorn")


def setup_logging(logger: logging.Logger):
    # 清空现有处理器
    logger.handlers.clear()

    # 控制台处理器（带颜色）
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(name)s:%(lineno)d    %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # 文件处理器（带颜色）
    file_handler = logging.FileHandler("../logs/app.log")
    file_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(name)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logger.addHandler(file_handler)


setup_logging(logger)
setup_logging(uvicorn_logger)
