# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def setup_logger(logger_name: str, enable_console: bool | None = None) -> logging.Logger:
    """创建或获取指定名称的logger，并根据开关控制是否输出到控制台。

    - 目录由环境变量 `LOG_DIR` 控制，默认 `logs`。
    - 是否输出到控制台由参数 `enable_console` 或环境变量 `LOG_TO_CONSOLE` 控制。
      当参数为 None 时，读取环境变量，取值为 1/true/yes/on 表示开启；其他表示关闭。
    """
    log_dir = os.getenv("LOG_DIR", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'

    if enable_console is None:
        env_val = os.getenv("LOG_TO_CONSOLE", "1").strip().lower()
        enable_console = env_val in ("1", "true", "yes", "on")

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        today = datetime.now().strftime('%Y%m%d')
        file_handler = logging.FileHandler(f'{log_dir}/{logger_name}_{today}.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))

        logger.addHandler(file_handler)

        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(console_handler)
    else:
        # 若已存在handler，确保开关一致：关闭控制台则移除纯控制台StreamHandler
        if not enable_console:
            for h in list(logger.handlers):
                # 注意：FileHandler继承自StreamHandler，这里仅移除“非文件”的StreamHandler
                if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
                    logger.removeHandler(h)

    return logger
