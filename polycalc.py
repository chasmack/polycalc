import ezdxf
import re
import io
from math import cos, sin, tan, atan2, hypot, pi
from math import degrees, radians, copysign, isclose
import numpy as np

INSUNITS_FOOT = 2
INSUNITS_METER = 6


def dms_angle(dms):
    # Convert a signed (clockwise positive) DMS string ('ddd.mm.ss')
    # to an angle (couterclockwise positive) in radians.
    m = re.fullmatch('(-)?(\d{1,3})\.(\d{2})(\d{2})', dms)
    if not m:
        raise ValueError
    deg, min, sec = map(int, m.groups()[1:])
    sign = m.group(1)
    if deg >= 360 or min >= 60 or sec >= 60:
        raise ValueError
    deg += min / 60 + sec / 3600
    if sign == '-':
        deg *= -1
    return radians(-deg)


def bearing_angle(quad, brg):
    # Convert DMS bearing string ('qdd.mmss') to an angle
    # (counterclockwise from positive x-axis) in radians.
    m = re.fullmatch('(\d{1,2})\.(\d{2})(\d{2})', brg)
    if not m:
        raise ValueError
    deg, min, sec = map(int, m.groups())
    if deg > 90 or min >= 60 or sec >= 60:
        raise ValueError
    deg += min / 60 + sec / 3600
    quad = int(quad)
    if quad % 2:
        a = radians((2 - quad) * 90 - deg)  # quadrants 1 and 3
    else:
        a = radians((1 - quad) * 90 + deg)  # quadrants 2 and 4
    return a


