import ezdxf
import re
from math import cos, sin, tan, atan2, pi
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


def bearing_distance(poly, id, quad, bearing, distance):
    if len(poly) == 0:
        raise ValueError('No initial point set line %s' % id)
    try:
        a = bearing_angle(quad, bearing)
    except ValueError:
        raise ValueError('Bad bearing format line %s: quad=%s bearing=%s' % (id, quad, bearing))
    d = float(distance)
    p0 = np.array(poly[-1][1:3], dtype=np.double)
    p1 = p0 + d * np.array((cos(a), sin(a)), dtype=np.double)
    poly.append([id] + list(p1) + [0.0])



def deflection_distance(poly, id, dir, delta, distance):
    if len(poly) == 0:
        raise ValueError('No initial point set line %s' % id)
    if len(poly) == 1:
        raise ValueError('No back tangent line %s' % id)
    a = dms_angle(delta)
    a *= -1 if dir == 'DL' else +1
    d = float(distance)
    p0 = np.array(poly[-2][1:3], dtype=np.double)
    a0 = poly[-2][3]
    p1 = np.array(poly[-1][1:3], dtype=np.double)

    # Calculate back tangent at p1, chord length
    v = p1 - p0
    t = atan2(v[1], v[0]) + a0 / 2

    p2 = p1 + d * np.array((cos(t + a), sin(t + a)), dtype=np.double)
    poly.append([id] + list(p2) + [0.0])


def delta_radius(poly, id, dir, delta, radius):
    if len(poly) == 0:
        raise ValueError('No initial point set line %s' % id)
    if len(poly) == 1:
        raise ValueError('No back tangent line %s' % id)
    a = dms_angle(delta)
    a *= -1 if dir == 'L' else +1
    r = float(radius)

    p0 = np.array(poly[-2][1:3], dtype=np.double)
    a0 = poly[-2][3]
    p1 = np.array(poly[-1][1:3], dtype=np.double)

    # Calculate back tangent at p1, chord length
    v = p1 - p0
    t = atan2(v[1], v[0]) + a0 / 2
    c = abs(2.0 * r * sin(a / 2.0))

    poly[-1][3] = a
    p2 = p1 + c * np.array((cos(t + a / 2), sin(t + a / 2)), dtype=np.double)
    poly.append([id] + list(p2) + [0.0])


def delta_radius_radial(poly, id, dir, delta, radius, radial_quad, radial_bearing):
    if len(poly) == 0:
        raise ValueError('No initial point set line %s' % id)
    a = dms_angle(delta)
    a *= -1 if dir == 'L' else +1
    r = float(radius)
    try:
        t = bearing_angle(radial_quad, radial_bearing) - copysign(pi/2, a)
    except ValueError:
        raise ValueError('Bad bearing format line %s: quad=%s bearing=%s' % (id, radial_quad, radial_bearing))
    p1 = np.array(poly[-1][1:3], dtype=np.double)
    c = abs(2.0 * r * sin(a / 2.0))
    poly[-1][3] = a
    p2 = p1 + c * np.array((cos(t + a / 2), sin(t + a / 2)), dtype=np.double)
    poly.append([id] + list(p2) + [0.0])


def check_poly(poly):
    if len(poly) == 0:
        raise ValueError('Empty polyline error')
    if len(poly) == 1:
        raise ValueError('Single point polyline error')

    for i in range(1, len(poly)):
        print('\nSegment: %s' % poly[i][0])
        p0 = np.array(poly[i-1][1:3], dtype=np.double)
        print('Begin . . . . .  X: %.3f        Y: %.3f' % (p0[0], p0[1]))
        p1 = np.array(poly[i][1:3], dtype=np.double)
        print('End . . . . . .  X: %.3f        Y: %.3f' % (p1[0], p1[1]))

        d = poly[i-1][3]
        if d == 0:
            # Line segment
            v = p1 - p0
            dist = np.sqrt(np.square(v).sum())
            a = atan2(v[1], v[0])
            print('  Distance: %.3f      Course: %s' % (dist, bearing_string(a)))

        else:
            # Curve segment
            v = p1 - p0
            a = atan2(v[1], v[0])
            c = np.sqrt(np.square(v).sum())
            r = c / 2.0 / sin(d / 2.0)
            l = r * d
            t = r * tan(d / 2.0)
            print('   Tangent: %.3f       Chord: %.3f      Course: %s' % (t, c, bearing_string(a)))
            print('Arc Length: %.3f      Radius: %.3f       Delta: %s' % (l, r, dms_string(d)))

        if i > 1:

            dp = poly[i-2][3]
            if d or dp:
                # Check previous segment is tangent
                vp = p0 - np.array(poly[i-2][1:3], dtype=np.double)
                da = a - d / 2 - atan2(vp[1], vp[0]) - dp / 2
                if round(da, 6):
                    print('\n### Segment %s is not tangent to %s.' % (poly[i][0], poly[i-1][0]))
                    print('### Difference in tangents: %s' % dms_string(da))


