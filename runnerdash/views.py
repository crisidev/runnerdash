# -*- coding: utf-8 -*-
import math
import logging

import numpy
import arrow
from passlib.hash import pbkdf2_sha256
from flask.views import View, MethodView
from flask import render_template, request, redirect, url_for, jsonify, current_app
from flask_googlemaps import GoogleMaps
from flask_login import login_required, login_user, logout_user

from .login import User, apikey_required
from .calculator import RunnerCalculator

log = logging.getLogger(__name__)


class LoginView(MethodView, RunnerCalculator):
    def get(self):
        return render_template('login.html')

    def post(self):
        username = request.form['signin-name']
        remember = request.form.get('signin-remember') == "1"
        db_pass = self.db.get_user_password(username)
        user_id = self.db.get_user_id(username)
        if db_pass is not None and user_id is not None and pbkdf2_sha256.verify(request.form['signin-pass'], db_pass):
            user = User(username, user_id)
            login_user(user, remember=remember)
            return redirect(url_for('index_view'), code=302)
        return render_template('login.html', failed=True)


class LogoutView(View, RunnerCalculator):
    decorators = [login_required]

    def dispatch_request(self):
        logout_user()
        return render_template('login.html', logout=True)


class IndexView(View, RunnerCalculator):
    decorators = [login_required]

    def dispatch_request(self):
        if self.db.is_first_run():
            return redirect(url_for('wizard_view'), code=302)
        else:
            return render_template(
                'index.html', activities=self._activity_table(), fullmap=self._get_random_activity_map()
            )


class DashboardView(MethodView, RunnerCalculator):
    decorators = [login_required]

    def post(self):
        activity_id = request.form['activity-id']

        trackpoints = list(self.db.track_points.find(activity_id=activity_id))
        path = self._get_path(trackpoints)

        start_point = path[0]
        middle_point = path[len(path) // 2]
        end_point = path[-1]

        markers = [
            {
                'color': 'green',
                'lat': start_point['lat'],
                'lng': start_point['lng'],
                'label': 'Start!'
            }, {
                'color': 'red',
                'lat': end_point['lat'],
                'lng': end_point['lng'],
                'label': 'End!'
            }
        ]

        trackmap = self.gmap.render(
            'trackmap',
            middle_point['lat'],
            middle_point['lng'],
            path=path,
            markers=markers,
            zoom=15,
            height="400px",
            position="relative",
            zindex=200
        )

        distances = numpy.diff([x.get('distance') for x in trackpoints])[::self.GRANULARITY]
        times = numpy.diff([arrow.get(x.get('timestamp')) for x in trackpoints])[::self.GRANULARITY]
        speeds = [
            '{0:.1f}'.format(x) for x in [x / y.total_seconds() * 3.6
                                          for x, y in zip(distances, times)] if not math.isnan(x)
        ]
        timestamps = [arrow.get(x.get('timestamp')).format("HH:mm") for x in trackpoints][::self.GRANULARITY]

        return render_template('dashboard.html', trackmap=trackmap, speeds=speeds, timestamps=timestamps)


class WizardView(MethodView, RunnerCalculator):
    def get(self):
        if self.db.is_first_run():
            settings = self.db._get_settings()
            return render_template('wizard.html', run_wizard="1", settings=settings)
        else:
            return redirect(url_for('index_view'), code=302)

    def post(self):
        if self.db.is_first_run():
            username = request.form['settings-name']
            birthdate = request.form['settings-birth']
            gender = request.form['settings-gender']
            weight = int(request.form['settings-weight'])
            gmap_apikey = request.form['settings-mapskey']
            password = pbkdf2_sha256.encrypt(request.form['settings-pass'], rounds=200000, salt_size=16)
            self.db.update_settings(username, birthdate, gender, weight, gmap_apikey, password=password)
            GoogleMaps(current_app, key=self.db.get_gmaps_api_key())
            return url_for('login_view')
        else:
            return url_for('index_view')


class SettingsView(MethodView, RunnerCalculator):
    decorators = [login_required]

    def get(self):
        settings = self.db._get_settings()
        return render_template(
            'settings.html', run_wizard="0", fullmap=self._get_random_activity_map(), settings=settings
        )

    def post(self):
        if request.form.get('settings-regen-apikey') == "1":
            self.db.regenerate_apikey()
            return url_for('settings_view')
        username = request.form['settings-name']
        birthdate = request.form['settings-birth']
        gender = request.form['settings-gender']
        weight = int(request.form['settings-weight'])
        gmap_apikey = request.form['settings-mapskey']
        password = request.form.get('settings-pass')
        if password:
            password = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
        self.db.update_settings(username, birthdate, gender, weight, gmap_apikey, password=password)
        return url_for('settings_view')


class APIView(MethodView, RunnerCalculator):
    decorators = [apikey_required]

    def post(self):
        self.db.load_activity_xml(request.data)
        return jsonify("success")


class StatisticsView(View, RunnerCalculator):
    decorators = [login_required]

    def dispatch_request(self):
        return render_template('statistics.html', fullmap=self._get_random_activity_map())