def bearing_string(a, sec_decimals=1):
    azi = (90 - degrees(a)) % 360
    quad = int(azi // 90)
    if quad % 2:
        deg = 90 - (azi % 90)
    else:
        deg = azi % 90

    min = (deg * 60) % 60
    sec = (min * 60) % 60
    deg = round(deg - min / 60)
    min = round(min - sec / 60)
    sec = round(sec, sec_decimals)
    if isclose(sec, 60.0, abs_tol=(0.1 ** sec_decimals)):
        sec = 0.0
        min += 1
    if min == 60:
        min = 0
        deg += 1
    quad = ('NE','SE','SW','NW')[quad]
    format = '%s%d°%02d\'%0' + str(sec_decimals + 3) + '.' + str(sec_decimals) + 'f"%s'
    return format % (quad[0], deg, min, sec, quad[1])


def dms_string(a, sec_decimals=1):
    sign = -1 if a < 0 else +1
    deg = degrees(sign * a)
    min = (deg * 60) % 60
    sec = (min * 60) % 60
    deg = round(deg - min / 60)
    min = round(min - sec / 60)
    sec = round(sec, sec_decimals)
    if isclose(sec, 60.0, abs_tol=(0.1 ** sec_decimals)):
        sec = 0.0
        min += 1
    if min == 60:
        min = 0
        deg += 1
    format = '%s%d°%02d\'%0' + str(sec_decimals + 3) + '.' + str(sec_decimals) + 'f"'
    return format % ('' if sign < 0 else '-', deg, min, sec)


def check_tangency(poly):
    if len(poly) < 3:
        raise ValueError('Tangency check requires two segments')

    p0 = np.array(poly[-3][0:2], dtype=np.double)
    d0 = poly[-3][2]
    p1 = np.array(poly[-2][0:2], dtype=np.double)
    d1 = poly[-2][2]
    p2 = np.array(poly[-1][0:2], dtype=np.double)

    v1 = p1 - p0
    t1 = atan2(v1[1], v1[0]) + d0 / 2
    v2 = p2 - p1
    t2 = atan2(v2[1], v2[0]) + d1 / 2
    dt = t2 - t1

    resp = []
    if round(dt, 6):
        resp.append('### Segment is not tangent.')
        resp.append('### Difference in tangents: %s' % dms_string(dt))
        resp.append('')

    return resp


def process_line_data(f):

    # Create a list of line commands removing comments
    line_data = []
    for line in f:
        line = line.decode(encoding="utf-8").strip()
        if line == '' or line.startswith('#'):
            continue
        line_data.append(line)

    listing = []
    polylines = []
    points = {}

    for i, line in enumerate(line_data):

        params = line.split()
        if len(params) < 2:
            raise ValueError('Bad line format: %s' % line)
        id = params.pop(0)
        cmd = params.pop(0)

        if cmd == 'BEGIN':
            # Start a new polyline
            if len(params) != 2:
                raise ValueError('Bad line format: %s' % line)
            try:
                n, e = map(float, params)
            except Exception as e:
                raise ValueError('Bad x/y coordinate: %s' % line)
            pt = [e, n, 0.0]
            polylines.append([pt])
            listing.append('%s - Begin polyline' % id)
            listing.append('  From N: %-14.3f     E: %.3f' % (n, e))
            listing.append('')

        elif cmd == 'BRANCH':
            # Begin a new polyline from the last point
            if len(params) != 0:
                raise ValueError('Bad line format: %s' % line)
            if len(polylines) == 0:
                raise ValueError('No polyline to branch: %s' % line)

            polylines.append([polylines[-1][-1].copy()])
            x, y = polylines[-1][-1][0:2]
            listing.append('%s - Branch polyline' % id)
            listing.append('  From N: %-14.3f     E: %.3f' % (y, x))
            listing.append('')

        elif cmd == 'RESUME':
            # Move the current polyline to the bottom of the polyline list
            if len(params) != 0:
                raise ValueError('Bad line format: %s' % line)
            if len(polylines) < 2:
                raise ValueError('Need two polylines to swap: %s' % line)

            polylines.insert(0, polylines.pop())
            x, y = polylines[-1][-1][0:2]
            listing.append('%s - Resume polyline' % id)
            listing.append('  From N: %-14.3f     E: %.3f' % (y, x))
            listing.append('')

        elif cmd == 'STORE':
            # Save coordinates of the last point in the polyline to the points list
            if len(params) == 0:
                if len(polylines) == 0:
                    raise ValueError('No point to store: %s' % line)
                points[id] = polylines[-1][-1].copy()
            elif len(params) == 2:
                try:
                    n, e = map(float, params)
                except ValueError:
                    raise ValueError('Bad point coordinates: %s' % line)
                points[id] = [e, n, 0.0]
            else:
                raise ValueError('Bad line format: %s' % line)

        elif cmd == 'RECALL':
            # Recall a point from the points list and start an new polyline
            if len(params) != 0:
                raise ValueError('Bad line format: %s' % line)
            if id not in points:
                raise ValueError('Point not found: %s' % line)
            polylines.append([points[id].copy()])
            x, y = polylines[-1][-1][0:2]
            listing.append('%s - Begin polyline' % id)
            listing.append('  From N: %-14.3f     E: %.3f' % (y, x))
            listing.append('')

        elif cmd == 'CLOSE':
            # Calculate closure between last point and a point in the points list.
            if len(params) != 0:
                raise ValueError('Bad line format: %s' % line)
            if len(polylines) == 0:
                raise ValueError('No polyline to close to: %s' % line)
            if id not in points:
                raise ValueError('Point not found: %s' % line)
            p0 = np.array(polylines[-1][-1][0:2], dtype=np.double)
            p1 = np.array(points[id][0:2], dtype=np.double)
            v = p1 - p0
            a = atan2(v[1], v[0])
            d = hypot(v[1], v[0])
            listing.append('%s - Closure' % id)
            listing.append('  From N: %-14.3f     E: %.3f' % (p0[1], p0[0]))
            listing.append('  To   N: %-14.3f     E: %.3f' % (p1[1], p1[0]))
            listing.append('  Distance: %-10.3f       Course: %s' % (d, bearing_string(a)))
            listing.append('')

        elif cmd == 'UNDO':
            # Pop the last point off of the current polyline
            if len(polylines) == 0:
                raise ValueError('No point to undo: %s' % line)
            polylines[-1].pop()
            if len(polylines[-1]) == 0:
                polylines.pop()
                listing.append('%s - Delete polyline' % id)
            else:
                polylines[-1][-1][-1] = 0.0
                listing.append('%s - Delete segment' % id)
            listing.append('')

        # elif cmd == 'JOIN':
        #     # Join the last two polylines
        #     if len(polylines) < 2:
        #         raise ValueError('Two polylines required for join: %s' % line)
        #     poly = polylines.pop()
        #     polylines[-1] += poly

        elif cmd in '1234':
            # Line segment by bearing/distance
            if len(params) != 2:
                raise ValueError('Bad line format: %s' % line)
            bearing, distance = params
            quad = cmd
            if len(polylines) == 0:
                raise ValueError('No initial point: %s' % line)
            poly = polylines[-1]
            try:
                a = bearing_angle(quad, bearing)
                d = float(distance)
            except Exception:
                raise ValueError('Bad bearing/distance: %s' % line)

            p0 = np.array(poly[-1], dtype=np.double)
            p1 = p0 + d * np.array((cos(a), sin(a), 0), dtype=np.double)
            poly.append(list(p1))

            x, y = polylines[-1][-1][0:2]
            listing.append('%s - Line to %s' % (id, ('NE','SE','SW','NW')[int(quad) - 1]))
            listing.append('  To N: %-14.3f       E: %.3f' % (y, x))
            listing.append('  Distance: %-10.3f       Course: %s' % (d, bearing_string(a)))
            listing.append('')

            if len(poly) > 2 and polylines[-1][-3][2]:
                # Previous segment was a curve
                listing += check_tangency(poly)

        elif cmd in 'LR':
            if len(params) < 2:
                raise ValueError('Bad line format: %s' % line)
            delta, radius = params[0:2]
            try:
                a = dms_angle(delta)
                a *= -1 if cmd == 'L' else +1
                r = float(radius)
            except Exception:
                raise ValueError('Bad delta/radius: %s' % line)

            if len(polylines) == 0:
                raise ValueError('No initial point: %s' % line)
            poly = polylines[-1]
            p1 = np.array(poly[-1], dtype=np.double)

            # Calculate bearing of back tangent
            if len(params) == 2:
                # Tangent curve
                if len(poly) < 2:
                    raise ValueError('No back tangent: %s' % line)
                p0 = np.array(poly[-2], dtype=np.double)
                v = p1 - p0
                t = atan2(v[1], v[0]) - v[2] / 2

                listing.append('%s - Tangent curve to %s' % (id, 'Right' if a < 0 else 'Left'))

            elif len(params) == 4:
                # Non-tangent curve with radial
                quad, bearing = params[2:4]
                try:
                    t = bearing_angle(quad, bearing) - copysign(pi / 2, a)
                except ValueError:
                    raise ValueError('Bad quadrant/bearing: %s' % line)

                listing.append('%s - Non-Tangent curve to %s' % (id, 'Right' if a < 0 else 'Left'))

            else:
                raise ValueError('Bad line format: %s' % line)

            c = abs(2.0 * r * sin(a / 2.0))

            p2 = p1 + c * np.array((cos(t + a / 2), sin(t + a / 2), 0), dtype=np.double)

            polylines[-1].append(list(p2))
            polylines[-1][-2][-1] = a

            x, y = polylines[-1][-1][0:2]
            delta = -1 * abs(polylines[-1][-2][-1])
            arc_len = -1 * r * delta
            tan_len = -1 * r * tan(delta / 2)
            listing.append('  To N: %-14.3f       E: %.3f' % (y, x))
            listing.append('  Tangent: %-10.3f        Chord:  %-10.3f     Course: %s' % (tan_len, c, bearing_string(t + a / 2)))
            listing.append('  Arc Len: %-10.3f        Radius: %-10.3f     Delta:  %s' % (arc_len, r, dms_string(delta)))
            listing.append('')


        elif cmd in ('DR', 'DL'):
            # Deflection angle/distance
            if len(params) != 2:
                raise ValueError('Bad line format: %s' % line)
            delta, distance = params[0:2]
            try:
                a = dms_angle(delta)
                a *= -1 if cmd == 'DL' else +1
                d = float(distance)
            except Exception:
                raise ValueError('Bad deflection/distance: %s' % line)

            if len(polylines) == 0:
                raise ValueError('No initial point: %s' % line)
            poly = polylines[-1]
            if len(poly) < 2:
                raise ValueError('No back tangent line: %s' % line)

            p0 = np.array(poly[-2], dtype=np.double)
            p1 = np.array(poly[-1], dtype=np.double)

            # Calculate back tangent at p1, chord length
            v = p1 - p0
            t = atan2(v[1], v[0]) - v[2] / 2

            p2 = p1 + d * np.array((cos(t + a), sin(t + a), 0.0), dtype=np.double)
            polylines[-1].append(list(p2))

            x, y = polylines[-1][-1][0:2]
            listing.append('%s - Line to %s' % (id, ('NE', 'SE', 'SW', 'NW')[int(quad) - 1]))
            listing.append('  To N: %-14.3f       E: %.3f' % (y, x))
            listing.append('  Distance: %-10.3f       Course: %s' % (d, bearing_string(t + a)))
            listing.append('')


        else:
            raise ValueError('Bad line format: %s' % line)

    dwg = ezdxf.new('R2010')
    dwg.header['$INSUNITS'] = INSUNITS_FOOT
    ms = dwg.modelspace()

    for poly in polylines:
        for i, (x, y, delta) in enumerate(poly):
            if delta != 0:
                poly[i][2:] = [0, 0, copysign(tan(delta / 4.0), delta)]
            else:
                poly[i].pop()
        ms.add_lwpolyline(poly)

    with io.StringIO() as f:
        dwg.write(f)
        dxf = f.getvalue()

    return dxf, listing


if __name__ == '__main__':

    LINE_DATA = 'data/linedata-deerfield.txt'
    DXF_FILE = 'data/linedata-deerfield.dxf'
    LST_FILE = 'data/linedata-deerfield.lst'
    # LINE_DATA = 'data/linedata-alderpoint.txt'
    # DXF_FILE = 'data/linedata-alderpoint.dxf'
    # LST_FILE = 'data/linedata-alderpoint.lst'
    # LINE_DATA = 'data/linedata-demo.txt'
    # DXF_FILE = 'data/linedata-demo.dxf'
    # LST_FILE = 'data/linedata-demo.lst'

    with open(LINE_DATA, 'rb') as f:
        dxf, listing = process_line_data(f)

    with open(LST_FILE, 'w') as f:
        f.write('\n'.join(listing))

    with open(DXF_FILE, 'w') as f:
        f.write(dxf)

    # for brg in ('100.0000', '223.4500', '323.0015', '490.0000'):
    #     try:
    #         azi = bearing_angle(brg)
    #         print('%s => %.8f' % (brg, azi))
    #     except ValueError as err:
    #         print(err)