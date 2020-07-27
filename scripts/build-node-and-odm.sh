#!/bin/bash
# This script will re-build the ODM and NodeODM docker images locally, so the flags used to compile that code actually works for the available hardware.
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# We specify commits that are compatible with the current version of WebODM
ODM="3a433cff0ab1f45433992389130fcf9db80fe483"
NodeODM="76b33914af34928dbb851bbe96de7fc073fe74ad"

echo "Step 1/5: Creating a temp directory..."
mkdir -p temp
cd temp

echo "Step 2/5: Cloning the ODM and NodeODM repos"
git clone -q https://github.com/OpenDroneMap/ODM
cd ODM
git checkout ${ODM}
cd ..
git clone -q https://github.com/OpenDroneMap/NodeODM
cd NodeODM
git checkout ${NodeODM}
cd ..

echo "Step 3/5: Building the docker images"
docker build ODM -t opendronemap/odm --no-cache
docker build NodeODM -t opendronemap/nodeodm --no-cache

echo "Step 4/5: Removing the temp directory"
cd ..
rm -r temp

echo "Step 5/5: Optional: Clean any dangling docker images that might be left"
docker system prune

echo "Done!! You can now go to your WebODM folder and run 'sudo ./webodm.sh rebuild'"
