# (C) Datadog, Inc. 2010-2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

from datadog_checks.dev import get_docker_hostname

HOST = get_docker_hostname()

URL = 'http://{}:8080'.format(HOST)

INSTANCE = {
    'url': URL, 'tags': ['key:my-tag'],
}

FULL_CONFIG = {
    'instances': [INSTANCE],
    'init_config': {},
    'logs': [
        {
            "log_processing_rules": [
                {
                    "name": "new_log_start_with_date",
                    "pattern": "\\[\\d{4}\\-\\d{2}\\-\\d{2}",
                    "type": "multi_line"
                }
            ],
            "path": "/airflow_logs/dag_processor_manager/dag_processor_manager.log",
            "service": "airflow-service",
            "source": "airflow",
            "type": "file"
        },
        {
            "log_processing_rules": [
                {
                    "name": "new_log_start_with_date",
                    "pattern": "\\[\\d{4}\\-\\d{2}\\-\\d{2}",
                    "type": "multi_line"
                }
            ],
            "path": "/airflow_logs/scheduler/*/*.log",
            "service": "airflow-service",
            "source": "airflow",
            "type": "file"
        }
    ],
}

INSTANCE_WRONG_URL = {'url': 'http://localhost:5555', 'tags': ['key:my-tag']}
