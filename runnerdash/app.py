# -*- coding: utf-8 -*-

import logging

from flask import Flask
from flask_googlemaps import GoogleMaps
from flask_login import LoginManager

from .config import cfg
from .db import RunnerDB
from .notify import RunnerNotify
from .login import login_manager
from .views import IndexView, APIView, DashboardView, SettingsView, StatisticsView, LoginView, LogoutView, WizardView

log = logging.getLogger(__name__)


class RunnerDash(object):
    NAME = 'runnerdash'

    def __init__(self, base_path, db_file, host, port, debug, devel):
        self.port = port
        self.host = host
        self.debug = debug
        self.devel = devel
        self.base_path = base_path
        cfg.db_file = db_file
        cfg.base_path = base_path
        self.app = Flask(self.NAME, template_folder="templates")
        self.notify = RunnerNotify()

    def start(self):
        log.info(
            'starting runnerdash, base_path: %s, db: %s, port: %d, debug: %s', cfg.base_path, cfg.db_file, self.port,
            self.debug
        )
        self.app.add_url_rule('/', view_func=IndexView.as_view('index_view'))
        self.app.add_url_rule('/api', view_func=APIView.as_view('api_view'))
        self.app.add_url_rule('/wizard', view_func=WizardView.as_view('wizard_view'))
        self.app.add_url_rule('/login', view_func=LoginView.as_view('login_view'))
        self.app.add_url_rule('/logout', view_func=LogoutView.as_view('logout_view'))
        self.app.add_url_rule('/dashboard', view_func=DashboardView.as_view('dashboard_view'))
        self.app.add_url_rule('/settings', view_func=SettingsView.as_view('settings_view'))
        self.app.add_url_rule('/statistics', view_func=StatisticsView.as_view('statistics_view'))
        self.notify.start()
        db = RunnerDB(cfg.db_file)
        gmap_apikey = db.get_gmaps_api_key()
        if gmap_apikey:
            GoogleMaps(self.app, key=gmap_apikey)
        login_manager.login_view = "login_view"
        login_manager.setup_app(self.app)
        if self.devel:
            self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.secret_key = db._generate_random_api_key()
        self.app.run(host=self.host, port=self.port, debug=self.debug, use_reloader=self.devel)

    def stop(self):
        self.notify.stop()
