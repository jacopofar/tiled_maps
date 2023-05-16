from tiled_maps.tilemap import TerrainMap

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
