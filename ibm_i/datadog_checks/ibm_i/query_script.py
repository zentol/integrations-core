import select
import pyodbc
import sys


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
                        print("|".join(str(el) for el in row), flush=True)
            except Exception as e:
                print("{}".format(e), file=sys.stderr, flush=True)
            print('ENDOFQUERY', flush=True)
