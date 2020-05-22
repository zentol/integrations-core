import os
import time
import sys
import requests

GITLAB_TOKEN = os.environ['GITLAB_TOKEN']
CI_PROJECT_ID = os.environ['CI_PROJECT_ID']
CI_PIPELINE_ID = int(os.environ['CI_PIPELINE_ID'])

PENDING_STATES = ['running', 'pending', 'created']


def get_pipelines_to_run_with_higher_priority():
    pending = []
    for state in PENDING_STATES:
        get_params = {'per_page': 100, 'status': state}
        r = requests.get(
            f"https://gitlab.ddbuild.io/api/v4/projects/{CI_PROJECT_ID}/pipelines",
            params=get_params,
            headers={'PRIVATE-TOKEN': GITLAB_TOKEN}
        )
        r.raise_for_status()
        pending.extend(r.json())

    # Filter out all pipelines with lower priority
    return [p for p in pending if p['id'] < CI_PIPELINE_ID]

print("Hello")
for _ in range(10):
    remaining = get_pipelines_to_run_with_higher_priority()
    print(remaining)
    if not remaining:
        # Success, pipeline can run
        break
    ids = [str(p['id']) for p in remaining]
    print(f"Found remaining pipelines: {', '.join(ids)}")
    time.sleep(120)
else:
    print("Hey")
    # Unable to run for 20min, maybe a pipeline is stuck ?
    ids = [str(p['id']) for p in remaining]
    print(f"ERROR: Can't run pipeline as there are remaining pipelines: {', '.join(ids)}")
    sys.exit(-1)

