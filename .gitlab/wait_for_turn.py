"""
First job of the CI that will wait for previous pipelines to be completed in order to prevent concurrency.
"""
import os
import urllib.parse
import urllib.request
import json
import time
import sys

GITLAB_API_TOKEN = os.environ['GITLAB_API_TOKEN']
CI_PROJECT_ID = os.environ['CI_PROJECT_ID']
CI_PIPELINE_ID = os.environ['CI_PIPELINE_ID']
CI_SERVER_URL = os.environ['CI_SERVER_URL']
INCOMPLETE_PIPELINE_STATUS = ['running', 'pending', 'created']

ITEMS_PER_PAGE = 100
SLEEP_DURATION = 120


def get_pipelines_for_status(status):
    params = {'per_page': ITEMS_PER_PAGE, 'status': status}
    headers = {'PRIVATE-TOKEN': GITLAB_API_TOKEN}

    data = urllib.parse.urlencode(params)
    data = data.encode('ascii')

    url = f"{CI_SERVER_URL}/api/v4/projects/{CI_PROJECT_ID}/pipeline"
    req = urllib.request.Request(url, data, headers)

    with urllib.request.urlopen(req) as response:
        pipelines = response.read()

    return json.loads(pipelines)


def can_pipeline_run():
    all_pipelines = []
    for status in INCOMPLETE_PIPELINE_STATUS:
        all_pipelines.extend(get_pipelines_for_status(status))

    higher_priority_pipelines = [p for p in all_pipelines if p["id"] < CI_PIPELINE_ID]

    # Current pipeline can run if it's
    return bool(higher_priority_pipelines)


if __name__ == "__main__":
    for i in range(20):
        if can_pipeline_run():
            break
        time.sleep(SLEEP_DURATION)
    else:
        # Pipeline couldn't be scheduled, let's fail to request manual assistance
        sys.exit(1)

