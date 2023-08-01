import math
import pandas as pd
import git

class CollectNewMetrics:
    def __init__(self, cleaned_files_vars_path, git_local_repo_path):
        self.cleaned_files_vars_path = cleaned_files_vars_path
        self.git_local_repo_path = git_local_repo_path

    def count_commits_before(self, commits_list, current_commit_id):
        commit_index = None
        for index, commit_id in enumerate(commits_list):
            if commit_id == current_commit_id:
                commit_index = index
                break

        if commit_index is None or commit_index == 0:
            return 0

        previous_commit_id = commits_list[commit_index - 1]
        commits_before_version = list(self.git_repo.iter_commits('{}..{}'.format(previous_commit_id, current_commit_id)))
        return len(commits_before_version)

    def calculate_new_metrics(self):
        cleaned_data = pd.read_csv(self.cleaned_files_vars_path)
        self.git_repo = git.Repo(self.git_local_repo_path)

        # Function to calculate the number of lines added and deleted for each version and file
        def count_lines_added_deleted(file_data):
            file_data['LinesAdded'] = file_data['CountLineCode'] - file_data['AltCountLineCode']
            file_data['LinesDeleted'] = file_data['AltCountLineCode'] - file_data['CountLineCode']
            return file_data

        # Function to count the number of commits that changed the file in each version
        def count_commits_per_version(file_data):
            version_commits_count = file_data.groupby('Version')['CommitId'].nunique().reset_index()
            version_commits_count.rename(columns={'CommitId': 'CommitsChanged'}, inplace=True)
            file_data = pd.merge(file_data, version_commits_count, on='Version', how='left')
            return file_data

        # Function to count the number of bug-fixing commits per version and file
        def count_bug_fixing_commits(file_data):
            git_repo = git.Repo(self.git_local_repo_path)
            bug_keywords = ["fix", "bug"]
            file_data['BugFixingCommits'] = 0

            for index, row in file_data.iterrows():
                file_path = row['Fichier']
                version = row['Version']
                commit_id = row['CommitId']

                file_commits = git_repo.iter_commits('--all', paths=file_path)

                for commit in file_commits:
                    if commit.hexsha == commit_id:  # Skip current commit
                        continue

                    commit_message = commit.message.lower()
                    for keyword in bug_keywords:
                        if keyword in commit_message:
                            file_data.at[index, 'BugFixingCommits'] += 1
                            break

            return file_data

        # Function to count the number of commits changing the file in current version and all previous versions
        def count_commits_before_version(file_data):
            version_commits = file_data.groupby('Version')['CommitId'].apply(list).reset_index()
            version_commits.rename(columns={'CommitId': 'CommitsList'}, inplace=True)
            file_data = pd.merge(file_data, version_commits, on='Version', how='left')

            file_data['CommitsBeforeVersion'] = file_data.apply(
                lambda row: self.count_commits_before(row['CommitsList'], row['CommitId']), axis=1
            )

            file_data.drop('CommitsList', axis=1, inplace=True)
            return file_data

        # Function to count the number of developers changing the file in each version
        def count_unique_developers_per_version(file_data):
            version_dev_count = file_data.groupby('Version')['CommitId'].apply(
                lambda x: len(set(self.git_repo.git.show("--format='%ae'", *x.unique().tolist()).split()))
            ).reset_index()
            version_dev_count.rename(columns={'CommitId': 'DevelopersChanged'}, inplace=True)
            file_data = pd.merge(file_data, version_dev_count, on='Version', how='left')
            return file_data

        # Function to count the number of developers changing the file in current version and all previous versions
        def count_unique_developers_before_version(file_data):
            version_devs = file_data.groupby('Version')['CommitId'].apply(
                lambda x: set(self.git_repo.git.show("--format='%ae'", *x.unique().tolist()).split())
            ).reset_index()
            version_devs.rename(columns={'CommitId': 'DevelopersList'}, inplace=True)
            file_data = pd.merge(file_data, version_devs, on='Version', how='left')

            file_data['DevelopersBeforeVersion'] = file_data.apply(
                lambda row: len(set.union(*[dev_set for dev_set in row['DevelopersList'] if row['CommitId'] not in dev_set])),
                axis=1
            )

            file_data.drop('DevelopersList', axis=1, inplace=True)
            return file_data

        # Function to calculate the average time between changes in each version
        def calculate_average_time_between_changes(file_data):
            version_commits = file_data.groupby('Version')['CommitId'].apply(list).reset_index()
            version_commits.rename(columns={'CommitId': 'CommitsList'}, inplace=True)
            file_data = pd.merge(file_data, version_commits, on='Version', how='left')

            file_data['TimeBetweenChanges'] = file_data.apply(
                lambda row: self.calculate_average_time(row['CommitsList']), axis=1
            )

            file_data.drop('CommitsList', axis=1, inplace=True)
            return file_data

        # Function to calculate the average expertise of developers for each file in each version
        def calculate_average_developer_expertise(file_data):
            version_commits = file_data.groupby('Version')['CommitId'].apply(list).reset_index()
            version_commits.rename(columns={'CommitId': 'CommitsList'}, inplace=True)
            file_data = pd.merge(file_data, version_commits, on='Version', how='left')

            file_data['AverageDeveloperExpertise'] = file_data.apply(
                lambda row: self.calculate_average_expertise(row['CommitsList'], row['CommitId']), axis=1
            )

            file_data.drop('CommitsList', axis=1, inplace=True)
            return file_data

        # Function to calculate the minimum expertise of developers for each file in each version
        def calculate_minimum_developer_expertise(file_data):
            version_commits = file_data.groupby('Version')['CommitId'].apply(list).reset_index()
            version_commits.rename(columns={'CommitId': 'CommitsList'}, inplace=True)
            file_data = pd.merge(file_data, version_commits, on='Version', how='left')

            file_data['MinimumDeveloperExpertise'] = file_data.apply(
                lambda row: self.calculate_minimum_expertise(row['CommitsList'], row['CommitId']), axis=1
            )

            file_data.drop('CommitsList', axis=1, inplace=True)
            return file_data

        # Calculate average time between commits for a list of commit ids
        def calculate_average_time(commit_list):
            times = [self.git_repo.git.log('-n 1', '--format=%ct', commit) for commit in commit_list]
            times = [int(time) for time in times if time.strip().isdigit()]
            if len(times) < 2:
                return math.nan

            average_time = sum([times[i] - times[i-1] for i in range(1, len(times))]) / (len(times))
            return average_time

        # Calculate average expertise of developers for a list of commit ids
        def calculate_average_expertise(commit_list, current_commit):
            expertise_values = []
            for commit in commit_list:
                if commit == current_commit:
                    continue

                try:
                    file_diff = self.git_repo.git.diff(commit + '^..' + commit, '--', file_path)
                    expertise_value = self.calculate_expertise_from_diff(file_diff)
                    expertise_values.append(expertise_value)
                except Exception as e:
                    print("Error calculating expertise for commit {} and file {}: {}".format(commit, file_path, e))

            if not expertise_values:
                return math.nan

            return sum(expertise_values) / len(expertise_values)

        # Calculate minimum expertise of developers for a list of commit ids
        def calculate_minimum_expertise(commit_list, current_commit):
            expertise_values = []
            for commit in commit_list:
                if commit == current_commit:
                    continue

                try:
                    file_diff = self.git_repo.git.diff(commit + '^..' + commit, '--', file_path)
                    expertise_value = self.calculate_expertise_from_diff(file_diff)
                    expertise_values.append(expertise_value)
                except Exception as e:
                    print("Error calculating expertise for commit {} and file {}: {}".format(commit, file_path, e))

            if not expertise_values:
                return math.nan

            return min(expertise_values)

        # Calculate expertise from the git diff output
        def calculate_expertise_from_diff(diff_output):
            added_lines = 0
            deleted_lines = 0

            lines = diff_output.splitlines()
            for line in lines:
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deleted_lines += 1

            total_lines = added_lines + deleted_lines
            if total_lines == 0:
                return 0

            expertise_value = added_lines / total_lines
            return expertise_value

        # Utilisation de la classe CollectNewMetrics pour calculer les nouvelles métriques
        print("Starting metrics calculation...")
        print("Reading data from '{}'...".format(self.cleaned_files_vars_path))
        new_metrics_data = cleaned_data.copy()

        # Calculating 'LinesAdded' and 'LinesDeleted'
        if 'CountLineCode' in new_metrics_data.columns and 'AltCountLineCode' in new_metrics_data.columns:
            print("Calculating 'LinesAdded' and 'LinesDeleted'...")
            new_metrics_data = count_lines_added_deleted(new_metrics_data)
        else:
            print("Skipping 'LinesAdded' and 'LinesDeleted' calculation as required columns are missing.")

        # Calculating 'CommitsChanged'
        print("Calculating 'CommitsChanged'...")
        new_metrics_data = count_commits_per_version(new_metrics_data)

        # Calculating 'BugFixingCommits'
        print("Calculating 'BugFixingCommits'...")
        new_metrics_data = count_bug_fixing_commits(new_metrics_data)

        # Calculating 'CommitsBeforeVersion'
        print("Calculating 'CommitsBeforeVersion'...")
        new_metrics_data = count_commits_before_version(new_metrics_data)

        # Calculating 'DevelopersChanged'
        print("Calculating 'DevelopersChanged'...")
        new_metrics_data = count_unique_developers_per_version(new_metrics_data)

        # Calculating 'DevelopersBeforeVersion'
        print("Calculating 'DevelopersBeforeVersion'...")
        new_metrics_data = count_unique_developers_before_version(new_metrics_data)

        # Calculating 'AverageTimeBetweenChanges'
        print("Calculating 'AverageTimeBetweenChanges'...")
        new_metrics_data = calculate_average_time_between_changes(new_metrics_data)

        # Calculating 'AverageDeveloperExpertise'
        print("Calculating 'AverageDeveloperExpertise'...")
        new_metrics_data = calculate_average_developer_expertise(new_metrics_data)

        # Calculating 'MinimumDeveloperExpertise'
        print("Calculating 'MinimumDeveloperExpertise'...")
        new_metrics_data = calculate_minimum_developer_expertise(new_metrics_data)

        print("Metrics calculation completed.")
        return new_metrics_data

if __name__ == "__main__":
    # Utilisation de la classe CollectNewMetrics pour calculer les nouvelles métriques
    cleaner = CollectNewMetrics('cleaned_files_vars.csv', 'C:/Users/elwin/OneDrive/Documents/ETS/mglDevops/hive')
    new_metrics_data = cleaner.calculate_new_metrics()

    # Écrire les nouvelles métriques dans le fichier finale_vars.csv
    new_metrics_data.to_csv('finale_vars.csv', index=False)
