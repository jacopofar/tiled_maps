#!/bin/zsh

# create the empty directory, or Docker will as root
mkdir -p pgdata

# the passwd mount is to reuse the user id
docker run --rm -d \
    --name postgis-test-db \
    -p 15432:5432 \
    -e POSTGRES_PASSWORD=testpassword \
    --user "$(id -u):$(id -g)" \
    -v /etc/passwd:/etc/passwd:ro \
    -v $(pwd)/pgdata:/var/lib/postgresql/data \
    postgis/postgis:16-master