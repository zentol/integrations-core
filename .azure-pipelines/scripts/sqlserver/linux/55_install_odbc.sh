#!/bin/bash

set -ex

sudo apt-get update
sudo apt-get install -y tdsodbc unixodbc unixodbc-dev
echo "tds_version = 8.0" | sudo tee -a /etc/odbc.ini
sudo cat /etc/freetds/freetds.conf | sed "s/tds version =.*/tds version = 8.0/g" | sudo tee /etc/freetds/freetds.conf

set +ex
