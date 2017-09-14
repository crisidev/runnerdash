# -*- coding: utf-8 -*-
import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler

from .config import cfg

log = logging.getLogger(__name__)


def make_dirs(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath, 0o755)


def handle_base_path():
    base_path = os.path.join(os.path.expanduser('~'), cfg.base_dir)
    make_dirs(base_path)
    return base_path


def setup_logging(debug, console, base_path):
    level = logging.DEBUG if debug else logging.INFO
    if not console:
        base_path = base_path or handle_base_path()
        log_file = os.path.join(base_path, cfg.log_file)
        rotation_handler = TimedRotatingFileHandler(log_file, when='h', interval=1, utc=True)
        logging.basicConfig(level=level, format=cfg.log_format, handlers=[rotation_handler])
    else:
        logging.basicConfig(level=level, format=cfg.log_format)
