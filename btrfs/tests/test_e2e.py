# (C) Datadog, Inc. 2010-present
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)
import pytest


@pytest.mark.e2e
def test_e2e(dd_agent_check):
    aggregator = dd_agent_check({}, rate=True)

    aggregator.assert_metric('system.disk.btrfs.used', count=4)
    aggregator.assert_all_metrics_covered()