def draw_polylines(line_data):

    polylines = []
    pts_stack = []
    for line in line_data:
        line = line.strip()
        if line == '' or line.startswith('#'):
            continue
        params = line.split()

        if params[1] == 'BEGIN':
            # Start a new polyline
            if len(params) != 4:
                raise ValueError('Bad line format: %s' % line)
            polylines.append([params[0:1] + [float(x) for x in params[2:4]] + [0.0]])
        elif params[1] == 'PUSH':
            # Save last point onto the points stack
            if len(polylines) == 0:
                raise ValueError('No point to push: %s' % line)
            pts_stack.append(params[0:1] + polylines[-1][-1][1:3] + [0.0])
        elif params[1] == 'POP':
            # Pop a point from the points stack and start an new polyline
            if len(pts_stack) == 0:
                raise ValueError('No point to pop: %s' % line)
            polylines.append([pts_stack.pop()])
        elif params[1] == 'UNDO':
            # Pop the last point off of the current polyline
            if len(polylines) == 0:
                raise ValueError('No point to undo: %s' % line)
            polylines[-1].pop()
            if len(polylines[-1]) == 0:
                polylines.pop()
        elif params[1] == 'JOIN':
            # Join the last two polylines
            if len(polylines) < 2:
                raise ValueError('Two polylines required for join: %s' % line)
            poly = polylines.pop()
            polylines[-1] += poly
        elif params[1] in '1234':
            # Line segment by bearing/distance
            if len(params) != 4:
                raise ValueError('Bad line format: %s' % line)
            bearing_distance(polylines[-1], *params)
        elif params[1] in 'LR':
            if len(params) == 4:
                # Tangent curve from last segment by delta/radius
                delta_radius(polylines[-1], *params)
            elif len(params) == 6:
                # Non-tangent curve by delta/radius/radial
                delta_radius_radial(polylines[-1], *params)
            else:
                raise ValueError('Bad line format: %s' % line)
        elif params[1] in ('DR', 'DL'):
            # Deflection angle/distance
            if len(params) == 4:
                deflection_distance(polylines[-1], *params)
        else:
            raise ValueError('Bad line format: %s' % line)

    return polylines


def create_dxf(polys, dxf_file):
    dwg = ezdxf.new('R2010')
    dwg.header['$INSUNITS'] = INSUNITS_FOOT
    ms = dwg.modelspace()

    for poly in polys:
        for i in range(len(poly)):
            id, x, y, delta = poly[i]
            if delta != 0:
                poly[i] = [x, y, 0, 0, copysign(tan(delta / 4.0), delta)]
            else:
                poly[i] = [x, y]

        ms.add_lwpolyline(poly)

    dwg.saveas(dxf_file)


if __name__ == '__main__':

    # LINE_DATA = 'data/linedata-pm1241.txt'
    # DXF_FILE = 'data/linedata-pm1241.dxf'
    LINE_DATA = 'data/linedata-demo.txt'
    DXF_FILE = 'data/linedata-demo.dxf'

    # polys = []
    # polys.append([
    #     [6072805.940408997, 1928939.402381297, 0.0],
    #     [6072891.260789272, 1928861.596509992, radians(-27.466666666667)],
    #     [6072949.527734600, 1928774.899767500, 0.0]
    # ])

    line_data = []
    with open(LINE_DATA) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                line_data.append(line)

    polys = draw_polylines(line_data)

    for poly in polys:
        check_poly(poly)

    create_dxf(polys, DXF_FILE)

    # for brg in ('100.0000', '223.4500', '323.0015', '490.0000'):
    #     try:
    #         azi = bearing_angle(brg)
    #         print('%s => %.8f' % (brg, azi))
    #     except ValueError as err:
    #         print(err)