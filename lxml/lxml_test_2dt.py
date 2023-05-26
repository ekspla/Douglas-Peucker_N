# -*- coding: utf-8 -*-

from collections import namedtuple
import time
from pathlib import Path
import sys
from datetime import datetime
import math
from lxml import etree
import reduce_points_2dt

start_t = time.time()

Trackpt = namedtuple('Trackpt', 'longitude, latitude, time')
Trackpt.__new__.__defaults__ = (None,) * len(Trackpt._fields)

argvs = sys.argv
argc = len(argvs)
if argc < 2:
    print(f'Usage: # python {argvs[0]} input_filename number_of_points\n')
    sys.exit(0)
in_file = argvs[1]
points = 2000 if argc < 3 else int(argvs[2])
out_file = Path(str(in_file)[:-4] + '_c.gpx')

tree = etree.parse(in_file)
NSMAP = tree.getroot().nsmap
trk = tree.findall('trk', namespaces=NSMAP)
trkseg = [x.findall('trkseg', namespaces=NSMAP) for x in trk][0]
trkpts = [x.findall('trkpt', namespaces=NSMAP) for x in trkseg][0]

gpx_segment = [Trackpt(
    longitude=float(x.attrib['lon']), 
    latitude=float(x.attrib['lat']), 
    time=datetime.fromisoformat(x.findall('time', namespaces=NSMAP)[0].text.replace('Z', '+00:00')), 
    ) 
    for x in trkpts]

length_2d = 111319 * sum([math.hypot( # 111319 m / deg., approximately.
    gpx_segment[i-1].latitude - x.latitude, 
    (gpx_segment[i-1].longitude - x.longitude) * math.cos(math.radians(gpx_segment[i-1].latitude)),
    ) if i else 0.0 for (i, x) in enumerate(gpx_segment)])
ave_speed = length_2d / (gpx_segment[-1].time - gpx_segment[0].time).total_seconds() # m/s
#print(length_2d, ave_speed)

rm_trkpts = reduce_points_2dt.reduce_points2dt(gpx_segment, target_points=points, flags_out=True, ave_speed=ave_speed)

parent = trkpts[0].getparent()
for trkpt, rm_trkpt in zip(trkpts, rm_trkpts):
    if rm_trkpt:
        parent.remove(trkpt)

with out_file.open('wb') as f:
    f.write(etree.tostring(
        tree, encoding='UTF-8', pretty_print=True, 
        doctype='<?xml version="1.0" encoding="UTF-8"?>'))

print(f'Processing Time: {time.time() - start_t} s.')
