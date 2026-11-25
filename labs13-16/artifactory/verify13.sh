#!/bin/bash
set -euo pipefail
AUTH=/home/devops/labs13-16/.docker-auth
cd /home/devops/labs13-16/demo
docker --config "$AUTH" pull 127.0.0.1:15000/docker-remote/library/alpine:3.21
docker --config "$AUTH" build -t 127.0.0.1:15000/docker-local/student-demo:1.0 .
docker --config "$AUTH" push 127.0.0.1:15000/docker-local/student-demo:1.0
docker --config "$AUTH" pull 127.0.0.1:15000/docker/student-demo:1.0
a=$(docker image inspect --format '{{.Id}}' 127.0.0.1:15000/docker-local/student-demo:1.0)
b=$(docker image inspect --format '{{.Id}}' 127.0.0.1:15000/docker/student-demo:1.0)
test "$a" = "$b"
printf 'Local and virtual image ID match: %s\n' "$a"
docker --config "$AUTH" run --rm 127.0.0.1:15000/docker/student-demo:1.0
