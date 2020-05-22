from contextlib import closing

import datadog_agent
from datadog_checks.base import is_affirmative

from .sql import compute_sql_signature

"""
8.0
| slow_log | CREATE TABLE `slow_log` (
  `start_time` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `user_host` mediumtext NOT NULL,
  `query_time` time(6) NOT NULL,
  `lock_time` time(6) NOT NULL,
  `rows_sent` int NOT NULL,
  `rows_examined` int NOT NULL,
  `db` varchar(512) NOT NULL,
  `last_insert_id` int NOT NULL,
  `insert_id` int NOT NULL,
  `server_id` int unsigned NOT NULL,
  `sql_text` mediumblob NOT NULL,
  `thread_id` bigint unsigned NOT NULL
) ENGINE=CSV DEFAULT CHARSET=utf8 COMMENT='Slow log' |"""

"""
5.6
| slow_log | CREATE TABLE `slow_log` (
  `start_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `user_host` mediumtext NOT NULL,
  `query_time` time NOT NULL,
  `lock_time` time NOT NULL,
  `rows_sent` int(11) NOT NULL,
  `rows_examined` int(11) NOT NULL,
  `db` varchar(512) NOT NULL,
  `last_insert_id` int(11) NOT NULL,
  `insert_id` int(11) NOT NULL,
  `server_id` int(10) unsigned NOT NULL,
  `sql_text` mediumtext NOT NULL,
  `thread_id` bigint(21) unsigned NOT NULL
) ENGINE=CSV DEFAULT CHARSET=utf8 COMMENT='Slow log' |
+----------+----------------------------------------------
"""


VALID_EXPLAIN_STATEMENTS = frozenset([
  'select',
  'table',
  'delete',
  'insert',
  'replace',
  'update',
])


class ExecutionPlansMixin(object):
    """
    Mixin for collecting execution plans from query samples.
    """

    def __init__(self, *args, **kwargs):
        self._checkpoint = None
        self._slow_query_log_table_enabled = None

        # TODO: Make this a configurable limit
        self.query_limit = 500
    
    def _submit_log_events(self, *args, **kwargs):
        raise NotImplementedError('Must implement method _submit_log_events')

    def _slow_query_log_table_exists(self, db):
        query = """SELECT COUNT(1) FROM information_schema.TABLES where TABLE_SCHEMA = 'mysql' AND TABLE_NAME='slow_log';"""

        with closing(db.cursor()) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
        return result and result[0] > 0

    def _collect_execution_plans_slow_query_log(self, db, tags, options):
        if not is_affirmative(options.get('extra_performance_queries', False)):
            return False
        if self._slow_query_log_table_enabled is None:
            self._slow_query_log_table_enabled = self._slow_query_log_table_exists(db)
        elif self._slow_query_log_table_enabled is False:
            return False

        query = """
            SELECT start_time, sql_text
              FROM mysql.slow_log
             WHERE start_time > %s
          ORDER BY start_time DESC
             LIMIT %s
            """
        with closing(db.cursor()) as cursor:
            # For the first collection, do nothing but select the first checkpoint
            if self._checkpoint is None:
                cursor.execute('SELECT CURRENT_TIMESTAMP()')
                row = cursor.fetchone()
                self._checkpoint = row[0]

            cursor.execute(query, (self._checkpoint, self.query_limit))
            rows = cursor.fetchall()

        # TODO: run these asynchronously / do some benchmarking to optimize
        for row in rows:
            if row[0] > self._checkpoint:
                self._checkpoint = row[0]

            sql_text = row[1]
            plan = self._run_explain(db, sql_text)
            if plan:
                self._submit_log_events([{
                    'query': datadog_agent.obfuscate_sql(sql_text), 
                    'plan': plan, 
                    'querysignature': compute_sql_signature(sql_text)
                }])

    def _run_explain(self, db, statement):
        # TODO: cleaner query cleaning to strip comments, etc.
        if statement.strip().split(' ', 1)[0].lower() not in VALID_EXPLAIN_STATEMENTS:
            return
        query = 'EXPLAIN FORMAT=json {statement}'.format(statement=statement)

        with closing(db.cursor()) as cursor:
            cursor.execute(query)
        return cursor.fetchone()[0]
