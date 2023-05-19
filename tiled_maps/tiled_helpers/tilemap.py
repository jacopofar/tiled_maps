from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class TileSetTileDef:
    id: int
    properties: list[dict]


@dataclass
class TileSet:
    columns: int
    image: str
    imageheight: int
    imagewidth: int
    margin: int
    name: str
    spacing: int
    tilecount: int
    tiledversion: str
    tileheight: int
    tilewidth: int
    type: str
    version: str
    path: str
    tiles: list[TileSetTileDef] | None = None


@dataclass
class Layer:
    height: int
    width: int
    id: int
    name: str
    opacity: float
    type: str
    visible: bool
    x: int
    y: int
    data: list[int]

    def tiles_with_coords(self, ignore_zero: bool = True):
        for idx, tid in enumerate(self.data):
            if tid == 0 and ignore_zero:
                continue
            yield ((idx % self.width) - self.x, (idx // self.height) - self.y, tid)


@dataclass
class TileSetRef:
    firstgid: int
    source: str


@dataclass
class TiledMap:
    path: str
    compressionlevel: int
    # height as number of tiles
    height: int
    # width as number of tiles
    width: int
    # pixel height of a single tile
    tileheight: int
    # pixel width of a single tile
    tilewidth: int
    infinite: bool
    layers: list[Layer]
    nextlayerid: int
    nextobjectid: int
    orientation: str
    renderorder: str
    tiledversion: str
    tilesets: list[TileSetRef]
    type: str
    version: str

    def resolve_tileset(self, tsr: TileSetRef) -> TileSet:
        """Fetches the actual tileset from the reference in the map."""
        # TODO cache this
        # TODO create helpers to handle paths according to Tiled logic
        with open(Path(self.path).parent / tsr.source) as tr:
            tileset_data = json.load(tr)
            if "tiles" in tileset_data:
                tileset_data["tiles"] = [
                    TileSetTileDef(**tsd) for tsd in tileset_data["tiles"]
                ]
            return TileSet(
                path=str(Path(self.path).parent / tsr.source), **tileset_data
            )

    def get_static_tile_id_bounds(self, tid: int):
        """Get the image path and bounds of a tile id"""
        for tsr in self.tilesets:
            if tsr.firstgid <= tid:
                ts = self.resolve_tileset(tsr)
                if ts.tilecount + tsr.firstgid <= tid:
                    continue
                local_id = tid - tsr.firstgid
                return (
                    Path(ts.path).parent / ts.image,
                    ts.tilewidth * (local_id % (ts.imagewidth / ts.tilewidth)),
                    ts.tileheight * (local_id // (ts.imagewidth / ts.tilewidth)),
                    ts.tilewidth,
                    ts.tileheight,
                )
        raise KeyError(f"No tiles found for {tid}")


def from_data(path: str, data: dict) -> TiledMap:
    parsed_layers = [Layer(**ld) for ld in data["layers"]]
    parsed_tileset_refs = [TileSetRef(**tsrd) for tsrd in data["tilesets"]]
    data: TiledMap = TiledMap(
        path=path,
        **data
        | dict(
            layers=parsed_layers,
            tilesets=parsed_tileset_refs,
        ),
    )
    return data
