#!/usr/bin/env python3
import json
import os
import decimal
import datetime
import time

ACTIVITY_JSON_PLANS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activity")


def main():
    def _make_big_activity(depth, json):
        out = [json]
        for i in range(depth):
            json["session_id"] = i
            json["text"] = "q" * 4000  # 4k char query
            out.append(json)
        return out

    def _load_test_activity_json(filename):
        with open(os.path.join(ACTIVITY_JSON_PLANS_DIR, filename), 'r') as f:
            return json.load(f)

    def default_json_event_encoding(o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        raise TypeError

    test_json = _load_test_activity_json("single_activity.json")[0]  # load json and grab first row
    big_activity = _make_big_activity(10000, test_json)

    # test row conv with str cast
    str_estimated_size = 0
    str_time_start = time.time()
    print("Running test with len(str(Obj)) conv on row size {}".format(len(big_activity)))
    for a in big_activity:
        str_estimated_size += len(str(a))

    str_elapsed_ms = (time.time() - str_time_start) * 1000

    # test row conv with json dump
    json_estimated_size = 0
    json_time_start = time.time()
    print("Running test with json.dumps(Obj) conv on row size {}".format(len(big_activity)))
    for a in big_activity:
        json_estimated_size += len(json.dumps(a, default=default_json_event_encoding))

    json_elapsed_ms = (time.time() - json_time_start) * 1000

    print("\nResults:")
    print("String Cast time (ms): {}".format(str_elapsed_ms))
    print("String Cast estimated size (bytes): {}".format(str_estimated_size))
    print("JSON Dump time (ms): {}".format(json_elapsed_ms))
    print("JSON Dump estimated size (bytes): {}".format(json_estimated_size))

    print("\nDo full json serialization on 10k row payload..")
    ser_time_start = time.time()
    out = json.dumps(big_activity, default=default_json_event_encoding)
    ser_elapsed_ms = (time.time() - ser_time_start) * 1000
    print("Actual Size (bytes): {}".format(len(out)))
    print("Total Ser Time (ms): {}".format(ser_elapsed_ms))


if __name__ == "__main__":
    main()





