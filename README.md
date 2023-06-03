# Map to Tiled maps

This Python project shows how to generate Tiled maps from an OpenStreetMap extract.

The generated files can be read an manipulated by Tiled and by the [Godot 4 tiledmap](https://github.com/jacopofar/godot-4-tiledmap) project.

## Features

The script is very hacky, in short it does two things;

1. Exposes a raster tile server compatible with QGIS or web libraries like Leaftet to show an overlay of the tiled map generated on the fly

2. Exposes an endpoint that generates Tiled maps files on the fly, also persisting them on the disk. This is for caching and to later serve them with as static files from nginx.

## Usage

1. Download an OpenStreetMap extract, for example from from [Geofabrik](https://download.geofabrik.de/). You can also use Osmium to extract a smaller area from a larger file.

2. Import the file into a PostGIS database, use the included `ingest_pbf.sh` script to quickly get a Dockerized postgis instance.

3. Prepare the `.env` file, use the `.env.example` as a template. You will also need to install dotenv, or populate the environment variables yourself.

4. Use PDM to install the dependencies, `dotenv run pdm run serve_reload` to run the script. `serve_reload` will watch for changes and reload the server, `serve` will not and will start multiple workers

## TO DO

The whole thing is quite hacky, here are some examples of improvements:

* Use JSONSchema and Pydantic 2 to handle the objects
* Handle terrains using wang tiles or similar
* Generate more object types
* Compress tilesets, rearranging them in a single one with only the used elements
* Rotate and scale objects to better fit an orthogonal map
* Handle overlapping elements, make it easy to specify what to preserve in case of conflicts
* Move the logic to config files
* Add tests? Right now the logic changes too often to make it worth