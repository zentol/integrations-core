# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from contextlib import closing, suppress
from datetime import datetime
from typing import List, NamedTuple, Tuple

import pyodbc
import threading

from datadog_checks.base import AgentCheck
from datadog_checks.base.utils.db import QueryManager

from . import queries
from .config_models import ConfigMixin

SystemInfo = NamedTuple('SystemInfo', [('hostname', str), ('os_version', int), ('os_release', int)])


class IbmICheck(AgentCheck, ConfigMixin):
    SERVICE_CHECK_NAME = "ibm_i.can_connect"

    def __init__(self, name, init_config, instances):
        super(IbmICheck, self).__init__(name, init_config, instances)

        self.connection = None
        self._query_manager = None
        self._current_errors = 0
        # self.check_initializations.append(self.set_up_query_manager)

    def handle_query_error(self, thread, error):
        thread.current_errors += 1
        return error

    def check(self, _):
        # From https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
        class CheckThread(threading.Thread):
            """Thread class with a stop() method. The thread itself has to check
            regularly for the stopped() condition."""

            def __init__(self, check=None, *args, **kwargs):
                super(CheckThread, self).__init__(*args, **kwargs)
                self.check = check
                self.current_errors = 0
                self._stop_event = threading.Event()

            def stop(self):
                self._stop_event.set()

            def stopped(self):
                return self._stop_event.is_set()

            def run(self):
                check_start = datetime.now()
                check_status = None

                connection = self.check._create_connection()
                if not self.stopped():
                    self.check.connection = connection
                else:
                    self.check.log.debug("Check stopped, not writing connection")

                try:
                    if not self.stopped():
                        self.check.query_manager.thread_execute(self)
                        check_status = AgentCheck.OK
                except AttributeError:
                    if not self.stopped():
                        self.check.warning('Could not set up query manager, skipping check run')
                        check_status = None
                except Exception as e:
                    if not self.stopped():
                        self.check._delete_connection(e)
                        check_status = AgentCheck.CRITICAL
                    else:
                        self.check.log.debug("Check stopped, not deleting connection")

                if not self.stopped():
                    if self.current_errors:
                        self.check._delete_connection("query error")
                        check_status = AgentCheck.CRITICAL

                    if check_status is not None:
                        self.check.service_check(
                            self.check.SERVICE_CHECK_NAME,
                            check_status,
                            tags=self.check.config.tags,
                            hostname=self.check._query_manager.hostname,
                        )

                    check_end = datetime.now()
                    check_duration = check_end - check_start
                    self.check.log.debug("Check duration: %s", check_duration)

                    if check_status is not None:
                        # The list() conversion is needed as self.config.tags is a tuple
                        check_duration_tags = list(self.check.config.tags) + ["check_id:{}".format(self.check.check_id)]
                        self.check.gauge(
                            "ibm_i.check.duration",
                            check_duration.total_seconds(),
                            check_duration_tags,
                            hostname=self.check._query_manager.hostname,
                        )

                else:
                    self.check.log.info("Check stopped")


        t = CheckThread(self)
        self.log.info("Starting check thread")
        t.start()
        t.join(20)
        t.stop()

        self.log.info("Finished joining check thread")

        if t.is_alive():
            self.log.info("Thread still alive, deleting connection")
            self._delete_connection("Thread timed out")
            self.log.info("Connection deleted")
        else:
            self.log.info("Thread dead")

    def execute_query(self, query):
        print("Executing query {}".format(query))
        # https://github.com/mkleehammer/pyodbc/wiki/Connection#execute
        with closing(self.connection.execute(query)) as cursor:

            # https://github.com/mkleehammer/pyodbc/wiki/Cursor
            for row in cursor:
                yield row

    def _create_connection(self):
        if self.connection:
            return self.connection

        # https://www.connectionstrings.com/as-400/
        # https://www.ibm.com/support/pages/odbc-driver-ibm-i-access-client-solutions
        connection_string = self.config.connection_string
        if not connection_string:
            connection_string = f'Driver={{{self.config.driver.strip("{}")}}};'

            if self.config.system:
                connection_string += f'System={self.config.system};'

            if self.config.username:
                connection_string += f'UID={self.config.username};'

            if self.config.password:
                connection_string += f'PWD={self.config.password};'
                self.register_secret(self.config.password)

        return pyodbc.connect(connection_string)

    def _delete_connection(self, e):
        if self.connection:
            self.warning('An error occurred, resetting IBM i connection: %s', e)
            with suppress(Exception):
                self.connection.close()
            self.connection = None

    @property
    def query_manager(self):
        if self._query_manager is None:
            self.set_up_query_manager()
        return self._query_manager

    def set_up_query_manager(self):
        system_info = self.fetch_system_info()
        if system_info:
            query_list = [
                queries.BaseDiskUsage,
                queries.CPUUsage,
                queries.InactiveJobStatus,
                queries.ActiveJobStatus,
                queries.JobMemoryUsage,
                queries.MemoryInfo,
                queries.JobsInJobQueueInfo,
                queries.JobQueueInfo,
                queries.get_message_queue_info(self.config.severity_threshold),
            ]
            if system_info.os_version > 7 or (system_info.os_version == 7 and system_info.os_release >= 3):
                query_list.append(queries.DiskUsage)
                query_list.append(queries.SubsystemInfo)

            if self.config.fetch_ibm_mq_metrics and self.ibm_mq_check():
                query_list.append(queries.IBMMQInfo)

            self._query_manager = QueryManager(
                self,
                self.execute_query,
                tags=self.config.tags,
                queries=query_list,
                hostname=system_info.hostname,
                error_handler=self.handle_query_error,
            )
            self._query_manager.compile_queries()

    def ibm_mq_check(self):
        # Try to get data from the IBM MQ tables. If they're not present,
        # an exception is raised, and we return that IBM MQ is not available.
        query = "SELECT QNAME, COUNT(*) FROM TABLE(MQREADALL()) GROUP BY QNAME"
        try:
            # self.execute_query(query) yields a generator, therefore the SQL query is actually run
            # only when needed (eg. when looping through it, transforming it
            # into a list, using next on it to get the next element).
            # We do need the query to be executed, which is why we do an operation on it.
            # We use the list operation because we know it will work as long as the query doesn't
            # raise an error (if we were to use next, we'd have to take care of the case where
            # the generator rasies a StopIteration exception because the query is valid but returns 0 rows).
            list(self.execute_query(query))  # type: List[Tuple[str]]
        except Exception as e:
            self.log.debug("Couldn't find IBM MQ data, turning off IBM MQ queries: %s", e)
            return False

        return True

    def fetch_system_info(self):
        try:
            return self.system_info_query()
        except Exception as e:
            self._delete_connection(e)

    def system_info_query(self):
        query = "SELECT HOST_NAME, OS_VERSION, OS_RELEASE FROM SYSIBMADM.ENV_SYS_INFO"
        results = list(self.execute_query(query))  # type: List[Tuple[str]]
        if len(results) == 0:
            self.log.error("Couldn't find system info on the remote system.")
            return None
        if len(results) > 1:
            self.log.error("Too many results returned by system query. Expected 1, got %d", len(results))
            return None

        info_row = results[0]
        if len(info_row) != 3:
            self.log.error("Expected 3 columns in system info query, got %d", len(info_row))
            return None

        hostname = info_row[0]
        try:
            os_version = int(info_row[1])
        except ValueError:
            self.log.error("Expected integer for OS version, got %s", info_row[1])
            return None

        try:
            os_release = int(info_row[2])
        except ValueError:
            self.log.error("Expected integer for OS release, got %s", info_row[2])
            return None

        return SystemInfo(hostname=hostname, os_version=os_version, os_release=os_release)
