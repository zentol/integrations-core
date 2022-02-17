# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest

from datadog_checks.dev import docker_run

from . import common


@pytest.fixture(scope='session')
def dd_environment(instance):
    with docker_run(common.COMPOSE_FILE):
        yield instance, common.E2E_METADATA


@pytest.fixture(scope='session')
def instance():
    return {'foo': 'bar'}
