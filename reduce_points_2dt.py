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
                    ave_speed = segment.length_2d() / segment.get_duration()
                    #print(ave_speed)
                    start_time = time.time()
                    segment.points = reduce_points2dt(trkpts, num_points, ave_speed=ave_speed)
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


def reduce_points2dt(trkpts, target_points, flags_out=False, ave_speed=5.556):
    """Reduce gpx track points using Douglas-Peucker N

    Args:
        trkpts; an iterable object containing track points.
            Each track point should have attributes of longitude/
            latitude (in decimal degrees) and elevation (float).
        target_points; number of points in integer
        flags_out; True/False output flags if True.
        ave_speed; averaged speed in m/s used for scaling times.

    Returns:
        a list of track points; reduced_points
    """
    queue = PriorityQueue()
    count = 2

    start_time = trkpts[0].time
    pts = [latlngt2xyz(
        trkpt.latitude, 
        trkpt.longitude, 
        (trkpt.time - start_time).total_seconds(), 
        ave_speed
        ) for trkpt in trkpts]
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

    if flags_out:
        return flags
    else:
        reduced_points = [trkpt for trkpt, flag in zip(trkpts, flags) if not flag]
        return reduced_points


def latlngt2xyz(lat, lng, t, ave_speed=5.556):

    # Mercator coordinates in radians
    x = math.asinh(math.tan(math.radians(lat)))
    y = math.radians(lng)

    # Scale times [s] using averaged speed [m/s]
    a = 6378137.0 # Radius in meters
    z = t * ave_speed / a

    return (x, y, z)


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
    argvs = sys.argv
    argc = len(argvs)
    if argc < 2:
        print(f'Usage: # python {argvs[0]} input_filename number_of_points\n')
        sys.exit(0)
    in_file = argvs[1]
    points = 2000 if argc < 3 else int(argvs[2])
    reduce_points(Path(in_file), points)
