# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os

from datadog_checks.dev import get_docker_hostname, get_here

HERE = get_here()
COMPOSE_FILE = os.path.join(HERE, 'docker', 'docker-compose.yaml')
SERVER = get_docker_hostname()
PORT = 9483

E2E_METADATA = {
    'docker_volumes': ['{}/agent_scripts/start_commands.sh:/tmp/start_commands.sh'.format(HERE)],
    'start_commands': ['bash /tmp/start_commands.sh'],
    'env_vars': {'LD_LIBRARY_PATH': '/opt/mqm/lib64:/opt/mqm/lib', 'C_INCLUDE_PATH': '/opt/mqm/inc'},
}
