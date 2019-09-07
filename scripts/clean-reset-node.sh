#!/bin/bash
# This script will re-build the ODM and NodeODM docker images locally, so the flags used to compile that code actually works for the available hardware.
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

if [ ! "$(docker ps -q -f name=^/$1$)" ]; then
  echo "Couldn't find a container with the name $1"
  exit
fi  

COMMAND="$(docker inspect -f '{{join .Config.Cmd " " }}' $1)"

docker stop $1
docker rm $1
docker run -d --name $1 --network webodm_default opendronemap/nodeodm ${COMMAND}