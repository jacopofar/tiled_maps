#!/bin/zsh

./start_db.sh

docker exec postgis-test-db sh -c 'until pg_isready; do echo "Waiting for the DB to be up..."; sleep 4; done'
# sometimes there's a random restart, especially with low memory. Wait some extra time
# meh...
sleep 5
docker exec -it postgis-test-db /usr/bin/createdb -U postgres osm_data
docker exec -it postgis-test-db /usr/bin/psql -U postgres -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology; CREATE SCHEMA osm" osm_data

docker run --name pgosm --rm \
    -v $(pwd)/$1:/app/$1 \
    -e POSTGRES_PASSWORD=testpassword \
    -e POSTGRES_HOST='postgis-test-db' \
    -e POSTGRES_DB='osm_data' \
    --link postgis-test-db\
    rustprooflabs/pgosm-flex python3 docker/pgosm_flex.py --ram 4 --debug --input-file /app/$1 --layerset everything