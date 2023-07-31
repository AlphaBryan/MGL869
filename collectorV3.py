from datetime import datetime
import git
import os
import re
import subprocess
import urllib.request as req
from xml.etree.ElementTree import parse
import time
# from subprocess import Popen, TimeoutExpired
from subprocess import Popen, PIPE, TimeoutExpired, DEVNULL

class Collector:
    bugs_to_collect = False
    vars_to_collect = False
    # JIRA XML bugs report for Hive project:
    #   - impacted releases defined
    #   - published releases only
    #   - releases >= 2.0.0
    #   - resolved bugs only
    bugs_report_url = 'https://issues.apache.org/jira/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?jqlQuery=project+%3D+HIVE+AND+issuetype+%3D+Bug+AND+status+%3D+Resolved+AND+affectedVersion+in+releasedVersions%28%29+AND+affectedVersion+%3E%3D+2.0.0'
    # Git repository of Hive project
    git_repo_name = 'hive'
    git_remote_repo_path = 'https://github.com/apache/' + git_repo_name
    # git_local_repo_folder = '../'
    git_local_repo_folder = 'C:/Users/elwin/OneDrive/Documents/ETS/mglDevops/'
    git_local_repo_path = git_local_repo_folder + git_repo_name
    # Path to CSV file listing versions per file per bug
    bug_files_path = './bug_files.csv'
    # Path to CSV file listing independent variables per file's versions
    files_vars_path = './files_varsTest.csv'
    # Path to Understand .exe
    # und_exe = '../scitools/bin/linux64/und'
    und_exe = 'C:/Program Files/SciTools/bin/pc-win64/und.exe'
    # Path to Understand commands files
    und_create_commands_path = './undCreateCommands.txt'
    und_analyze_commands_path = './undAnalyzeCommands.txt'
    # Path to metrics file
    metrics_file_path = './metrics.csv'

    def collect_vars(self):
        print('Start collect vars')
        if not (os.path.exists(self.bug_files_path) and \
                os.path.exists(self.git_local_repo_path)):
            print('collect vars Forced stop')
            return

        # Previously collected bugs
        collected_bugs = self.get_collected_bugs()

        # Build output file's header
        output_file_header = 'Version,CommitId,Fichier,ContientBogue,'
        # subprocess.run([self.und_exe, self.und_create_commands_path])
        metrics_file_header = open(self.metrics_file_path, 'r').readlines()[0]
        output_file_header += 'NbrCommits,LinesAdded,LinesRemoved,' + ','.join(metrics_file_header.split(',')[3:])
        output_file = open(self.files_vars_path, 'w')
        output_file.write(output_file_header)

        # Fetch files' versions from Git
        git_repo = git.Repo(self.git_local_repo_path)
        git_repo.git.reset('--hard') # Reset local repo

        prev_tag = None # Previous tag
        for tag in git_repo.tags:
            print('Iteration tag:', tag)
            version = self.parse_version(tag.name) # HIVE's version related to tag
            if not version or int(version[0]) < 2:
                prev_tag = tag
                continue

            # Generate metrics with Understand
            print('Process Generate metrics start for tag:', tag)
            git_repo.git.checkout(tag.commit.hexsha, force=True) # Restore local repo to tag's commit
            start_time = time.time()

            # Here is where we add the new metrics
            num_commits, lines_added, lines_removed = self.get_metrics_for_file(git_repo, self.file_path, prev_tag.commit.hexsha, tag.commit.hexsha)

            # try:
            #     process = Popen([self.und_exe, self.und_analyze_commands_path], stdout=DEVNULL, stderr=DEVNULL)
            #     # Wait for one hour
            #     stdout, stderr = process.communicate(timeout=3600)
            # except TimeoutExpired:
            #     process.kill()
            #     stdout, stderr = process.communicate()
            #     print("The command took too long to run and was terminated.")

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"The command took {execution_time} seconds to run.")
            print('Process Generate metrics end for tag:', tag)

            metrics_lines = open(self.metrics_file_path, 'r').readlines()
            if len(metrics_lines) < 1: # No metric was generated
                prev_tag = tag
                continue

            for line in metrics_lines[1:]:
                line_values = line.split(',')
                if len(line_values) < 3:  # Make sure there are at least 3 elements
                    continue
                if line_values[0] not in ('File', 'Method', 'Class'): # Only consider File, Method and Class metrics
                    continue

                file_name = line_values[2] # MetricShowDeclaredInFile setting puts file name in 3rd column
                file_metrics = ','.join(line_values[3:])
                file_has_bug = (file_name, version) in collected_bugs
                # Print results in CSV output file
                line_start = version + ',' + tag.commit.hexsha + ',' + file_name
                output_file.write(line_start + ',' + str(num_commits) + ',' + str(lines_added) + ',' + str(lines_removed) + ',' + str(file_has_bug) + ',' + file_metrics)

            prev_tag = tag

        output_file.close() # Save output file

    def get_metrics_for_file(self, repo, file_path, start_commit, end_commit):
        print('trying to get more metrics')
        # Get the number of commits that modified the file
        num_commits = sum(1 for commit in repo.iter_commits(paths=file_path))

        # Get the number of lines added/removed in the file
        diff_index = repo.commit(end_commit).diff(repo.commit(start_commit))
        file_diff = [d for d in diff_index.iter_change_type('M') if d.a_path == file_path]
        if file_diff:
            lines_added = file_diff[0].added
            lines_removed = file_diff[0].removed
        else:
            lines_added = lines_removed = 0

        return num_commits, lines_added, lines_removed
    
    def get_collected_bugs(self):
        if not os.path.exists(self.bug_files_path):
            return None
        
        file_bugs = {} # Dict of bugs per (file, version) pair
        # Input CSV file in format bug_id,file_name,file_version
        input_file = open(self.bug_files_path, 'r')
        for line in input_file.read().splitlines()[1:]:
            line_values = line.split(',')
            if len(line_values) <= 1:
                continue

            bug_id = line_values[0]
            bug_file = (line_values[1], line_values[2])

            if bug_file in file_bugs:
                file_bugs[bug_file] += [bug_id]
            else:
                file_bugs[bug_file] = [bug_id]

        return file_bugs
    
    def parse_version(self, text):
        version = re.search('[0-9]+\.[0-9]+\.[0-9]', text)
        return version.group() if version else None
if __name__ == "__main__":
    collector = Collector()
    collector.collect_vars()