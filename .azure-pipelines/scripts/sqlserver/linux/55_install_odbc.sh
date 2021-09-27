#!/bin/bash

set -ex

sudo apt-get update
sudo apt-get install -y tdsodbc unixodbc unixodbc-dev

set +ex
