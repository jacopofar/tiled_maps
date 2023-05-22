from os import environ
from typing import Generator
import json

import psycopg
from psycopg.types import TypeInfo
from psycopg.types.shapely import register_shapely
from shapely.geometry import shape
from shapely import prepare

from tiled_maps.dumb_generator import TerrainMap

POSTGIS_CONN_STR = environ["POSTGIS_CONN_STR"]


def get_connection():
    with psycopg.connect(POSTGIS_CONN_STR) as conn:
        info = TypeInfo.fetch(conn, "geometry")
        register_shapely(info, conn)
        yield conn


def retrieve_features(
    x: int, y: int, z: int, conn: psycopg.Connection, swap_z: bool = False, prepare_geometries: bool = False
) -> Generator[tuple[int, shape, dict], None, None]:
    # depending on the service, tile Y is swapped
    y_clause = "%(y)s"
    if swap_z:
        y_clause = f"(2 ^ %(z)s - %(y)s)::integer"
    tables = ["building_polygon", "road_line", "water_polygon"]

    results = conn.execute(
        """
    UNION ALL
    """.join(
            [
                f"""
        SELECT
            gdata.osm_id AS osm_id,
            gdata.geom AS geom,
            tags.tags AS tags
        FROM
            osm.{tname} gdata
                LEFT JOIN osm.tags tags ON tags.osm_id = ABS(gdata.osm_id)
        WHERE
                geom &&
                st_tileenvelope(%(z)s, %(x)s, {y_clause})
        """
                for tname in tables
            ]
        ),
        dict(z=z, x=x, y=y),
    )
    for row in results:
        osm_id, geom, tags = row
        # some test shows this brings no benefits here
        # probably each geometry is accessed only once and they are
        # pretty simple
        if prepare_geometries:
            prepare(geom)
        yield osm_id, geom, tags


def cell_bbox(
    x: int, y: int, z: int, tiles: int, conn: psycopg.Connection, swap_z: bool = False
) -> tuple[float, float, float, float]:
    y_clause = "%(y)s"
    # depending on the service, tile Y is swapped
    if swap_z:
        y_clause = f"(2 ^ %(z)s - %(y)s)::integer"
    extent = json.loads(
        conn.execute(
            f"""
        select st_asgeojson(st_tileenvelope(%(z)s, %(x)s, {y_clause}))
        """,
            dict(z=z, x=x, y=y),
        ).fetchone()[0]
    )
    # must be EPSG 3857
    assert extent["crs"]["properties"]["name"] == "EPSG:3857"
    # last coordinate is repeated
    coords = [tuple(t) for t in extent["coordinates"][0][:3]]
    min_x = min(x for (x, _) in coords)
    max_x = max(x for (x, _) in coords)
    min_y = min(y for (_, y) in coords)
    max_y = max(y for (_, y) in coords)
    return (min_x, max_x, min_y, max_y)


def tile_to_terrainmap(
    x: int,
    y: int,
    z: int,
    conn: psycopg.Connection,
    tiles: int = 32,
    swap_z: bool = False,
) -> TerrainMap:
    y_clause = "%(y)s"
    # depending on the service, tile Y is swapped
    if swap_z:
        y_clause = f"(2 ^ %(z)s - %(y)s)::integer"
    results = conn.execute(
        f"""
            with
                needed_resolution as (
                    select sqrt(st_area(ST_TileEnvelope(%(z)s, %(x)s, {y_clause}))) / %(tiles)s as v
                ),
                grid(geom, x, y) AS (
                    SELECT (
                        ST_SquareGrid(needed_resolution.v,
                        ST_TileEnvelope(%(z)s, %(x)s, {y_clause}))).*
                        from needed_resolution
                ),
                index_bounds as (
                    select min(x) as minx, min(y) as miny from grid
                ),
                cells_with_roads as (select distinct 'road' as name, g.x, g.y
                          from grid g,
                               osm.road_line rl
                          where st_intersects(g.geom, rl.geom)),
                cells_with_buildings as (select distinct 'build' as name, g.x, g.y
                                    from grid g,
                                        osm.building_polygon bp
                                    where st_intersects(g.geom, bp.geom)),
                cells_with_parks as (select distinct 'park' as name, g.x, g.y
                                    from grid g,
                                        osm.leisure_polygon lp
                                    where st_intersects(g.geom, lp.geom)
                                        and lp.osm_type = 'park'
                                    ),
                all_relevant_cells as (
                    select name, x, y from cells_with_roads
                                    union all
                    select name, x, y from cells_with_buildings
                                    union all
                    select name, x, y from cells_with_parks
                )
            select x - minx as x, %(tiles)s - y + miny as y, name
            from all_relevant_cells,
                index_bounds
            where x - minx < %(tiles)s and y - miny <= %(tiles)s
        """,
        dict(z=z, x=x, y=y, tiles=tiles),
    ).fetchall()
    ret: TerrainMap = []
    for row in results:
        ret.append(tuple(row))
    return ret
