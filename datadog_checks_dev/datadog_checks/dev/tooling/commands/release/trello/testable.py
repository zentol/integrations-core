# (C) Datadog, Inc. 2018-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import random
import time
from typing import List, Optional, Sequence, Set, Tuple
from datetime import datetime, timedelta
import requests
import click

from .....subprocess import SubprocessError, run_command
from .....utils import basepath, chdir, get_next
from ....constants import CHANGELOG_LABEL_PREFIX, CHANGELOG_TYPE_NONE, get_root, set_root
from ....github import get_pr, get_pr_from_hash, get_pr_labels, get_pr_milestone, parse_pr_number, get_team_members, get_reviews, get_last_prs
from ....trello import TrelloClient
from ....utils import format_commit_id
from ...console import CONTEXT_SETTINGS, abort, echo_failure, echo_info, echo_success, echo_waiting, echo_warning


class TrelloCardAssigner:
    def __init__(self, teams: [str]):
        self.__user_teams = {}
        self.__teams = []
        
        for team in teams:
            echo_info(f'Get team members for #{team}')
            members = get_team_members(team)
            member_logins = [m["login"] for m in members]
            team = TrelloCardAssigner.Team(team)
            limit = datetime.utcnow() + timedelta(days=-100)
            self.__teams.append(team)
            for login in member_logins:
                date = self.__get_last_pr_date(login)
            
                if date and date > limit:
                    self.__user_teams[login] = team
                    team.add(login)
                else:
                    echo_info(f'Skip inactive user {login} {date}')
                time.sleep(1)


    def get_next_tester(self, author: str, pr_num: int) -> Optional[str]:
        if author not in self.__user_teams:            
            return None
        team = self.__user_teams[author]
        return team.get_next_tester(author, pr_num)

    def get_stats(self):
        stats = {}
        for team in self.__teams:
            stats[team.get_name()] = team.get_stats()        
        return stats

    def __get_last_pr_date(self, user: str) -> Optional[datetime]:
        last_prs = []
        for _ in range(7):
            try:
                last_prs = get_last_prs(user)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    time.sleep(5)                    
                else:
                    raise

        last_prs_items = last_prs['items']
        if len(last_prs_items) == 0:
            return None
        last_pr = last_prs_items[0]
        created_at = last_pr['created_at']
        return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")        
        

    class Team:
        def __init__(self, name: str):
            self.__prs_by_tester = {}
            self.__name = name            
        
        def add(self, user: str):
            self.__prs_by_tester[user] = []

        def get_next_tester(self, author: str, pr_num: int) -> Optional[str]:            
            exclude_testers = self.__get_reviewers(pr_num)
            exclude_testers.add(author)
            
            # find a tester who are not the author or a reviewer
            tester = self.__select_testers(lambda t: t in exclude_testers)
            if tester is None:
                # find a tester who are not the author
                tester = self.select_testers(lambda t: t != author)

            if tester is not None:
                self.__prs_by_tester[tester].append(pr_num)
            else:
                raise Exception() ## TODOTOTOD
            return tester

        def get_stats(self):
            return self.__prs_by_tester

        def get_name(self):
            return self.__name

        def __select_testers(self, user_excluded_fct) -> Optional[str]:
            candidates = []
            minReview = 0
            for user, prs in self.__prs_by_tester.items():
                if not user_excluded_fct(user):
                    if len(candidates) == 0 or len(prs) <= minReview:
                        # if we find a user with last review clean the candidate
                        if len(prs) < minReview:
                            candidates.clear()
                        candidates.append(user)
                        minReview = len(prs)

            if len(candidates) > 0:
                return candidates[random.randint(0, len(candidates) - 1)]
            return None

        def __get_reviewers(self, pr_num: int) -> Set[str]:
            reviews = get_reviews(pr_num)
            return set([r["user"]["login"] for r in reviews])


