import sys

import pyodbc

from datadog_checks.base.utils.serialization import json


def query():
    connection = None

    for string in sys.stdin:
        if connection is None:
            connection_string = string.strip()
            try:
                connection = pyodbc.connect(connection_string)
            except Exception as e:
                print("{}".format(e), file=sys.stderr, flush=True)
                # Make the next query end immediately and fetch the error
                print('ENDOFQUERY', flush=True)
        else:
            query = string.strip()
            try:
                with connection.execute(query) as c:
                    for row in c:
                        print(
                            json.dumps([item if item is None else str(item) for item in row]).decode("utf-8"),
                            flush=True,
                        )
            except Exception as e:
                print("{}".format(e), file=sys.stderr, flush=True)
            print('ENDOFQUERY', flush=True)
