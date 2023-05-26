# Douglas-Peucker_N

Reduce gpx track points by using Douglas-Peucker N algorithm.  https://psimpl.sourceforge.net/douglas-peucker.html

May 2023, a quick python port by ekspla.  https://github.com/ekspla/Douglas-Peucker_N

Requires gpxpy.  https://github.com/tkrajina/gpxpy

Original version written in JavaScript by 330k.  https://github.com/330k/gpx_tools

## Introduction
This is a faster algorithm to reduce size of a track as compared to simplify--crosstrack in gpsbabel [1](https://www.gpsbabel.org/htmldoc-1.8.0/filter_simplify.html).
I found it useful for processing tracks/routes before installing them into a small navigation devices.

Processing time was measured using my core i5 (gen4) PC with CPython 3.9 and compared with those of gpsbabel.
It took less than 1 sec to reduce 78252 of trackpoints (a sample file in 330k's web site  [2](https://github.com/330k/gpx_tools)) to 2000 points, 
surprisingly faster than 23 sec with gpsbabel.

## Coordinate transformations used in the scripts
- `reduce_points.py`  
  (x, y) = Mercator_projection(latitude, longitude); assuming sphere.
- `reduce_points_3d.py`  
  (x, y, z) = Cartesian(latitude, longitude, altitude); assuming ellipsoid.
- `reduce_points_2dt.py`  
  (x, y) = Mercator_projection(latitude, longitude); assuming sphere.  
  z = time * Average_speed
    This script may be useful in processing real gps tracks with timestamps.

## How to use
**An example to process tracks** is shown in **reduce_points()**.  For routes/waypoints, modify the codes in that function.

If you want to use them with **lxml**, examples are shown in **./lxml**.

## Reference
[1] https://www.gpsbabel.org/htmldoc-1.8.0/filter_simplify.html

[2] https://github.com/330k/gpx_tools

[3] https://330k.github.io/line_simplify_demo/gpx_visual_simplify.html
