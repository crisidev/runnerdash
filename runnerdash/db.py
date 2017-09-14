# -*- coding: utf-8 -*-
import os
import logging
from binascii import hexlify
from tempfile import NamedTemporaryFile
from collections import namedtuple

import arrow
import dataset
import sqlalchemy

from .tcx import RunnerTCX

log = logging.getLogger(__name__)

Activity = namedtuple('Activity', ['start_date', 'tcx'])


class RunnerDBError(Exception):
    pass


class RunnerDB(object):
    TABLE_ACTIVITIES = 'activities'
    TABLE_SETTINGS = 'settings'
    TABLE_HEART_RATE_VALUES = 'heart_rate_values'
    TABLE_TRACK_POINTS = 'track_points'

    def __init__(self, storage_path):
        self.storage_path = storage_path
        log.debug("initalizing db connection ot sqlite:///%s", self.storage_path)
        self._db = dataset.connect('sqlite:///{}'.format(self.storage_path))

    @property
    def db(self):
        return self._db

    @property
    def activities(self):
        return self._db[self.TABLE_ACTIVITIES]

    @property
    def settings(self):
        return self._db[self.TABLE_SETTINGS]

    @property
    def heart_rate_values(self):
        return self._db[self.TABLE_HEART_RATE_VALUES]

    @property
    def track_points(self):
        return self._db[self.TABLE_TRACK_POINTS]

    def _find_tcx_files(self, folder):
        for root, _, files in os.walk(folder):
            for name in files:
                if name.endswith('.tcx'):
                    yield self._tcx_to_activity(os.path.join(root, name))

    def _tcx_to_activity(self, path):
        tcx = RunnerTCX(path)
        tcx_start_date = tcx.activity.Id.text
        log.debug("found activity tcx file, start_date: %s", tcx_start_date)
        return Activity(tcx_start_date, tcx)

    def _store_activity(self, activity):
        activity_date = str(activity.tcx.activity.Id.text)
        if not self.find_activity_by_date(activity_date):
            json_activity = {
                'activity': activity_date,
                'activity_type': activity.tcx.activity_type,
                'altitude_avg': activity.tcx.altitude_avg,
                'altitude_max': activity.tcx.altitude_max,
                'altitude_min': activity.tcx.altitude_min,
                'altitude_units': 'meters',
                'ascent': activity.tcx.ascent,
                'ascent_units': 'meters',
                'calories': activity.tcx.calories,
                'completed_at': activity.tcx.completed_at,
                'descent': activity.tcx.descent,
                'descent_units': 'meters',
                'distance': float(activity.tcx.distance),
                'distance_units': activity.tcx.distance_units,
                'duration': activity.tcx.duration,
                'duration_units': 'seconds',
                'heart_rate_avg': -1,
                'heart_rate_max': -1,
                'heart_rate_min': -1,
                'creator': str(activity.tcx.activity.Creator.Name),
                'pace': activity.tcx.pace,
                'pace_hours': sum(int(x) * 60**i
                                  for i, x in enumerate(reversed(activity.tcx.pace.split(":")))) / 60 / 60,
                'pace_units': 'mm:ss/km',
                'started_at': activity.start_date,
                'start_latitude': activity.tcx.latitude,
                'start_longitude': activity.tcx.longitude
            }
            if activity.tcx.hr_values():
                json_activity.update(
                    {
                        'heart_rate_avg': activity.tcx.hr_avg,
                        'heart_rate_max': activity.tcx.hr_max,
                        'heart_rate_min': activity.tcx.hr_min,
                    }
                )

            log.info("registering new activity %s", activity_date)
            return self.activities.insert(json_activity)
        else:
            log.info("activity %s already registered", activity_date)
            return 0

    def _store_heart_rate_values(self, activity_id, activity):
        for value in activity.tcx.hr_values():
            self.heart_rate_values.insert({'activity_id': activity_id, 'value': value})

    def _store_track_points(self, activity_id, activity):
        for track in activity.tcx.trackpoints:
            self.track_points.insert(
                {
                    'activity_id': activity_id,
                    'altitude': float(track.AltitudeMeters),
                    'altitude_units': 'meters',
                    'distance': float(track.DistanceMeters),
                    'distance_units': 'meters',
                    'latitude': float(track.Position.LatitudeDegrees),
                    'longitude': float(track.Position.LongitudeDegrees),
                    'timestamp': str(track.Time)
                }
            )

    def _query_like(self, table, column, filter):
        statement = 'SELECT * FROM {} WHERE {} LIKE "%{}%"'.format(table, column, filter)
        return self.db.query(statement)

    def _load_activity(self, activity):
        activity_id = self._store_activity(activity)
        if activity_id:
            self._store_heart_rate_values(activity_id, activity)
            self._store_track_points(activity_id, activity)

    def _get_settings(self):
        return self.settings.find_one(id=0) or {}

    def _generate_random_api_key(self):
        return hexlify(os.urandom(24)).decode()

    def regenerate_apikey(self):
        api_key = self._generate_random_api_key()
        data = {'api_key': api_key, 'id': 0}
        self.settings.update(data, ['id'])

    def is_first_run(self):
        try:
            return True if len(self.settings.columns) == 1 else False
        except sqlalchemy.exc.OperationalError:
            return True

    def load_activities(self, folder):
        log.info("loading exitisting activities from folder %s", folder)
        for activity in self._find_tcx_files(folder):
            self._load_activity(activity)

    def load_activity_xml(self, xml):
        with NamedTemporaryFile() as fd:
            fd.write(xml)
            activity = self._tcx_to_activity(fd.name)
            self._load_activity(activity)

    def load_activity(self, path):
        if path.endswith('.tcx'):
            log.info("loading new activity from file %s", path)
            activity = self._tcx_to_activity(path)
            self._load_activity(activity)

    def find_activity_by_id(self, activity_id):
        return self.activities.find_one(id=activity_id)

    def find_activity_by_date(self, activity_date):
        return self.activities.find_one(activity=activity_date)

    def find_last_activity(self):
        statement = 'SELECT * FROM {} WHERE activity LIKE "%" ORDER BY started_at DESC LIMIT 1'.format(
            self.TABLE_ACTIVITIES
        )
        return self.db.query(statement)

    def find_all_activities(self):
        try:
            statement = 'SELECT * FROM {} WHERE activity LIKE "%" ORDER BY started_at DESC'.format(
                self.TABLE_ACTIVITIES
            )
            return self.db.query(statement)
        except sqlalchemy.exc.OperationalError:
            return []

    def find_past_activities(self, past=7):
        past = arrow.now().shift(days=-past)
        for activity in self.find_activities():
            if past <= arrow.get(activity.get('started_at')):
                yield activity

    def update_settings(self, username, birthdate, gender, weight, gmap_apikey, password=None):
        data = {
            'id': 0,
            'username': username,
            'birth_date': birthdate,
            'gender': gender,
            'weight': weight,
            'gmap_apikey': gmap_apikey
        }
        if password:
            data.update({'password': password})
        settings = self._get_settings()
        if not settings or not settings.get('api_key'):
            api_key = self._generate_random_api_key()
            data.update({'api_key': api_key})
            self.settings.insert(data)
        else:
            api_key = settings.get('api_key')
            data.update({'api_key': api_key})
            self.settings.update(data, ['id'])

    def get_gmaps_api_key(self):
        return self._get_settings().get('gmap_apikey')

    def get_user_password(self, username):
        settings = self.settings.find_one(username=username) or {}
        if settings:
            return settings.get('password')
        return None

    def get_user_id(self, username):
        settings = self.settings.find_one(username=username)
        if settings:
            return settings.get('id')
        return None

    def find_user_by_id(self, id):
        return self.settings.find_one(id=id)

    def find_all_api_keys(self):
        return [x.get('api_key') for x in self.settings.all()]
