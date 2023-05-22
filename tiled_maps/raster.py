from functools import lru_cache

from tiled_maps.dumb_generator import TerrainMap
from tiled_maps.tiled_helpers import tilemap
from PIL import Image, ImageDraw


def terrainmap_to_image(tm: TerrainMap, tiles: int = 32) -> Image:
    SIZE = 150
    out = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    d = ImageDraw.Draw(out)
    for x, y, terrain in tm:
        if terrain == "road":
            d.rectangle(
                (
                    x * SIZE / tiles,
                    y * SIZE / tiles,
                    (x + 1) * SIZE / tiles,
                    (y + 1) * SIZE / tiles,
                ),
                fill=(10, 10, 10),
            )
        elif terrain == "build":
            d.rectangle(
                (
                    x * SIZE / tiles,
                    y * SIZE / tiles,
                    (x + 1) * SIZE / tiles,
                    (y + 1) * SIZE / tiles,
                ),
                fill=(128, 128, 128),
            )
        else:
            # unknown, mark as red
            d.rectangle(
                (
                    x * SIZE / tiles,
                    y * SIZE / tiles,
                    (x + 1) * SIZE / tiles,
                    (y + 1) * SIZE / tiles,
                ),
                fill=(355, 10, 10),
            )
    return out


@lru_cache
def get_tile_raster(img: str, bbox: tuple[int, int, int, int]) -> Image:
    with Image.open(img) as im_in:
        return im_in.crop(bbox)


def render_tilemap(tm: tilemap.TiledMap) -> Image.Image:
    out = Image.new(
        "RGBA", (tm.width * tm.tilewidth, tm.height * tm.tileheight), (0, 0, 0, 0)
    )
    for layer in tm.layers:
        if layer.type == "tilelayer":
            for x, y, id in layer.tiles_with_coords():
                img, ix, iy, iw, ih = tm.get_static_tile_id_bounds(id)
                tile_img = get_tile_raster(img, (ix, iy, ix + iw, iy + ih))
                out.paste(tile_img, (x * tm.tilewidth, y * tm.tileheight))
    return out


if __name__ == "__main__":
    import json

    map_path = "demo_tilegame2/maps/manual/chunk_0_0.json"
    RAW_MAP = json.load(open(map_path))
    tm = tilemap.from_data(RAW_MAP | dict(path=map_path))
    render_tilemap(tm).show()
