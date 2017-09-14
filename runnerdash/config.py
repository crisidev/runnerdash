# -*- coding: utf-8 -*-
import logging

log = logging.getLogger(__name__)


class RunnerConfig(dict):
    def __init__(self):
        super().__init__()
        self.base_dir = '.config/runnerdash'
        self.log_file = 'runnerdash.log'
        self.log_format = "%(asctime)s [%(levelname)s] pid(%(process)d): %(message)s"

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


cfg = RunnerConfig()
