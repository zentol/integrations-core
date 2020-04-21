#!/bin/bash

source "$DDEV_COMMON_SCRIPTS/common.sh"

echo 'Running 55_install_client.sh'

ATTEMPTS=8 TIMEOUT=10 with_backoff bash -c 'false'
