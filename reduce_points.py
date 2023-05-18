﻿# -*- coding: utf-8 -*-
#
# 2023, a quick python port by ekspla.  https://github.com/ekspla
#
# Reduce gpx track points by using Douglas-Peucker N algorithm.
# (https://psimpl.sourceforge.net/douglas-peucker.html)
#
# Originally written in javascript by 330k.  https://github.com/330k
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
                    segment.points = reduce_points2(trkpts, num_points)
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


def reduce_points2(trkpts, target_points):
    """Reduce gpx track points using Douglas-Peucker N
    
    Args:
        trkpts; should be an iterable containing track points.
            Each track point should have attributes of longitude
            and latitude in decimal degree format.
        target_points; number of points in integer

    Returns:
        a list of track points; reduced_points
    """
    queue = PriorityQueue()
    #removed_points = []
    #reduced_points = []
    count = 2
    v = {}

    pts = [(
            math.radians(trkpt.longitude), 
            math.asinh(math.tanh(math.radians(trkpt.latitude))), 
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

    #for i in range(len(pts)):
    #    if flags[i]:
    #        removed_points.append(trkpts[i])
    #    else:
    #        reduced_points.append(trkpts[i])
    #print(len(removed_points), len(reduced_points))

    reduced_points = [trkpts[i] for i in range(len(pts)) if not flags[i]]
    return reduced_points


def find_farthest(pts, start, end):
    a = pts[start]
    b = pts[end]
    d = 0.0
    m = -sys.float_info.max
    c = -1

    for i in range(start + 1, end):
        #d = segment_point_distance(a[0], a[1], b[0], b[1], pts[i][0], pts[i][1])
        d = segment_point_distance(*a, *b, *pts[i])
        if m < d:
            m = d
            c = i
    return {'start':start, 'end':end, 'pos':c, 'dist':m}


def segment_point_distance(ax, ay, bx, by, px, py):
    t = (ax ** 2 + ay ** 2 + bx * px - ax * (bx + px) + by * py - ay * (by + py))/(ax ** 2 + ay ** 2 - 2 * ax * bx + bx ** 2 - 2 * ay * by + by ** 2)
    x = ax - (ax - bx) * t
    y = ay - (ay - by) * t

    if 0 <= t <= 1:
        return (x - px) ** 2 + (y - py) ** 2
    elif t > 1:
        return (bx - px) ** 2 + (by - py) ** 2
    else:
        # // includes A == B
        return (ax - px) ** 2 + (ay - py) ** 2


class PriorityQueue():
    name = "Pairing Heap"
    _size = 0
    _root = None

    def _merge(self, i, j):
        if i == None: return j
        if j == None: return i

        if i['p'] < j['p']:
            ret = i
            i = j
            j = ret

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
