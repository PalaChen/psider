import os
import sys
from loguru import logger

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

INFO_LOG = "info"


default_format:str=(
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "process:{process} {message}"
)

def get_log(path, file_name):
    file_path = os.path.join(path, f'log/{file_name}.log')
    logger.remove(handler_id=None)
    logger.add(file_path, encoding='utf-8', rotation="500 MB", compression="zip", retention="5 days",format=default_format)
    logger.add(sys.stderr)

    return logger


logger = get_log(BASE_PATH, INFO_LOG)