def create_trello_card(
    client: TrelloClient,
    trelloCardAssigner: TrelloCardAssigner,
    teams: List[str],
    pr_num: int,
    pr_title: str,
    pr_url: str,
    pr_labels: List[str],
    pr_body: str,
    dry_run: bool,
    pr_author: str,
    config: dict,
) -> None:
    labels = ', '.join(f'`{label}`' for label in sorted(pr_labels))
    body = f'''\
Pull request: {pr_url}
Author: `{pr_author}`
Labels: {labels}

{pr_body}'''
    for team in teams:
        member = pick_card_member(config, pr_author, team)
        if member is None:
            member = trelloCardAssigner.get_next_tester(pr_author, pr_num)
        if member:
            echo_info(f'Randomly assigned issue to {member}')
        if dry_run:
            echo_success(f'Will create a card for team {team}: ', nl=False)
            echo_info(pr_title)
            continue
        creation_attempts = 3
        for attempt in range(3):
            rate_limited, error, response = client.create_card(team, pr_title, body, member)
            if rate_limited:
                wait_time = 10
                echo_warning(
                    'Attempt {} of {}: A rate limit in effect, retrying in {} '
                    'seconds...'.format(attempt + 1, creation_attempts, wait_time)
                )
                time.sleep(wait_time)
            elif error:
                if attempt + 1 == creation_attempts:
                    echo_failure(f'Error: {error}')
                    break

                wait_time = 2
                echo_warning(
                    'Attempt {} of {}: An error has occurred, retrying in {} '
                    'seconds...'.format(attempt + 1, creation_attempts, wait_time)
                )
                time.sleep(wait_time)
            else:
                echo_success(f'Created card for team {team}: ', nl=False)
                echo_info(response.json().get('url'))
                break


def _all_synced_with_remote(refs: Sequence[str]) -> bool:
    fetch_command = 'git fetch --dry'
    result = run_command(fetch_command, capture=True, check=True)
    return all(ref not in result.stderr for ref in refs)


def _get_and_parse_commits(base_ref: str, target_ref: str) -> List[Tuple[str, str]]:
    echo_info(f'Getting diff between {base_ref!r} and {target_ref!r}... ', nl=False)

    # Format as '<commit_hash> <subject line>', e.g.:
    # 'a70a792f9d1775b7d6d910044522f7a0d6941ad7 Update README.md'
    pretty_format = '%H %s'

    diff_command = f'git --no-pager log "--pretty={pretty_format}" {base_ref}..{target_ref}'

    try:
        result = run_command(diff_command, capture=True, check=True)
    except SubprocessError:
        echo_failure('Failed!')
        raise

    echo_success('Success!')
    lines: List[str] = result.stdout.splitlines()

    commits = []

    for line in reversed(lines):
        commit_hash, _, commit_subject = line.partition(' ')
        commits.append((commit_hash, commit_subject))

    return commits


def get_commits_between(base_ref: str, target_ref: str, *, root: str) -> List[Tuple[str, str]]:
    with chdir(root):
        if not _all_synced_with_remote((base_ref, target_ref)):
            abort(f'Your repository is not sync with the remote repository. Please run `git fetch` in {root!r} folder.')

        try:
            return _get_and_parse_commits(base_ref, target_ref)
        except SubprocessError as exc:
            echo_failure(str(exc))
            echo_failure('Unable to get the diff.')
            echo_info(
                f'HINT: ensure {base_ref!r} and {target_ref!r} both refer to a valid git reference '
                '(such as a tag or a release branch).'
            )
            raise click.Abort


def pick_card_member(config: dict, author: str, team: str) -> Optional[str]:
    """Return a member to assign to the created issue.
    In practice, it returns one trello user which is not the PR author, for the given team.
    For it to work, you need a `trello_users_$team` table in your ddev configuration,
    with keys being github users and values being their corresponding trello IDs (not names).

    For example::
        [trello_users_integrations]
        john = "xxxxxxxxxxxxxxxxxxxxx"
        alice = "yyyyyyyyyyyyyyyyyyyy"
    """
    users = config.get(f'trello_users_{team.lower()}')
    if not users:
        return None
    member = random.choice([key for user, key in users.items() if user != author])
    return member


