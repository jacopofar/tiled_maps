from copy import deepcopy
import json

from tiled_maps.tilemaps import TerrainMap

RAW_MAP = json.load(open("demo_tilegame2/maps/manual/chunk_0_0.json"))
RAW_MAP["layers"][0]["data"] = []


def terrain_to_tilemap(tm: TerrainMap):
    new_map = deepcopy(RAW_MAP)
    cells = dict()
    for x, y, terrain in tm:
        if terrain == "road":
            cells[(x, y)] = 47
        if terrain == "build":
            cells[(x, y)] = 28

    for y in range(128):
        for x in range(128):
            new_map["layers"][0]["data"].append(cells.get((x, y), 0))
    return new_map
