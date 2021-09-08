
from datadog_checks.base.utils.db.utils import DBMAsyncJob, default_json_event_encoding
from datadog_checks.base import is_affirmative


class SqlserverStatementSamples(DBMAsyncJob):
    def __init__(self, check):
        pass
