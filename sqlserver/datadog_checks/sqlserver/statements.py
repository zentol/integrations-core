import time

from cachetools import TTLCache
from datadog_checks.base import is_affirmative
from datadog_checks.base.utils.db.sql import compute_sql_signature
from datadog_checks.base.utils.db.statement_metrics import StatementMetrics
from datadog_checks.base.utils.db.utils import DBMAsyncJob, RateLimitingTTLCache, default_json_event_encoding
from datadog_checks.base.utils.serialization import json

try:
    import datadog_agent
except ImportError:
    from ..stubs import datadog_agent

DEFAULT_COLLECTION_INTERVAL = 10

SQL_SERVER_METRICS_COLUMNS = [
    "execution_count",
    "total_worker_time",
    "total_physical_reads",
    "total_logical_writes",
    "total_logical_reads",
    "total_clr_time",
    "total_elapsed_time",
    "total_rows",
    "total_dop",
    "total_grant_kb",
    "total_used_grant_kb",
    "total_ideal_grant_kb",
    "total_reserved_threads",
    "total_used_threads",
    "total_columnstore_segment_reads",
    "total_columnstore_segment_skips",
    "total_spills",
]

# alternate approach, do a sub select to look up the dbid for each query, not sure if this is faster than cross
# join or not. Plus because we're grouping by plan_handle there is a concern that some of the aggregations may be off if
# one query has multiple plans. Cross apply seems to do the same thing.
# select text,
# (select value from sys.dm_exec_plan_attributes(plan_handle) where attribute = 'dbid') as dbid,
# sum(execution_count) as execution_count
# from sys.dm_exec_query_stats cross apply sys.dm_exec_sql_text(sql_handle)
# group by text, sql_handle, plan_handle, dbid;

# TODO: aggregate by both database and userid
STATEMENT_METRICS_QUERY = """\
with qstats as (
    select text, query_hash, query_plan_hash, value as dbid, {}
    from sys.dm_exec_query_stats
        cross apply sys.dm_exec_sql_text(sql_handle)
        cross apply sys.dm_exec_plan_attributes(plan_handle)
    where 
        attribute = 'dbid'
    group by text, sql_handle, query_hash, query_plan_hash, value
) 
select text, query_hash, query_plan_hash, name as database_name, {}
    from qstats S
    join sys.databases D on S.dbid = D.database_id;
""".format(
    ', '.join(['sum({}) as {}'.format(c, c) for c in SQL_SERVER_METRICS_COLUMNS]),
    ', '.join(SQL_SERVER_METRICS_COLUMNS)
)

PLAN_LOOKUP_QUERY = """\
select query_plan from sys.dm_exec_query_stats
    cross apply sys.dm_exec_query_plan(plan_handle)
where
    query_hash = ? and query_plan_hash = ?
"""


def _row_key(row):
    """
    :param row: a normalized row from pg_stat_statements
    :return: a tuple uniquely identifying this row
    """
    return row['database_name'], row['query_signature'], row['query_hash'], row['query_plan_hash']


