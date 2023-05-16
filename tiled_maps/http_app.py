from typing import Union
from io import BytesIO
import json
from pathlib import Path
import mimetypes
import re
from os import environ

from tiled_maps.database import get_connection, tile_to_terrainmap
from tiled_maps.raster import terrainmap_to_image
from tiled_maps.tilemap import terrain_to_tilemap

from fastapi import FastAPI, HTTPException
from fastapi import Depends
from fastapi.responses import Response


app = FastAPI()

CHUNK_REGEX = re.compile(r".+chunk_(-?\d+)_(-?\d+).json")
WORLD_CENTER_X = int(environ["WORLD_CENTER_X"])
WORLD_CENTER_Y = int(environ["WORLD_CENTER_Y"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/zxy/{z}/{x}/{y}.png")
def retrieve_xyz_tile(z: int, x: int, y: int, conn=Depends(get_connection)):
    print(z, x, y)
    tm = tile_to_terrainmap(x, y, z, conn, tiles=32)
    out_image = terrainmap_to_image(tm, tiles=32)

    ret_data = BytesIO()
    out_image.save(ret_data, "PNG")
    return Response(content=ret_data.getvalue(), media_type="image/png")


@app.get("/game01/{file_path:path}")
def retrieve_game_file(file_path: str, conn=Depends(get_connection)):
    print(file_path)
    base_folder = Path("demo_tilegame2")
    p = base_folder / file_path
    print(p)
    print(base_folder)
    assert p.is_relative_to(base_folder)
    if p.exists() and not p.is_dir():
        raw_data = p.read_bytes()
        return Response(content=raw_data, media_type=mimetypes.guess_type(file_path)[0])
    # does not exist, is it a chunk to calculate?
    if CHUNK_REGEX.match(file_path) is None:
        raise HTTPException(status_code=404, detail="Item not found")
    # it exists, get the coordinates
    x, y = (int(e) for e in CHUNK_REGEX.match(file_path).groups())
    # assuming zoom level 18, a tile is a square of 152 meters of side
    # so each cell is more or less a meter (very roughly)
    tm = tile_to_terrainmap(WORLD_CENTER_X + x, WORLD_CENTER_Y + y, 18, conn, tiles=128)
    whole_dict = terrain_to_tilemap(tm)
    # write the file for cachine and troubleshooting
    with open(p, "w") as fw:
        json.dump(whole_dict, fw)
    return whole_dict
