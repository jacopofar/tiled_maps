from io import BytesIO
import json
from pathlib import Path
import mimetypes
import re
from os import environ

from tiled_maps.database import get_connection
from tiled_maps.raster import render_tilemap
from tiled_maps.tilegen import generate


from fastapi import FastAPI, HTTPException
from fastapi import Depends
from fastapi.responses import Response


app = FastAPI()

CHUNK_REGEX = re.compile(r".+chunk_(-?\d+)_(-?\d+).json")
WORLD_CENTER_X = int(environ["WORLD_CENTER_X"])
WORLD_CENTER_Y = int(environ["WORLD_CENTER_Y"])
GAME_ZOOM_LEVEL = int(environ["GAME_ZOOM_LEVEL"])
TILE_RESOLUTION = int(environ["TILE_RESOLUTION"])
CELL_PIXEL_SIZE = int(environ["CELL_PIXEL_SIZE"])


@app.get("/maps/generated/world.world")
def get_world_file():
    game_world_data = {
        "patterns": [
            {
                "regexp": "chunk_(\\-?\\d+)_(\\-?\\d+)\\.json",
                "multiplierX": TILE_RESOLUTION * CELL_PIXEL_SIZE,
                "multiplierY": TILE_RESOLUTION * CELL_PIXEL_SIZE,
                "offsetX": 0,
                "offsetY": 0,
            }
        ],
        "type": "world",
    }
    with open("demo_tilegame2/maps/generated/world.world", "w") as fw:
        json.dump(game_world_data, fw, indent=2)
    return game_world_data


@app.get("/zxy_gamified/{z}/{x}/{y}.{ext}")
def generate_raster_tile(
    z: int, x: int, y: int, ext: str, conn=Depends(get_connection)
):
    import time

    start = time.time()
    # path is fake, this is not going to be persisted
    tm = generate.generate_map(Path("/fake"), x, y, z, conn, tiles=TILE_RESOLUTION)
    print(f"Time for pure generation: {time.time() - start:.2f}")
    data_repr = tm.to_dict()

    if ext == "json":
        return data_repr
    elif ext == "png":
        out_image = render_tilemap(tm)
        ret_data = BytesIO()
        out_image.save(ret_data, "PNG")
        return Response(content=ret_data.getvalue(), media_type="image/png")
    else:
        return HTTPException(400, f"Unknown extension {ext}")


@app.get("/{file_path:path}")
def get_path(file_path: str):
    base_folder = Path("demo_tilegame2")
    p = base_folder / file_path
    assert p.is_relative_to(base_folder)
    if p.exists() and not p.is_dir():
        raw_data = p.read_bytes()
        return Response(content=raw_data, media_type=mimetypes.guess_type(file_path)[0])
    # not there, was it a chunk request?
    if CHUNK_REGEX.match(file_path) is None:
        print("Cannot find ", p)
        raise HTTPException(404, "File not found")
    # it was, generate it on the fly
    # get the tiled world coordinates
    x, y = (int(e) for e in CHUNK_REGEX.match(file_path).groups())
    geo_x = WORLD_CENTER_X + x
    geo_y = WORLD_CENTER_Y + y
    p = base_folder / f"maps/generated/chunk_{x}_{y}.json"
    # if already there, read it and that's it
    if p.exists():
        with open(p) as fr:
            return json.load(fr)
    print(f"Chunk {y, y} means XYZ {geo_x, geo_y, GAME_ZOOM_LEVEL}")
    import time

    start = time.time()
    with get_connection() as conn:
        tm = generate.generate_map(
            p, geo_x, geo_y, GAME_ZOOM_LEVEL, conn, tiles=TILE_RESOLUTION
        )
    print(f"Time for pure generation: {time.time() - start:.2f}")
    # cache the file
    data_repr = tm.to_dict()
    with open(p, "w") as fw:
        json.dump(data_repr, fw)
    for relpath, content in tm.get_event_files():
        with open(p.parent / relpath, "w") as fw:
            fw.write(content)
    return data_repr
