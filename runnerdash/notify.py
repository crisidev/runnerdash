# -*- coding: utf-8 -*-
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .db import RunnerDB
from .utils import make_dirs
from .config import cfg

log = logging.getLogger(__name__)


class RunnerFileHandler(FileSystemEventHandler):
    def __init__(self, base_path):
        db = RunnerDB(cfg.db_file)
        db.load_activities(base_path)

    def on_created(self, event):
        path = event.src_path
        log.debug('new file creation event raised, path: %s', path)
        db = RunnerDB(cfg.db_file)
        db.load_activity(path)


class RunnerNotify(object):
    WATCH_DIR = 'activities'

    def __init__(self):
        self.base_path = os.path.join(cfg.base_path, self.WATCH_DIR)
        self.event_handler = RunnerFileHandler(self.base_path)
        self.observer = Observer()

    def start(self):
        make_dirs(self.base_path)
        self.observer.schedule(self.event_handler, path=self.base_path, recursive=False)
        self.observer.start()
        log.info("started filesystem notifier, base_path: %s", self.base_path)

    def stop(self):
        self.observer.stop()
        self.observer.join()
        log.info("stopped filesystem notifier, base_path: %s", self.base_path)
