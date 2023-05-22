from dataclasses import dataclass


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
    wangsets: list[dict] = None
    tiles: list[TileSetTileDef] | None = None
