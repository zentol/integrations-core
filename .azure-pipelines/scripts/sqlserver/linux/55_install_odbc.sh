#!/bin/bash

set -ex

sudo apt-get update
sudo apt-get install -y --no-install-recommends tdsodbc unixodbc unixodbc-dev

set +ex
