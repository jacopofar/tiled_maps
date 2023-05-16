from copy import deepcopy
import json
from pathlib import Path

TerrainMap = list[tuple[int, int, str]]

RAW_MAP = json.load(open("demo_tilegame2/maps/manual/chunk_0_0.json"))
RAW_MAP["layers"][0]["data"] = []


def get_cells_ids():
    cell_ids = {}
    for ts in RAW_MAP["tilesets"]:
        base_gid = ts["firstgid"]
        print(f"processing tileset {ts['source']}")
        # TODO nicer and safer Path check?
        # brutal concatenation to comply with Tiled paths
        with open("demo_tilegame2/maps/manual/" + ts["source"]) as fr:
            ts_data = json.load(fr)
            for tile in ts_data.get("tiles", []):
                for prp in tile.get("properties", []):
                    if prp["name"] == "name":
                        this_tile_name = prp["value"]
                        this_tile_id = base_gid + tile["id"]
                        print(f"Tile {this_tile_name} has id {this_tile_id}")
                        cell_ids[this_tile_name] = this_tile_id
    return cell_ids


def terrain_to_tilemap(tm: TerrainMap):
    new_map = deepcopy(RAW_MAP)
    tiles_ids_mapping = get_cells_ids()
    cells = dict()
    for x, y, terrain in tm:
        if terrain == "road":
            cells[(x, y)] = tiles_ids_mapping["dirt_a"]
        if terrain == "build":
            cells[(x, y)] = tiles_ids_mapping["wall_bright"]
        if terrain == "park":
            cells[(x, y)] = tiles_ids_mapping["park_a"]

    for y in range(128):
        for x in range(128):
            new_map["layers"][0]["data"].append(cells.get((x, y), 0))
    return new_map
