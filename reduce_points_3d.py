# -*- coding: utf-8 -*-
#
# May 2023, a quick python port by ekspla.  https://github.com/ekspla/Douglas-Peucker_N
#
# Reduce gpx track points by using Douglas-Peucker N algorithm.
# (https://psimpl.sourceforge.net/douglas-peucker.html)
#
# Original version written in JavaScript by 330k.  https://github.com/330k/gpx_tools
# (c) 2014-2023 Kei Misawa, MIT License.

import math
import sys
from pathlib import Path
import time
import gpxpy
import gpxpy.gpx


def reduce_points(gpxdocs, num_points=65535, write_file=True):
    with gpxdocs.open('r') as gpx_file_r:
        gpx = gpxpy.parse(gpx_file_r)

        for track in gpx.tracks:
            for segment in track.segments:
                trkpts = segment.points
                trkpts_length = len(trkpts)
                if num_points < trkpts_length:
                    start_time = time.time()
                    segment.points = reduce_points3d(trkpts, num_points)
                    print(f'Time: {time.time() - start_time} s')
                print(f'Reduce trkpt: from {trkpts_length} to {len(segment.points)}')

        out_file = Path(str(gpxdocs)[:-4] + '_c.gpx') if write_file else None
        finalize_gpx(gpx, out_file)


def finalize_gpx(gpx, outfile_path=None):
    """Output gpx xml to the outfile_path (or print if not specified).

    Args:
        gpx
        outfile_path (optional): write gpx xml to the file or print (if None).
    """
    if outfile_path is not None:
        result = gpx.to_xml('1.1')
        result_file = open(outfile_path, 'w')
        result_file.write(result)
        result_file.close()
    else:
        print(gpx.to_xml('1.1'))


def reduce_points3d(trkpts, target_points):
    """Reduce gpx track points using Douglas-Peucker N

    Args:
        trkpts; an iterable object containing track points.
            Each track point should have attributes of longitude/
            latitude (in decimal degrees) and elevation (float).
        target_points; number of points in integer

    Returns:
        a list of track points; reduced_points
    """
    queue = PriorityQueue()
    count = 2

    pts = [latlng2xyz(trkpt.latitude, trkpt.longitude, trkpt.elevation)
        for trkpt in trkpts]
    flags = [True, ] * len(trkpts)

    farthest = find_farthest(pts, 0, len(pts) - 1)
    queue.enqueue(farthest['dist'], farthest)
    flags[0] = flags[-1] = False

    while queue.size() and (count < target_points):
        v = queue.dequeue()
        flags[v['pos']] = False
        count += 1

        if (v['start'] + 2 <= v['pos']):
            farthest = find_farthest(pts, v['start'], v['pos'])
            queue.enqueue(farthest['dist'], farthest)

        if (v['pos'] + 2 <= v['end']):
            farthest = find_farthest(pts, v['pos'], v['end'])
            queue.enqueue(farthest['dist'], farthest)

    reduced_points = [trkpt for trkpt, flag in zip(trkpts, flags) if not flag]
    return reduced_points


def latlng2xyz(lat, lng, h = 0.0):
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    f2 = 1 - e2

    latrad = math.radians(lat)
    lngrad = math.radians(lng)

    sinlat = math.sin(latrad)
    coslat = math.cos(latrad)
    sinlng = math.sin(lngrad)
    coslng = math.cos(lngrad)

    w2 = 1.0 - sinlat * sinlat * e2
    w = math.sqrt(w2)
    N = a / w

    return (
            (N + h) * coslat * coslng,
            (N + h) * coslat * sinlng,
            (N * f2 + h) * sinlat,
           )


def find_farthest(pts, start, end):
    a = pts[start]
    b = pts[end]
    d = 0.0
    m = -sys.float_info.max
    c = -1

    for i in range(start + 1, end):
        d = segment_point_distance3d(*a, *b, *pts[i])
        if m < d:
            m = d
            c = i
    return {'start':start, 'end':end, 'pos':c, 'dist':m}


def segment_point_distance3d(ax, ay, az, bx, by, bz, px, py, pz):
    """Squared distance, actually"""
    t = ((ax - bx) * (ax - px) + (ay - by) * (ay - py) + (az - bz) * (az - pz)) / ((ax - bx) * (ax - bx) + (ay - by) * (ay - by) + (az - bz) * (az - bz))

    if t > 1:
        t = 1
    elif t > 0:
        pass
    else:
        # // includes A == B
        t = 0

    x = ax - t * (ax - bx)
    y = ay - t * (ay - by)
    z = az - t * (az - bz)

    #return math.hypot(x - px, y - py, z - pz) # for Python version => 3.8
    return (x - px) * (x - px) + (y - py) * (y - py) + (z - pz) * (z - pz)


class PriorityQueue():
    name = "Pairing Heap"
    _size = 0
    _root = None

    def _merge(self, i, j):
        if i is None: return j
        if j is None: return i

        if i['p'] < j['p']:
            i, j = j, i

        j['next'] = i['head']
        i['head'] = j

        return i

    def _mergeList(self, s):
        n = None

        while s:
            a = s
            b = None
            s = s['next']
            a['next'] = None
            if s:
                b = s
                s = s['next']
                b['next'] = None

            a = self._merge(a, b)
            a['next'] = n
            n = a

        while n:
            j = n
            n = n['next']
            s = self._merge(j, s)

        return s

    def enqueue(self, priority, value):
        self._root = self._merge(self._root, {
            'p': priority,
            'v': value,
            'next': None,
            'head': None,
            })
        self._size += 1

    def dequeue(self):
        result = self._root['v']
        self._root = self._mergeList(self._root['head'])
        self._size -= 1

        return result

    def size(self):
        return self._size


if __name__ == '__main__':
    reduce_points(Path(sys.argv[1]), 2000)
