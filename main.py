import gspread
from oauth2client.service_account import ServiceAccountCredentials

import requests
from datetime import datetime, timedelta, timezone

scopes = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "PYTHON PROJECTS/git_check/credentials.json", scopes)
client = gspread.authorize(creds)

spreadsheet = client.open("Testing").worksheet("Sheet1")
request_data = spreadsheet.get_all_values()

usernames = []
for row in request_data[1:]:  # Skip the first row which contains column headers
    usernames.append(row[1])


def get_total_commits(username):
    base_url = f"https://api.github.com/users/{username}/repos"

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    response = requests.get(base_url, headers=headers)
    while response.status_code != 200:
        response = requests.get(base_url)

    if response.status_code == 200:
        repos = response.json()
        total_commits = 0
        today = datetime.now().replace(tzinfo=timezone.utc)
        last_month = (datetime.now() - timedelta(days=30)
                      ).replace(tzinfo=timezone.utc)

        for repo in repos:

            commits_count = get_commits_count(
                username, repo['name'], today, last_month)

            total_commits += commits_count if commits_count is not None else 0

        return total_commits
    else:
        return None


def get_commits_count(username, repo, since, until):
    base_url = f"https://api.github.com/repos/{username}/{repo}/commits"

    count = 0
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    response = requests.get(base_url, headers=headers)
    while response.status_code != 200:
        response = requests.get(base_url)
    data = response.json()

    if response.status_code == 200:
        if isinstance(data, list) and len(data) > 0:
            # Iterate through each commit and extract the date
            for commit in data:
                commit_date = commit['commit']['author']['date']

                commit_date = datetime.fromisoformat(commit_date)

                if until <= commit_date < since:
                    count += 1
        return count


# username = 'Netherquark'  # Replace 'username' with the GitHub username
for username in usernames:

    total_commits = get_total_commits(username)

    if total_commits is not None:
        print("Total number of commits in the last month across all repos of",
              username, ":", total_commits)
    else:
        print("Failed to fetch total commits count.")
