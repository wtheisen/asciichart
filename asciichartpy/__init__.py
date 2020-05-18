# -*- coding: utf-8 -*-
"""Module to generate ascii charts.

This module provides a single function `plot` that can be used to generate an
ascii chart from a series of numbers. The chart can be configured via several
options to tune the output.
"""

from __future__ import division
from math import ceil, floor, isnan

__all__ = ['plot']

# Python 3.2 has math.isfinite, which could have been used, but to support older
# versions, this little helper is shorter than having to keep doing not isnan(),
# plus the double-negative of "not is not a number" is confusing, so this should
# help with readability.
def _isnum(n):
    return not isnan(n)

def plot(series, cfg=None):
    """Generate an ascii chart for a series of numbers.

    `series` should be a list of ints or floats. Missing data values in the
    series can be specified as a NaN. In Python versions less than 3.5, use
    float("nan") to specify an NaN. With 3.5 onwards, use math.nan to specify a
    NaN.

        >>> series = [1,2,3,4,float("nan"),4,3,2,1]
        >>> print(plot(series))
            4.00  ┤  ╭╴╶╮
            3.00  ┤ ╭╯  ╰╮
            2.00  ┤╭╯    ╰╮
            1.00  ┼╯      ╰

    `cfg` is an optional dictionary of various parameters to tune the appearance
    of the chart. `minimum` and `maximum` will clamp the y-axis and all values:

        >>> series = [1,2,3,4,float("nan"),4,3,2,1]
        >>> print(plot(series, {'minimum': 0}))
            4.00  ┼  ╭╴╶╮
            3.00  ┤ ╭╯  ╰╮
            2.00  ┤╭╯    ╰╮
            1.00  ┼╯      ╰
            0.00  ┤

        >>> print(plot(series, {'minimum': 2}))
            4.00  ┤  ╭╴╶╮
            3.00  ┤ ╭╯  ╰╮
            2.00  ┼─╯    ╰─

        >>> print(plot(series, {'minimum': 2, 'maximum': 3}))
            3.00  ┤ ╭─╴╶─╮
            2.00  ┼─╯    ╰─

    `height` specifies the number of rows the graph should occupy. It can be
    used to scale down a graph with large data values:

        >>> series = [10,20,30,40,50,40,30,20,10]
        >>> print(plot(series, {'height': 4}))
           50.00  ┤   ╭╮
           40.00  ┤  ╭╯╰╮
           30.00  ┤ ╭╯  ╰╮
           20.00  ┤╭╯    ╰╮
           10.00  ┼╯      ╰

    `color` specifies a tuple with ascii escape sequence(s) to wrap the graphs
    in, if threshold is in use, then the first color will be used if the final
    value is above the threshold, the second if below.
    
        >>> print(plot(series, {'colors': ('\033[0;32;40m')}))

    `threshold` specifies a y-value that will change the coloring of the graph
    depending on whether the final value in the series is above or below the
    threshold.

        >>> print(plot(series, {'threshold': 25}))

    `width` can be used to specifiy the number of characters you want the graph
    to span. The series will be averaged over `width` steps to ensure it fits.
    If the length of the series is not evenly divisible by `width`, the series
    will be padded with the final value to reach the next evenly divisible
    number (this leads to an overly long flat line right at the end of the
    chart).

        >>> print(plot(series, {'width': 30}))

    `format` specifies a Python format string used to format the labels on the
    y-axis. The default value is "{:8.2f} ". This can be used to remove the
    decimal point:

        >>> series = [10,20,30,40,50,40,30,20,10]
        >>> print(plot(series, {'height': 4, 'format':'{:8.0f}'}))
              50 ┤   ╭╮
              40 ┤  ╭╯╰╮
              30 ┤ ╭╯  ╰╮
              20 ┤╭╯    ╰╮
              10 ┼╯      ╰
	"""
    if len(series) == 0 or all(isnan(n) for n in series):
        return ''

    cfg = cfg or {}
    minimum = cfg.get('minimum', min(filter(_isnum, series)))
    maximum = cfg.get('maximum', max(filter(_isnum, series)))
    default_symbols = ['┼', '┤', '╶', '╴', '─', '╰', '╭', '╮', '╯', '│']
    symbols = cfg.get('symbols', default_symbols)

    if minimum > maximum:
        raise ValueError('The minimum value cannot exceed the maximum value.')

    interval = maximum - minimum
    offset = cfg.get('offset', 3)
    height = cfg.get('height', interval)
    ratio = height / interval if interval > 0 else 1

    threshold = cfg.get('threshold', None)
    color = cfg.get('color', ('', ''))
    width = cfg.get('width', None)

    min2 = int(floor(minimum * ratio))
    max2 = int(ceil(maximum * ratio))

    def clamp(n):
        return min(max(n, minimum), maximum)

    def scaled(y):
        return int(round(clamp(y) * ratio) - min2)

    rows = max2 - min2
    width = len(series) + offset
    placeholder = cfg.get('format', '{:8.2f} ')

    result = [[' '] * width for i in range(rows + 1)]

    # axis and labels
    for y in range(min2, max2 + 1):
        label = placeholder.format(maximum - ((y - min2) * interval / (rows if rows else 1)))
        result[y - min2][max(offset - len(label), 0)] = label
        if color:
            if threshold:
                if series[-1] > threshold:
                    result[y - min2][offset - 1] = symbols[0] + color if y == 0 else symbols[1] + color[0]  # zero tick mark
                else:
                    result[y - min2][offset - 1] = symbols[0] + color if y == 0 else symbols[1] + color[1]  # zero tick mark
            else:
                result[y - min2][offset - 1] = symbols[0] + color if y == 0 else symbols[1] + color  # zero tick mark
        else:
            result[y - min2][offset - 1] = symbols[0] if y == 0 else symbols[1]  # zero tick mark

    # first value is a tick mark across the y-axis
    d0 = series[0]
    if _isnum(d0):
        if threshold:
            if series[-1] > threshold:
                result[rows - scaled(d0)][offset - 1] = symbols[0] + color[0]
            else:
                result[rows - scaled(d0)][offset - 1] = symbols[0] + color[1]


    # plot the line

    if width:
        if len(series) % width != 0:
            Q = int(len(series) / width) + 1
            Z = (Q * 30) - len(series)

            series += [series[-1] for i in range(0, Z)]
        else:
            Q = int(lene(y_vals) / 30)
        series = [sum(series[i:i+Q])//Q for i in range(0, len(series), Q)]

    for x in range(len(series) - 1):
        d0 = series[x + 0]
        d1 = series[x + 1]

        if isnan(d0) and isnan(d1):
            continue

        if isnan(d0) and _isnum(d1):
            result[rows - scaled(d1)][x + offset] = symbols[2]
            continue

        if _isnum(d0) and isnan(d1):
            result[rows - scaled(d0)][x + offset] = symbols[3]
            continue

        y0 = scaled(d0)
        y1 = scaled(d1)
        if y0 == y1:
            result[rows - y0][x + offset] = symbols[4]
            continue

        result[rows - y1][x + offset] = symbols[5] if y0 > y1 else symbols[6]
        result[rows - y0][x + offset] = symbols[7] if y0 > y1 else symbols[8]

        start = min(y0, y1) + 1
        end = max(y0, y1)
        for y in range(start, end):
            result[rows - y][x + offset] = symbols[9]


    return '\033[0m\n'.join([''.join(row).rstrip() for row in result])
