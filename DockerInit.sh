#!/bin/sh

CONFIG_FILE=/configs/config.ini
XPATHS_FILE=/configs/xpaths.json

if [ ! -f $CONFIG_FILE ]; then
    cp /crawler-tracker/config.ini $CONFIG_FILE
    cp /crawler-tracker/xpaths.json $XPATHS_FILE
fi
rm /crawler-tracker/config.ini /crawler-tracker/xpaths.json
ln -s $CONFIG_FILE /crawler-tracker/config.ini
ln -s $XPATHS_FILE /crawler-tracker/xpaths.json