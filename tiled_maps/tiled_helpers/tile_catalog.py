from pathlib import Path
import json
from os.path import relpath

from tiled_maps.tiled_helpers.tilemap import TileSetRef, TileSetTileDef
from tiled_maps.tiled_helpers.tileset import TileSet


class TileCatalog:
    tilesets: list[TileSet]

    def __init__(self, tilesets):
        self.tilesets = tilesets
        self._tilenamecache: dict[str, int] = {}

    def dump_references_for_map(self, map_path: Path) -> list[TileSetRef]:
        ret = []
        currentgid = 1
        for ts in self.tilesets:
            cp = relpath(ts.path, map_path.parent)
            ret.append(TileSetRef(firstgid=currentgid, source=cp))
            currentgid += ts.tilecount

        return ret

    def get_tile_by_name(self, name: str) -> int:
        if name in self._tilenamecache:
            return self._tilenamecache[name]
        currentgid = 1
        for ts in self.tilesets:
            if ts.tiles is not None:
                for tile_props in ts.tiles:
                    if any(
                        p["name"] == "name" and p["value"] == name
                        for p in tile_props.properties
                    ):
                        this_gid = currentgid + tile_props.id
                        self._tilenamecache[name] = this_gid
                        return this_gid
            currentgid += ts.tilecount
        raise KeyError(f"Tile {name} not found")


def scan_tileset_folder(folder: Path) -> TileCatalog:
    ret = []
    for p in folder.glob("*.json"):
        with open(p) as fr:
            raw_data = json.load(fr)
        if raw_data.get("type", "") == "tileset":
            if "tiles" in raw_data:
                raw_data["tiles"] = [
                    TileSetTileDef(**tsd)
                    for tsd in raw_data["tiles"]
                    if 'animation' not in tsd
                ]
            ret.append(TileSet(path=str(p), **raw_data))
    return TileCatalog(tilesets=ret)
