from dataclasses import dataclass
from pathlib import Path
import json
from typing import Generator
from tiled_maps.tiled_helpers.tileset import TileSet, TileSetTileDef


@dataclass
class Layer:
    height: int
    width: int
    id: int
    name: str
    type: str
    data: list[int]
    opacity: float = 1.0
    visible: bool = True
    x: int = 0
    y: int = 0

    def tiles_with_coords(self, ignore_zero: bool = True):
        for idx, tid in enumerate(self.data):
            if tid == 0 and ignore_zero:
                continue
            yield ((idx % self.width) - self.x, (idx // self.height) - self.y, tid)

    def set_tile(self, x: int, y: int, tid: int) -> None:
        try:
            self.data[x + y * self.width] = tid
        except IndexError:
            # TODO maybe the caller should handle this?
            print(f"IndexError: {x}, {y}, {tid}")

    def is_empty(self, x, y) -> bool:
        try:
            return self.data[x + y * self.width] == 0
        except IndexError:
            # TODO maybe the caller should handle this?
            return True

    def to_dict(self) -> dict:
        """An object that can be dumped as valid Tiled JSON"""
        ret = {}
        for k, v in self.__dict__.items():
            if type(v) in (str, int, float, bool):
                ret[k] = v
            elif isinstance(v, Path):
                ret[k] = str(v)
            elif k == "data":
                ret[k] = v
            else:
                raise ValueError(f"How to serialize {k} of type {type(v)}?")
        return ret


@dataclass
class TileSetRef:
    firstgid: int
    source: str

    def to_dict(self) -> dict:
        """An object that can be dumped as valid Tiled JSON"""
        return dict(firstgid=self.firstgid, source=self.source)


@dataclass
class TiledMap:
    path: str
    # height as number of tiles
    height: int
    # width as number of tiles
    width: int
    # pixel height of a single tile
    tileheight: int
    # pixel width of a single tile
    tilewidth: int
    layers: list[Layer]
    nextlayerid: int
    nextobjectid: int
    tilesets: list[TileSetRef]
    compressionlevel: int = -1
    infinite: bool = False
    orientation: str = "orthogonal"
    renderorder: str = "right-down"
    tiledversion: str = "1.10.1"
    type: str = "map"
    version: str = "1.10"
    # x, y, name, props
    event_data: list[tuple[int, int, str, dict]] | None = None
    event_files: list[tuple[str, str]] | None = None

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

    def add_event(
        self, x: int, y: int, name: str, props: dict, content: list[str]
    ) -> None:
        """Add an event file to the map"""
        # TODO event content here should be stored with a separate function
        # right now we just assume the name and content are always paired
        if self.event_data is None:
            self.event_data = []
            self.event_files = []
        self.event_data.append((x * self.tilewidth, y * self.tileheight, name, props))
        self.event_files.append((f"{name}.json", json.dumps(content, indent=2)))

    def to_dict(self) -> dict:
        """An object that can be dumped as valid Tiled JSON"""
        ret = {}
        for k, v in self.__dict__.items():
            if type(v) in (str, int, float, bool):
                ret[k] = v
            elif isinstance(v, Path):
                ret[k] = str(v)
            elif k == "layers" and type(v) == list:
                if "layers" not in ret:
                    ret["layers"] = []
                # we don't know if the event layers has been seen before or after
                # so always append
                # hopefully later this can be replaced with a proper Pydantic type
                ret[k] = ret[k] + [l.to_dict() for l in v]
            elif k == "tilesets" and type(v) == list:
                ret[k] = [tsr.to_dict() for tsr in v]
            elif k == "event_data" and type(v) == list:
                if "layers" not in ret:
                    ret["layers"] = []
                ret["layers"].append(
                    {
                        "draworder": "topdown",
                        "id": len(self.layers) + 2,
                        "name": "events",
                        "offsety": 1,
                        "opacity": 1,
                        "type": "objectgroup",
                        "visible": True,
                        "x": 0,
                        "y": 0,
                        "objects": [
                            {
                                "height": 1,
                                "id": idx + 1,
                                "name": name,
                                "properties": [
                                    {
                                        "name": "event_path",
                                        "type": "string",
                                        "value": f"{name}.json",
                                    }
                                ]
                                + [
                                    dict(name=k, type="string", value=v)
                                    for k, v in props.items()
                                ],
                                "rotation": 0,
                                "type": "event",
                                "visible": True,
                                "width": 1,
                                "x": x,
                                "y": y,
                            }
                            for idx, (x, y, name, props) in enumerate(self.event_data)
                        ],
                    }
                )
            elif k == "event_files":
                # these are going to their own files, ignored here
                continue
            elif k == "event_data" and v is None:
                # no events, ignored
                continue
            else:
                raise ValueError(f"How to serialize {k} of type {type(v)}?")
        return ret

    def get_event_files(self) -> Generator[tuple[str, str], None, None]:
        """Yields the event files as pairs of (path, content)"""
        if self.event_files is None:
            return
        for path, content in self.event_files:
            yield path, content


def from_data(data: dict) -> TiledMap:
    parsed_layers = [Layer(**ld) for ld in data["layers"]]
    parsed_tileset_refs = [TileSetRef(**tsrd) for tsrd in data["tilesets"]]
    return TiledMap(
        **data
        | dict(
            layers=parsed_layers,
            tilesets=parsed_tileset_refs,
        ),
    )
