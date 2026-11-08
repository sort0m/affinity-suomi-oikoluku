"""Generate a small original checkmark ICO using only the standard library."""
from pathlib import Path
import math
import struct


def make_icon(target):
    images = []
    for size in (16, 32, 48):
        pixels = bytearray()
        def distance(x, y, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0, min(1, ((x-a[0])*dx + (y-a[1])*dy)/(dx*dx+dy*dy)))
            return math.hypot(x-a[0]-t*dx, y-a[1]-t*dy)
        for y in reversed(range(size)):
            for x in range(size):
                px, py = (x + .5) / size, (y + .5) / size
                inside = math.hypot(px-.5, py-.5) < .47
                check = min(distance(px, py, (.25, .50), (.43, .68)),
                            distance(px, py, (.43, .68), (.77, .32))) < .06
                pixels.extend((255, 255, 255, 255) if inside and check else
                              (119, 118, 15, 255) if inside else (0, 0, 0, 0))
        mask = bytes(((size + 31) // 32) * 4 * size)
        header = struct.pack('<IiiHHIIiiII', 40, size, size*2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
        images.append((size, header + pixels + mask))
    result = bytearray(struct.pack('<HHH', 0, 1, len(images)))
    offset = 6 + 16*len(images)
    for size, data in images:
        result.extend(struct.pack('<BBBBHHII', size, size, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for _, data in images:
        result.extend(data)
    Path(target).write_bytes(result)
