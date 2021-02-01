#!/usr/bin/env bash
env_file='.docker-env'
docker_compose_file='docker-compose.yml'
source ${env_file}
docker-compose --env-file=${env_file} up -d