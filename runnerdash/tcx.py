# -*- coding: utf-8 -*-
import os

from lxml import objectify
from tcxparser import TCXParser, namespace


class RunnerTCX(TCXParser):
    @property
    def trackpoints(self):
        return self.root.xpath('//ns:Trackpoint', namespaces={'ns': namespace})
