# -*- coding: utf-8 -*-
import random
import logging

import arrow

from .db import RunnerDB
from .maps import RunnerMap
from .config import cfg

log = logging.getLogger(__name__)


class RunnerCalculator(object):
    GRANULARITY = 10
    MET_TABLE = {
        'running': {
            4.0: 3.0,
            4.5: 3.5,
            6.4: 6.0,
            8.0: 8.3,
            9.5: 9.8,
            11.2: 11,
            12.9: 11.8,
            14.5: 12.8,
            16.0: 14.5,
            17.7: 16.0,
            19.3: 19.0,
            20.9: 19.8,
            22.5: 23.0
        }
    }

    def __init__(self):
        self.gmap = RunnerMap()
        self.db = RunnerDB(cfg.db_file)

    def _calculate_calories(self, weight, pace, duration, activity_type):
        speed = 1 / pace
        met_table = self.MET_TABLE[activity_type]
        value = min(met_table.keys(), key=lambda x: abs(x - speed))
        met = met_table[value]
        return met * weight * duration / 60 / 60

    def _calculate_duration(self, start, end):
        duration = (end - start).total_seconds()
        if duration < 60:
            return '{} sec'.format(duration)
        else:
            return '{0:.0f} min {1:.0f} sec'.format((duration % 3600) // 60, duration % 60)

    def _activity_table(self):
        for activity in self.db.find_all_activities():
            start = arrow.get(activity.get('started_at'))
            end = arrow.get(activity.get('completed_at'))
            calories = activity.get('calories')
            if not calories:
                calories = self._calculate_calories(
                    self.db._get_settings().get('weight'),
                    activity.get('pace_hours'), activity.get('duration'), activity.get('activity_type')
                )

            yield {
                'activity-id': activity.get('id'),
                'date': start.format('ddd DD MMM YYYY'),
                'start_time': start.format('HH:mm'),
                'type': activity.get('activity_type').capitalize(),
                'distance': '{0:.2f} km'.format(activity.get('distance') / 1000),
                'duration': self._calculate_duration(start, end),
                'pace': '{} min/km'.format(activity.get('pace')),
                'calories': '{0:.0f}'.format(calories)
            }

    def _get_path(self, trackpoints):
        return [{
            'lat': trackpoint.get('latitude'),
            'lng': trackpoint.get('longitude')
        } for trackpoint in trackpoints]

    def _get_random_activity_map(self):
        activity = random.choice(list(self.db.find_all_activities()))

        trackpoints = self.db.track_points.find(activity_id=activity.get('id'))
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

        return self.gmap.render('fullmap', middle_point['lat'], middle_point['lng'], path=path, markers=markers)
