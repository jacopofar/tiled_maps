from os import environ

import psycopg
from psycopg.types import TypeInfo
from psycopg.types.shapely import register_shapely
from tiled_maps.tilemaps import TerrainMap

POSTGIS_CONN_STR = environ["POSTGIS_CONN_STR"]


def get_connection():
    with psycopg.connect(POSTGIS_CONN_STR) as conn:
        info = TypeInfo.fetch(conn, "geometry")
        register_shapely(info, conn)
        yield conn


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