@click.command(
    context_settings=CONTEXT_SETTINGS, short_help='Create a Trello card for each change that needs to be tested'
)
@click.argument('base_ref')
@click.argument('target_ref')
@click.option('--milestone', help='The PR milestone to filter by')
@click.option('--new-root', help='')
@click.option('--dry-run', '-n', is_flag=True, help='Only show the changes')
@click.pass_context
def testable(ctx: click.Context, base_ref: str, target_ref: str, milestone: str, dry_run: bool, new_root: str) -> None:
    """
    Create a Trello card for changes since a previous release (referenced by `BASE_REF`)
    that need to be tested for the next release (referenced by `TARGET_REF`).

    `BASE_REF` and `TARGET_REF` can be any valid git references. It practice, you should use either:

    * A tag: `7.16.1`, `7.17.0-rc.4`, ...

    * A release branch: `6.16.x`, `7.17.x`, ...

    * The `master` branch.

    NOTE: using a minor version shorthand (e.g. `7.16`) is not supported, as it is ambiguous.

    Example: assuming we are working on the release of 7.17.0, we can...

    * Create cards for changes between a previous Agent release and `master` (useful when preparing an initial RC):

        `$ ddev release testable 7.16.1 origin/master`

    * Create cards for changes between a previous RC and `master` (useful when preparing a new RC, and a separate
    release branch was not created yet):

        `$ ddev release testable 7.17.0-rc.2 origin/master`

    * Create cards for changes between a previous RC and a release branch (useful to only review changes in a
    release branch that has diverged from `master`):

        `$ ddev release testable 7.17.0-rc.4 7.17.x`

    * Create cards for changes between two arbitrary tags, e.g. between RCs:

        `$ ddev release testable 7.17.0-rc.4 7.17.0-rc.5`

    TIP: run with `ddev -x release testable` to force the use of the current directory.
    To avoid GitHub's public API rate limits, you need to set
    `github.user`/`github.token` in your config file or use the
    `DD_GITHUB_USER`/`DD_GITHUB_TOKEN` environment variables.


    See trello subcommand for details on how to setup access:

    `ddev release trello -h`.

"""    
    if new_root is not None:
        set_root(new_root)
    root = get_root()
    repo = basepath(root)
    if repo not in ('integrations-core', 'datadog-agent'):
        abort(f'Repo `{repo}` is unsupported.')

    commits = get_commits_between(base_ref, target_ref, root=root)
    num_changes = len(commits)

    if not num_changes:
        echo_warning('No changes.')
        return

    if repo == 'integrations-core':
        options = {
            '1': 'Integrations',
            '2': 'Containers',
            '3': 'Core',
            '4': 'Platform',
            '5': 'Tools and Libraries',
            's': 'Skip',
            'q': 'Quit',
        }
    else:
        options = {
            '1': 'Core',
            '2': 'Containers',
            '3': 'Logs',
            '4': 'Platform',
            '5': 'Networks',
            '6': 'Processes',
            '7': 'Trace',
            '8': 'Integrations',
            '9': 'Tools and Libraries',
            's': 'Skip',
            'q': 'Quit',
        }
    default_option = get_next(options)
    options_prompt = f'Choose an option (default {options[default_option]}): '
    options_text = '\n' + '\n'.join('{} - {}'.format(key, value) for key, value in options.items())

    commit_ids: Set[str] = set()
    user_config = ctx.obj
    trello = TrelloClient(user_config)

    teams = [
             'agent-core',
             'container-integrations',
             'logs-intake',            
             'agent-platform',        
             'networks',
             'processes',
             'agent-apm',                          
    ]


    trelloCardAssigner = TrelloCardAssigner(teams)
            
    for i, (commit_hash, commit_subject) in enumerate(commits, 1):
        commit_id = parse_pr_number(commit_subject)
        if commit_id is not None:
            api_response = get_pr(commit_id, user_config, raw=True)
            if api_response.status_code == 401:
                abort('Access denied. Please ensure your GitHub token has correct permissions.')
            elif api_response.status_code == 403:
                echo_failure(
                    'Error getting info for #{}. Please set a GitHub HTTPS '
                    'token to avoid rate limits.'.format(commit_id)
                )
                continue
            elif api_response.status_code == 404:
                echo_info(f'Skipping #{commit_id}, not a pull request...')
                continue

            api_response.raise_for_status()
            pr_data = api_response.json()
        else:
            try:
                api_response = get_pr_from_hash(commit_hash, repo, user_config, raw=True)
                if api_response.status_code == 401:
                    abort('Access denied. Please ensure your GitHub token has correct permissions.')
                elif api_response.status_code == 403:
                    echo_failure(
                        'Error getting info for #{}. Please set a GitHub HTTPS '
                        'token to avoid rate limits.'.format(commit_hash)
                    )
                    continue

                api_response.raise_for_status()
                pr_data = api_response.json()
                pr_data = pr_data.get('items', [{}])[0]
            # Commit to master
            except IndexError:
                pr_data = {
                    'number': commit_hash,
                    'html_url': f'https://github.com/DataDog/{repo}/commit/{commit_hash}',
                }
            commit_id = str(pr_data.get('number', ''))

        if commit_id and commit_id in commit_ids:
            echo_info(f'Already seen PR #{commit_id}, skipping it.')
            continue
        commit_ids.add(commit_id)

        pr_labels = sorted(get_pr_labels(pr_data))
        documentation_pr = False
        nochangelog_pr = True
        for label in pr_labels:
            if label.startswith('documentation'):
                documentation_pr = True

            if label.startswith(CHANGELOG_LABEL_PREFIX) and label.split('/', 1)[1] != CHANGELOG_TYPE_NONE:
                nochangelog_pr = False

        if documentation_pr and nochangelog_pr:
            echo_info(f'Skipping documentation {format_commit_id(commit_id)}.')
            continue

        pr_milestone = get_pr_milestone(pr_data)
        if milestone and pr_milestone != milestone:
            echo_info(f'Looking for milestone {milestone}, skipping {format_commit_id(commit_id)}.')
            continue

        pr_url = pr_data.get('html_url', f'https://github.com/DataDog/{repo}/pull/{commit_id}')
        pr_title = pr_data.get('title', commit_subject)
        pr_author = pr_data.get('user', {}).get('login', '')
        pr_body = pr_data.get('body', '')
        pr_num = pr_data.get('number', 0)

        trello_config = user_config['trello']
        if not (trello_config['key'] and trello_config['token']):
            abort('Error: You are not authenticated for Trello. Please set your trello ddev config')

        teams = [trello.label_team_map[label] for label in pr_labels if label in trello.label_team_map]
        if teams:
            create_trello_card(trello, trelloCardAssigner, teams, pr_num, pr_title,
                               pr_url, pr_labels, pr_body, dry_run, pr_author, user_config)
            continue

        finished = False
        choice_error = ''
        progress_status = f'({i} of {num_changes}) '
        indent = ' ' * len(progress_status)

        while not finished:
            echo_success(f'\n{progress_status}{pr_title}')

            echo_success('Url: ', nl=False, indent=indent)
            echo_info(pr_url)

            echo_success('Author: ', nl=False, indent=indent)
            echo_info(pr_author)

            echo_success('Labels: ', nl=False, indent=indent)
            echo_info(', '.join(pr_labels))

            if pr_milestone:
                echo_success('Milestone: ', nl=False, indent=indent)
                echo_info(pr_milestone)

            # Ensure Unix lines feeds just in case
            echo_info(pr_body.strip('\r'), indent=indent)

            echo_info(options_text)

            if choice_error:
                echo_warning(choice_error)

            echo_waiting(options_prompt, nl=False)

            # Terminals are odd and sometimes produce an erroneous null byte
            choice = '\x00'
            while choice == '\x00':
                choice = click.getchar().strip()

            if not choice:
                choice = default_option

            if choice not in options:
                echo_info(choice)
                choice_error = f'`{choice}` is not a valid option.'
                continue
            else:
                choice_error = ''

            value = options[choice]
            echo_info(value)

            if value == 'Skip':
                echo_info(f'Skipped {format_commit_id(commit_id)}')
                break
            elif value == 'Quit':
                echo_warning(f'Exited at {format_commit_id(commit_id)}')
                return
            else:
                create_trello_card(
                    trello, trelloCardAssigner, [
                        value], pr_num, pr_title, pr_url, pr_labels, pr_body, dry_run, pr_author, user_config
                )

            finished = True
    for team, stat in trelloCardAssigner.get_stats().items():
        print (team)
        for k, v in stat.items():
            print ("\t" + k, end =" ")
            for x in v:
                print (x, end =" ")
            print ()