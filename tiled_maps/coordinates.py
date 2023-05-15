from math import atan, sinh, pi, degrees


def tile_bounds(x: int, y: int, zoom: int):
    # zoom factor
    n = 2**zoom
    # longitude is a simple division of the circle
    # TODO extra pairs are calculated in case this tile "wraps"
    # and goes over the international date line and/or the poles
    lon1 = x / n * 360.0 - 180.0
    lon2 = (x + 1) / n * 360.0 - 180.0
    lon3 = (x + 1) / n * 360.0 - 180.0
    lon4 = x / n * 360.0 - 180.0

    # latitude is more complex, Mercator is distorted because
    # it projects over a cylinder
    # there's a thing called "Gudermannian function" to calculate
    # this distortion, that's why there are sinh here
    lat1 = atan(sinh(pi * (1 - 2 * y / n)))
    lat1 = degrees(lat1)

    lat2 = atan(sinh(pi * (1 - 2 * (y + 1) / n)))
    lat2 = degrees(lat2)

    lat3 = atan(sinh(pi * (1 - 2 * y / n)))
    lat3 = degrees(lat3)

    lat4 = atan(sinh(pi * (1 - 2 * (y + 1) / n)))
    lat4 = degrees(lat4)

    north = max(lat1, lat2, lat3, lat4)
    south = min(lat1, lat2, lat3, lat4)
    east = max(lon1, lon2, lon3, lon4)
    west = min(lon1, lon2, lon3, lon4)

    return (north, south, east, west)


if __name__ == "__main__":
    # TMS coordinates of the La Scala opera house
    # note that they differ from Google ones since
    # the Y axis here grows going north, Google does the
    # opposite and folows the computer graphics convention
    # rather than the cartesian convention for the Y axis

    print(tile_bounds(137763, 168327, 18))