class SqlserverStatementMetrics(DBMAsyncJob):
    """Collects telemetry for SQL statements"""

    def __init__(self, check):
        self.check = check
        self.log = check.log
        collection_interval = float(
            check.statement_metrics_config.get('collection_interval', DEFAULT_COLLECTION_INTERVAL)
        )
        if collection_interval <= 0:
            collection_interval = DEFAULT_COLLECTION_INTERVAL
        self.collection_interval = collection_interval
        super(SqlserverStatementMetrics, self).__init__(
            check,
            run_sync=is_affirmative(check.statement_metrics_config.get('run_sync', False)),
            enabled=is_affirmative(check.statement_metrics_config.get('enabled', True)),
            expected_db_exceptions=(),
            min_collection_interval=check.min_collection_interval,
            config_host=check.resolved_hostname,
            dbms="sqlserver",
            rate_limit=1 / float(collection_interval),
            job_name="query-metrics",
            shutdown_callback=self._close_db_conn,
        )
        self._state = StatementMetrics()
        self._init_caches()

    def _init_caches(self):
        # full_statement_text_cache: limit the ingestion rate of full statement text events per query_signature
        self._full_statement_text_cache = TTLCache(
            maxsize=self.check.instance.get('full_statement_text_cache_max_size', 10000),
            ttl=60 * 60 / self.check.instance.get(
                'full_statement_text_samples_per_hour_per_query', 1
            ),
        )

        # seen_samples_ratelimiter: limit the ingestion rate per (query_signature, plan_signature)
        # TODO: maybe we can far relax this rate? Since nothing is changing, there is no "activity" info for these
        # plans, we only really need them once per hour
        self._seen_plans_ratelimiter = RateLimitingTTLCache(
            # assuming ~100 bytes per entry (query & plan signature, key hash, 4 pointers (ordered dict), expiry time)
            # total size: 10k * 100 = 1 Mb
            maxsize=int(self.check.instance.get('seen_samples_cache_maxsize', 10000)),
            ttl=60 * 60 / int(self.check.instance.get('samples_per_hour_per_query', 15)),
        )

    def _close_db_conn(self):
        pass

    def _load_raw_query_metrics_rows(self):
        self.log.debug("collecting sql server statement metrics")
        with self.check.connection.open_managed_default_connection():
            with self.check.connection.get_managed_cursor() as cursor:
                cursor.execute(STATEMENT_METRICS_QUERY)
                columns = [i[0] for i in cursor.description]
                # construct row dicts manually as there's no DictCursor for pyodbc
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.log.debug("loaded sql server statement metrics len(rows)=%s", len(rows))
                return rows

    def _normalize_queries(self, rows):
        normalized_rows = []
        for row in rows:
            try:
                obfuscated_statement = datadog_agent.obfuscate_sql(row['text'])
            except Exception as e:
                # obfuscation errors are relatively common so only log them during debugging
                # TODO: maybe should not log whole text because it's not obfuscated by the database
                self.log.debug("Failed to obfuscate query '%s': %s", row['text'], e)
                continue
            row['text'] = obfuscated_statement
            row['query_signature'] = compute_sql_signature(obfuscated_statement)
            row['query_hash'] = row['query_hash'].hex()
            row['query_plan_hash'] = row['query_plan_hash'].hex()
            normalized_rows.append(row)
        return normalized_rows

    def _collect_metrics_rows(self):
        rows = self._load_raw_query_metrics_rows()
        rows = self._normalize_queries(rows)
        if not rows:
            return []
        metric_columns = [c for c in rows[0].keys() if c.startswith("total_") or c == 'execution_count']
        rows = self._state.compute_derivative_rows(rows, metric_columns, key=_row_key)
        return rows

    @staticmethod
    def _to_metrics_payload_row(row):
        row = {k: v for k, v in row.items()}
        row['text'] = row['text'][0:200]
        return row

    def _to_metrics_payload(self, rows):
        return {
            'host': self.check.resolved_hostname,
            'timestamp': time.time() * 1000,
            'min_collection_interval': self.collection_interval,
            'tags': self.check.tags,
            'sqlserver_rows': [self._to_metrics_payload_row(r) for r in rows],
            'sqlserver_version': self.check.static_info_cache.get("version", ""),
            'ddagentversion': datadog_agent.get_version(),
        }

    def collect_statement_metrics_and_plans(self):
        """
        Collects statement metrics and plans.
        :return:
        """
        try:
            rows = self._collect_metrics_rows()
            if not rows:
                return
            for event in self._rows_to_fqt_events(rows):
                self._check.database_monitoring_query_sample(json.dumps(event, default=default_json_event_encoding))
            # truncate query text to the maximum length supported by metrics tags
            payload = self._to_metrics_payload(rows)
            self._check.database_monitoring_query_metrics(json.dumps(payload, default=default_json_event_encoding))
            for event in self._collect_plans(rows):
                self._check.database_monitoring_query_sample(json.dumps(event, default=default_json_event_encoding))

        except Exception:
            self.log.exception('Unable to collect statement metrics due to an error')
            return []

    def _rows_to_fqt_events(self, rows):
        for row in rows:
            query_cache_key = _row_key(row)
            if query_cache_key in self._full_statement_text_cache:
                continue
            self._full_statement_text_cache[query_cache_key] = True
            tags = self.check.tags + ["db:{}".format(row['database_name'])]
            yield {
                "timestamp": time.time() * 1000,
                "host": self._check.resolved_hostname,
                "ddagentversion": datadog_agent.get_version(),
                "ddsource": "sqlserver",
                "ddtags": ",".join(tags),
                "dbm_type": "fqt",
                "db": {
                    "instance": row['database_name'],
                    "query_signature": row['query_signature'],
                    "statement": row['text'],
                },
                "sqlserver": {},
            }

    def run_job(self):
        self.collect_statement_metrics_and_plans()

    def _load_plan(self, query_hash, query_plan_hash):
        # loads the plan
        self.log.debug("collecting plan")

        with self.check.connection.open_managed_default_connection():
            with self.check.connection.get_managed_cursor() as cursor:
                cursor.execute(PLAN_LOOKUP_QUERY,
                               bytes.fromhex(query_hash),
                               bytes.fromhex(query_plan_hash))
                result = cursor.fetchall()
                if not result:
                    self.log.debug("failed to loan plan, it must have just been expired out of the plan cache")
                    return None
                return result[0][0]

    def _collect_plans(self, rows):
        for row in rows:
            plan_key = (row['query_signature'], row['query_hash'], row['query_plan_hash'])
            if self._seen_plans_ratelimiter.acquire(plan_key):
                raw_plan = self._load_plan(row['query_hash'], row['query_plan_hash'])
                yield {
                    "host": self._db_hostname,
                    "ddagentversion": datadog_agent.get_version(),
                    "ddsource": "sqlserver",
                    "ddtags": ",".join(self.check.tags),
                    "timestamp": time.time() * 1000,
                    "dbm_type": "plan",
                    "db": {
                        "instance": row.get("database_name", None),
                        "plan": {
                            "definition": raw_plan,
                            "signature": row['query_plan_hash'],
                            "collection_errors": None,
                        },
                        "query_signature": row['query_signature'],
                        # "application": row.get('application_name', None),
                        # "user": row['usename'],
                        "statement": row['text'],
                    },
                    'sqlserver': {
                        'query_hash': row['query_hash'],
                        'query_plan_hash': row['query_plan_hash'],
                    },
                }
