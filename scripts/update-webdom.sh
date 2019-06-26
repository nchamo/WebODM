#!/bin/bash
# This script will pull the latest master from the WebODM repo and then rebuild. It will stop the service before running, and start it again before finishing.
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Step 1/5: Stopping the service"
systemctl stop webodm-docker.service 

echo "Step 2/5: Pulling latest master"
cd ../WebODM
git pull

echo "Step 3/5: Rebuilding the image"
./webodm.sh rebuild

echo "Step 4/5: Starting the service again"
systemctl start webodm-docker.service

echo "Step 5/5: Optional: Clean any dangling docker images that might be left"
docker system prune

echo "Done!!"
