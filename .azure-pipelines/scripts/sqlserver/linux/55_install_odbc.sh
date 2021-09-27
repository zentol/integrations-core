#!/bin/bash

set -ex

sudo apt-get update
sudo apt-get install -y tdsodbc unixodbc unixodbc-dev
echo "tds_version = 8.0" >> /etc/odbc.ini

set +ex
