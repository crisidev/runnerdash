# -*- coding: utf-8 -*-
import logging

from flask_googlemaps import Map, icons

log = logging.getLogger(__name__)


class RunnerMap(object):
    STYLE = (
        "height:{0};"
        "width:{1};"
        "top:{2};"
        "bottom:{3};"
        "left:{4};"
        "right:{5};"
        "position:{6};"
        "z-index:{7};"
    )

    def render(
        self,
        name,
        lat,
        lng,
        zoom=16,
        path=[],
        markers={},
        height="100%",
        width="100%",
        top=0,
        bottom=0,
        left=0,
        right=0,
        position="absolute",
        zindex=0
    ):
        map_markers = {}
        for marker in markers:
            map_markers[getattr(icons.dots, marker['color'])] = [
                (marker['lat'], marker['lng'], "<b style='color:{};'>{}</b>".format(marker['color'], marker['label']))
            ]
        return Map(
            identifier=name,
            varname=name,
            lat=lat,
            lng=lng,
            style=self.STYLE.format(height, width, top, bottom, left, right, position, zindex),
            zoom=zoom,
            markers=map_markers,
            polylines=[{
                'stroke_color': '#0AB0DE',
                'stroke_opacity': 1.0,
                'stroke_weight': 3,
                'path': path
            }]
        )
