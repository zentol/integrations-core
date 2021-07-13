import select
import pyodbc
import sys


def query():
    connection = None

    for string in sys.stdin:
        if connection is None:
            connection_string = string.strip()
            connection = pyodbc.connect(connection_string)
        else:
            query = string.strip()
            try:
                with connection.execute(query) as c:
                    for row in c:
                        print("|".join(str(el) for el in row), flush=True)
            except pyodbc.Error as e:
                print("{}\n".format(e), file=sys.stderr, flush=True)

            print('ENDOFQUERY', flush=True)


