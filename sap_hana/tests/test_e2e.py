# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest

from . import metrics

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_check(dd_agent_check, instance):
    aggregator = dd_agent_check(instance, rate=True)
    server_tag = 'server:{}'.format(instance['server'])
    port_tag = 'port:{}'.format(instance['port'])

    for metric in metrics.STANDARD:
        aggregator.assert_metric_has_tag(metric, server_tag)
        aggregator.assert_metric_has_tag(metric, port_tag)
    for metric in metrics.OPTIONAL:
        aggregator.assert_metric_has_tag(metric, server_tag, at_least=0)
        aggregator.assert_metric_has_tag(metric, port_tag, at_least=0)

    aggregator.assert_all_metrics_covered()
