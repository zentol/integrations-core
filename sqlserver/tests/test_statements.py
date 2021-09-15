import re
from copy import copy, deepcopy

import pytest
import logging

from datadog_checks.sqlserver import SQLServer
from datadog_checks.sqlserver.statements import STATEMENT_METRICS_QUERY

from .common import CHECK_NAME, CUSTOM_METRICS, CUSTOM_QUERY_A, CUSTOM_QUERY_B, EXPECTED_DEFAULT_METRICS, assert_metrics
from .utils import not_windows_ci, windows_ci
from .conftest import datadog_conn_docker

try:
    import pyodbc
except ImportError:
    pyodbc = None


@pytest.fixture
def dbm_instance(instance_docker):
    instance_docker['dbm'] = True
    # set the default for tests to run sychronously to ensure we don't have orphaned threads running around
    instance_docker['query_samples'] = {'enabled': True, 'run_sync': True, 'collection_interval': 1}
    # set a very small collection interval so the tests go fast
    instance_docker['query_metrics'] = {'enabled': True, 'run_sync': True, 'collection_interval': 0.1}
    return copy(instance_docker)


@pytest.fixture
def bob_conn(dbm_instance):
    # Make DB connection
    conn_str = 'DRIVER={};Server={};Database=master;UID={};PWD={};'.format(
        dbm_instance['driver'], dbm_instance['host'], "bob", "hey-there-bob123"
    )
    conn = pyodbc.connect(conn_str, timeout=30)
    yield conn
    conn.close()


@not_windows_ci
@pytest.mark.integration
@pytest.mark.usefixtures('dd_environment')
@pytest.mark.parametrize(
    "database,query,params,match_query",
    [
        [
            "datadog_test",
            "SELECT * FROM things",
            (),
            "SELECT * FROM things"
        ],
        [
            "datadog_test",
            "SELECT * FROM things where id = ?",
            (1,),
            "(@P1 INT)SELECT * FROM things where id = @P1"
        ],
        [
            "master",
            "SELECT * FROM datadog_test.dbo.things where id = ?",
            (1,),
            "(@P1 INT)SELECT * FROM datadog_test.dbo.things where id = @P1"
        ],
        [
            "datadog_test",
            "SELECT * FROM things where id = ? and name = ?",
            (1, "hello"),
            "(@P1 INT,@P2 NVARCHAR(10))SELECT * FROM things where id = @P1 and name = @P2"
        ],
    ],
)
def test_statement_metrics(aggregator, dd_run_check, dbm_instance, bob_conn, database, query, params, match_query):
    check = SQLServer(CHECK_NAME, {}, [dbm_instance])

    with bob_conn.cursor() as cursor:
        cursor.execute("USE {}".format(database))

    def _run_test_queries():
        with bob_conn.cursor() as cursor:
            cursor.execute(query, params)
            cursor.execute(query, params)

    _run_test_queries()
    dd_run_check(check)
    aggregator.reset()
    _run_test_queries()
    dd_run_check(check)

    dbm_metrics = aggregator.get_event_platform_events("dbm-metrics")
    assert len(dbm_metrics) == 1, "should have collected exactly one dbm-metrics payload"
    payload = dbm_metrics[0]
    sqlserver_rows = payload.get('sqlserver_rows', [])
    assert sqlserver_rows, "should have collected some sqlserver query metrics rows"
    matching_rows = [r for r in sqlserver_rows if r['text'] == match_query]
    assert len(matching_rows) == 1, "expected exactly one matching metrics row"
    row = matching_rows[0]
    assert row['execution_count'] == 2, "wrong execution count"
    assert row['query_signature'], "missing query signature"
    assert row['database_name'] == database, "incorrect database_name"

    dbm_samples = aggregator.get_event_platform_events("dbm-samples")
    assert len(dbm_samples) > 0, "should have collected some samples"

@not_windows_ci
@pytest.mark.integration
@pytest.mark.usefixtures('dd_environment')
def test_basic_statement_metrics_query(datadog_conn_docker):
    test_query = "select * from sys.databases"

    # run this test query to guarantee there's at least one application query in the query plan cache
    with datadog_conn_docker.cursor() as cursor:
        cursor.execute(test_query)
        cursor.fetchall()

    # this test ensures that we're able to run the basic STATEMENT_METRICS_QUERY without error
    # the dm_exec_plan_attributes table-valued function used in this query contains a "sql_variant" data type
    # which is not supported by pyodbc, so we need to explicitly cast the field into the type we expect to see
    # without the cast this is expected to fail with
    # pyodbc.ProgrammingError: ('ODBC SQL type -150 is not yet supported.  column-index=77  type=-150', 'HY106')
    with datadog_conn_docker.cursor() as cursor:
        logging.debug("running statement_metrics_query: %s", STATEMENT_METRICS_QUERY)
        cursor.execute(STATEMENT_METRICS_QUERY)

        columns = [i[0] for i in cursor.description]
        # construct row dicts manually as there's no DictCursor for pyodbc
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        matching = [r for r in rows if r['text'] == test_query]
        assert matching, "the test query should be visible in the query stats"
        row = matching[0]

        cursor.execute(
            "select count(*) from sys.dm_exec_query_stats where query_hash = ? and query_plan_hash = ?",
            row['query_hash'],
            row['query_plan_hash']
        )

        assert cursor.fetchall()[0][0] == 1, "failed to read back the same query stats using the query and plan hash"

@not_windows_ci
@pytest.mark.integration
@pytest.mark.usefixtures('dd_environment')
def test_load_plans(datadog_conn_docker):
    test_query = "select * from sys.databases"

    # run this test query to guarantee there's at least one application query in the query plan cache
    with datadog_conn_docker.cursor() as cursor:
        cursor.execute(test_query)
        cursor.fetchall()

    with datadog_conn_docker.cursor() as cursor:
        logging.debug("running statement_metrics_query: %s", STATEMENT_METRICS_QUERY)
        cursor.execute(STATEMENT_METRICS_QUERY)
        columns = [i[0] for i in cursor.description]
        # construct row dicts manually as there's no DictCursor for pyodbc
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        import pdb
        pdb.set_trace()
