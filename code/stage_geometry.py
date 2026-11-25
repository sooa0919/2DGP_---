"""Terrain contours traced in the assembled preview's 4096 x 1008 world."""

# Coordinates use the game's bottom-left origin. Trees, grass and rocks in
# object.png are decoration; only the earth/cliff silhouettes are solid.
TERRAIN = (
    ((0, 0), (0, 78), (132, 77), (234, 73), (304, 72), (326, 35),
     (358, 12), (422, 5), (478, 18), (522, 48), (548, 73), (620, 79),
     (716, 77), (748, 89), (790, 87), (790, 0)),
    ((609, 436), (638, 442), (747, 440), (842, 438), (920, 438),
     (949, 430), (943, 407), (922, 385), (916, 270), (923, 127),
     (933, 48), (954, 0), (779, 0), (762, 81), (756, 317),
     (744, 366), (668, 386), (615, 399)),
    ((979, 233), (1000, 241), (1040, 235), (1090, 240), (1112, 232),
     (1101, 205), (1081, 181), (1073, 36), (1091, 0),
     (1006, 0), (1017, 43), (1010, 185), (989, 207)),
    ((1185, 234), (1208, 241), (1255, 235), (1303, 239), (1320, 230),
     (1307, 206), (1286, 180), (1285, 42), (1308, 0),
     (1200, 0), (1218, 50), (1219, 179), (1196, 207)),
    ((1341, 309), (1404, 315), (1470, 308), (1525, 311), (1558, 304),
     (1532, 270), (1512, 196), (1518, 112), (1540, 80), (1620, 64),
     (1620, 0), (1460, 0), (1450, 77), (1434, 234), (1408, 273)),
    ((1520, 0), (1520, 70), (1730, 72), (1920, 70), (2110, 74),
     (2350, 74), (2474, 72), (2492, 48), (2535, 35), (2600, 35),
     (2648, 48), (2667, 69), (2800, 78), (2910, 78), (3080, 74), (3290, 78),
     (3470, 77), (3660, 78), (3785, 73), (3920, 72), (4000, 100),
     (4096, 148), (4096, 0)),
    # Starting overhang at the left edge.
    ((0, 812), (64, 802), (130, 784), (161, 755), (196, 743),
     (235, 698), (275, 670), (288, 651), (241, 637), (125, 640), (0, 650)),
    # Central tree: lower branch, upper branch, and the trunk above them.
    ((2520, 449), (2537, 532), (2577, 612), (2668, 601), (2764, 578),
     (2855, 581), (2951, 619), (3032, 604), (3091, 602), (3138, 626),
     (3170, 669), (3162, 714), (3107, 741), (3045, 762), (2921, 783),
     (2851, 758), (2826, 757), (2828, 787), (2861, 826), (2970, 831),
     (3068, 840), (3092, 902), (3067, 972), (3054, 1008), (3310, 1008),
     (3280, 898), (3254, 795), (3250, 690), (3344, 625), (3335, 500),
     (3316, 484), (3190, 480), (3090, 489), (2886, 482), (2710, 478),
     (2611, 473), (2542, 445)),
    # Final right-hand ledge and its lower, curved support.
    ((3653, 817), (3700, 827), (3860, 828), (4000, 828), (4096, 826),
     (4096, 0), (4000, 75), (4033, 187), (4047, 293), (4035, 405),
     (4000, 507), (3918, 536), (3821, 539), (3778, 585), (3760, 664),
     (3687, 711), (3656, 754)),
)


def collision_rectangles(step=4, polygons=TERRAIN):
    """Represent polygon interiors by narrow vertical spans, including undersides."""
    from .level import Platform
    rectangles = []
    for polygon in polygons:
        first = int(min(x for x, _ in polygon)) // step * step
        last = int(max(x for x, _ in polygon))
        previous = {}
        for left in range(first, last, step):
            right = min(left + step, last)
            x = (left + right) / 2
            crossings = []
            for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
                if min(x1, x2) <= x < max(x1, x2):
                    crossings.append(y1 + (y2 - y1) * (x - x1) / (x2 - x1))
            crossings.sort()
            current = {}
            for bottom, top in zip(crossings[::2], crossings[1::2]):
                bounds = (round(bottom), round(top))
                if bounds[1] <= bounds[0]:
                    continue
                old = previous.get(bounds)
                if old is not None and rectangles[old].right == left:
                    p = rectangles[old]
                    rectangles[old] = Platform(p.left, p.bottom, right, p.top)
                    current[bounds] = old
                else:
                    current[bounds] = len(rectangles)
                    rectangles.append(Platform(left, bounds[0], right, bounds[1]))
            previous = current
    return rectangles


def terrain_collision_rectangles():
    """Use the tile's measured central-tree shape instead of its old outline."""
    import json
    from .level import Platform
    from .settings import IMAGE_ROOT
    rectangles = collision_rectangles(polygons=tuple(p for i, p in enumerate(TERRAIN) if i != 7))
    path = IMAGE_ROOT / 'background/stage1/central_tree_collision.json'
    rectangles.extend(Platform(*bounds) for bounds in json.loads(path.read_text(encoding='utf-8')))
    return rectangles
