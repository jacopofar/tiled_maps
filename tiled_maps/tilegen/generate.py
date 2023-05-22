from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import psycopg
from shapely.geometry import shape, box

from tiled_maps.tiled_helpers.tilemap import TiledMap, Layer
from tiled_maps.tiled_helpers.tile_catalog import scan_tileset_folder, TileCatalog

from tiled_maps.database import retrieve_features, cell_bbox


@dataclass
class TiledRepresentation:
    ground: dict[tuple[int, int], int]
    meter1: dict[tuple[int, int], int]


def get_covered_points(
    tile_bbox: tuple[float, float, float, float],
    geom_bbox: tuple[float, float, float, float],
    cell_width: float,
    cell_height: float,
) -> Generator[tuple[int, int, box], None, None]:
    min_x, max_x, min_y, max_y = tile_bbox
    g_min_x, g_min_y, g_max_x, g_max_y = geom_bbox
    cur_y = max(g_min_y, min_y)
    while cur_y < min(max_y, g_max_y):
        cur_x = max(g_min_x, min_x)
        while cur_x < min(max_x, g_max_x):
            if cur_x > min_x and cur_y > min_y:
                yield (
                    int((cur_x - min_x) / cell_width),
                    # NOTE: y coordinate uses computer graphic convention,
                    # not cartesian
                    int((max_y - cur_y) / cell_height),
                    box(cur_x, cur_y, cur_x + cell_width, cur_y + cell_height),
                )
            cur_x += cell_width
        cur_y += cell_height


def represent_feature(
    osm_id: int,
    geom: shape,
    tags: dict,
    catalog: TileCatalog,
    bbox: tuple[float, float, float, float],
    cell_width: float,
    cell_height: float,
) -> TiledRepresentation | None:
    if "building" in tags:
        tr = TiledRepresentation(ground={}, meter1={})
        for x, y, p in get_covered_points(bbox, geom.bounds, cell_width, cell_height):
            if p.intersects(geom):
                tr.ground[(x, y)] = catalog.get_tile_by_name("wall_bright")
        return tr
    elif tags.get("highway") == "footway":
        tr = TiledRepresentation(ground={}, meter1={})
        for x, y, p in get_covered_points(bbox, geom.bounds, cell_width, cell_height):
            if p.intersects(geom):
                tr.ground[(x, y)] = catalog.get_tile_by_name("dirt_a")
        return tr
    elif tags.get("natural") == "water":
        tr = TiledRepresentation(ground={}, meter1={})
        for x, y, p in get_covered_points(bbox, geom.bounds, cell_width, cell_height):
            if p.intersects(geom):
                tr.ground[(x, y)] = catalog.get_tile_by_name("water_a")
        return tr
    else:
        return None


def generate_map(
    path: str, x: int, y: int, z: int, conn: psycopg.Connection, tiles: int
) -> TiledMap:
    catalog = scan_tileset_folder(Path("demo_tilegame2/spritesheets/"))
    layers = [
        Layer(
            height=tiles,
            width=tiles,
            id=1,
            name="ground",
            type="tilelayer",
            data=[0] * (tiles**2),
        ),
        Layer(
            height=tiles,
            width=tiles,
            id=2,
            name="meter1",
            type="tilelayer",
            data=[0] * (tiles**2),
        ),
    ]
    new_map = TiledMap(
        path=path,
        height=tiles,
        width=tiles,
        tileheight=32,
        tilewidth=32,
        layers=layers,
        nextobjectid=1,
        nextlayerid=len(layers) + 1,
        tilesets=catalog.dump_references_for_map(path),
    )
    bbox = cell_bbox(x, y, z, tiles, conn)
    min_x, max_x, min_y, max_y = bbox
    cell_width = (max_x - min_x) / tiles
    cell_height = (max_y - min_y) / tiles
    for osm_id, geom, tags in retrieve_features(x, y, z, conn):
        new_feat = represent_feature(
            osm_id, geom, tags, catalog, bbox, cell_width, cell_height
        )
        if new_feat is not None:
            for (x, y), tid in new_feat.ground.items():
                new_map.layers[0].set_tile(x, y, tid)
            for (x, y), tid in new_feat.meter1.items():
                new_map.layers[1].set_tile(x, y, tid)
    return new_map