# # (C) Datadog, Inc. 2022-present
# # All rights reserved
# # Licensed under a 3-clause BSD style license (see LICENSE)

import pytest

from datadog_checks.dev.tooling.commands.validate.jmx_metrics import duplicate_bean_check, validate_jmx_metrics
from datadog_checks.dev.tooling.utils import get_jmx_metrics_file
from mock import patch
from tests.tooling.commands.validate.jmx_test_cases.common import BEANS, DUPLICATE_BEANS


def yaml_path_helper(path):
    current = __file__.split("/")
    return "/".join(current[:-1]) + path


@pytest.mark.parametrize(
    'beans,errors',
    [
        (BEANS, 0),
        (DUPLICATE_BEANS, 1),
    ],
)
def test_duplicate_beans_function(beans, errors):
    result = duplicate_bean_check(beans.get("jmx_metrics"))
    assert len(result) >= errors

@pytest.mark.parametrize(
    'bean_yaml_path,errors',
    [
        (yaml_path_helper("/jmx_test_cases/bean.yaml"), 0),
        (yaml_path_helper("/jmx_test_cases/duplicate_bean.yaml"), 1),
    ],
)
def test_duplicate_bean_loader(bean_yaml_path, errors):
    with patch("datadog_checks.dev.tooling.utils.get_jmx_metrics_file", side_effect=[(bean_yaml_path, True)]) as mock_get_jmx_metrics_file:
      mock_get_jmx_metrics_file.return_value = (bean_yaml_path, True)
      validate_jmx_metrics("kafka", [], False)
