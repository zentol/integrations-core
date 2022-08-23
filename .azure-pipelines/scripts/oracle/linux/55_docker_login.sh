#!/bin/bash
set -euo pipefail

set +x

echo "[INFO] Docker login"
for i in 2 4 8 16 32; do
  echo "$ORACLE_DOCKER_PASSWORD" | docker login container-registry.oracle.com --username "$ORACLE_DOCKER_USERNAME" --password-stdin && break
  echo "[INFO] Wait $i seconds and retry docker login"
  sleep $i
done

set -ex

# Allocate 6GB for oracle
# The default number of memory addresses is 65536, i.e. 512MB (Linux 64-bit).
# => To get 6GB, we multiply that amount by 12.
sudo sysctl -w vm.max_map_count=$(expr 12 \* 65536)

set +ex
