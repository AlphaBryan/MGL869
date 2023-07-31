import pandas as pd
import git
from git import Repo
import os
import time
import datetime
from collections import defaultdict

def extract_metrics(repo, commit, file):
    added_lines = 0
    deleted_lines = 0
    modified_file = False
    for diff in commit.diff(commit.parents or git.NULL_TREE, create_patch=True).iter_change_type('M'):
        if diff.a_path == file or diff.b_path == file:
            modified_file = True
            for line in diff.diff.decode('utf-8').split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deleted_lines += 1
    return modified_file, added_lines, deleted_lines

def collect_metrics():
    git_remote_repo_path = 'https://github.com/apache/hive'
    git_local_repo_path = 'C:/Users/elwin/OneDrive/Documents/ETS/mglDevops/hive'
    files_vars_path = './files_vars.csv'

    # Load existing commits
    existing_data_df = pd.read_csv(files_vars_path, delimiter=';')

    repo = Repo(git_local_repo_path)
    all_files = []
    file_modifications = defaultdict(list)
    file_developers = defaultdict(set)

    counter = 0 ; 
    # Loop over each row in the CSV data
    for _, row in existing_data_df.iterrows():
        counter+=1
        if counter == 2:
            break 
        commit_hexsha = row["CommitId"]
        file = row["Fichier"]
        print(f"Processing commit {commit_hexsha}, file {file}")

        # Get the commit from the repo
        commit = repo.commit(commit_hexsha)
        print(f"commit {commit.stats}")


        # Check if the file was modified in this commit
        modified_file, added_lines, deleted_lines = extract_metrics(repo, commit, file)
        if modified_file:
            print('ok')
            metrics = {}
            metrics["CommitId"] = commit.hexsha
            metrics["Fichier"] = file
            metrics["message"] = commit.message
            metrics["timestamp"] = commit.committed_date
            metrics["author"] = commit.author.name
            metrics["ContientBogue"] = any(keyword in commit.message for keyword in ["fix", "bug", "issue"])
            metrics["modified_file"] = modified_file
            metrics["added_lines"] = added_lines
            metrics["deleted_lines"] = deleted_lines
            file_modifications[file].append(metrics)
            all_files.append(metrics)

            # Add the commit's author to the set of developers for this file
            file_developers[file].add(commit.author.name)
            print(f"file_developers {file_developers}")
            

    df = pd.DataFrame(all_files)

    # post-processing to compute additional metrics
    for file, modifications in file_modifications.items():
        modifications.sort(key=lambda x: x["timestamp"])
        num_commits = len(modifications)
        num_authors = len(set(x["author"] for x in modifications))
        num_developers = len(file_developers[file])
        avg_time_between_modifications = 0
        if num_commits > 1:
            times_between_modifications = [(modifications[i]["timestamp"] - modifications[i - 1]["timestamp"]) for i in range(1, num_commits)]
            avg_time_between_modifications = sum(times_between_modifications) / len(times_between_modifications)

        df.loc[(df["CommitId"] == modifications[0]["CommitId"]) & (df["Fichier"] == file), "num_commits"] = num_commits
        df.loc[(df["CommitId"] == modifications[0]["CommitId"]) & (df["Fichier"] == file), "num_authors"] = num_authors
        df.loc[(df["CommitId"] == modifications[0]["CommitId"]) & (df["Fichier"] == file), "num_developers"] = num_developers
        df.loc[(df["CommitId"] == modifications[0]["CommitId"]) & (df["Fichier"] == file), "avg_time_between_modifications"] = avg_time_between_modifications

    return df

new_metrics_df = collect_metrics()
print('new_metrics_df',new_metrics_df)
print('new_metrics_df.columns',new_metrics_df.columns)

files_vars_path = './files_vars.csv'

# Load existing commits
# existing_data_df = pd.read_csv(files_vars_path, delimiter=';')
# Merge the new metrics with the existing data
# merged_df = pd.merge(existing_data_df, new_metrics_df, how='left', left_on=["CommitId", "Fichier"], right_on=["CommitId", "Fichier"])

# Save the merged data to a new CSV file
# merged_df.to_csv("merged_files_vars.csv", index=False)
