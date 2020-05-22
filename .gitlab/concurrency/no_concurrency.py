import os
import time
import sys
import requests

GITLAB_TOKEN = os.environ['GITLAB_TOKEN']
CI_PROJECT_ID = os.environ['CI_PROJECT_ID']
CI_PIPELINE_ID = int(os.environ['CI_PIPELINE_ID'])

PENDING_STATES = ['running', 'created']
PIPELINES_COUNT_TO_RETURN = 100
SLEEP_BETWEEN_CHECK = 120
TOTAL_WAIT_TIME = 40 * 60


def get_pipelines_to_run_with_higher_priority():
    pending = []
    for state in PENDING_STATES:
        get_params = {'per_page': PIPELINES_COUNT_TO_RETURN, 'status': state}
        r = requests.get(
            f"https://gitlab.ddbuild.io/api/v4/projects/{CI_PROJECT_ID}/pipelines",
            params=get_params,
            headers={'PRIVATE-TOKEN': GITLAB_TOKEN}
        )
        r.raise_for_status()
        pending.extend(r.json())

    # Filter out all pipelines with lower priority
    return [p for p in pending if p['id'] < CI_PIPELINE_ID]


total_wait_time = 0
while total_wait_time < TOTAL_WAIT_TIME:
    remaining = get_pipelines_to_run_with_higher_priority()
    print(remaining)
    if not remaining:
        # Success, pipeline can run
        break
    pip_ids = [str(p['id']) for p in remaining]
    print(f"Found remaining pipelines: {', '.join(pip_ids)}")
    time.sleep(SLEEP_BETWEEN_CHECK)
    total_wait_time += SLEEP_BETWEEN_CHECK
else:
    # Unable to run for 40min, maybe a pipeline is stuck ?
    pip_ids = [str(p['id']) for p in remaining]
    print(f"ERROR: Can't run pipeline as there are remaining pipelines: {', '.join(pip_ids)}")
    sys.exit(-1)

