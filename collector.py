import git
import os
import re
import shutil
import subprocess
import urllib.request as req
from xml.etree.ElementTree import parse


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
    git_local_repo_folder = '../'
    git_local_repo_path = git_local_repo_folder + git_repo_name
    # Path to CSV file listing files per bug
    bug_files_path = './bug_files.csv'
    # Path to CSV file listing independent variables per file's versions
    files_vars_path = './files_vars.csv'
    # Path to Understand project folder
    und_project = './und_project'
    # Path to Understand .exe
    und_exe = '../scitools/bin/linux64/und'
    # Path to Understand commands files
    und_create_commands_path = './undCreateCommands.txt'
    und_analyze_commands_path = './undAnalyzeCommands.txt'
    # Path to metrics file
    metrics_file_path = './metrics.csv'

    def __init__(self, bugs_to_collect, vars_to_collect):
        self.bugs_to_collect = bugs_to_collect
        self.vars_to_collect = vars_to_collect


    def collect(self):
        if not (self.bugs_to_collect or self.vars_to_collect):
            return

        if self.bugs_to_collect:
            self.collect_bugs()
        if self.vars_to_collect:
            self.collect_vars()


    def collect_bugs(self):
        bugs = [] # List of bugs
        output_file = open(self.bug_files_path, 'w')
        output_file.write('BugId,Fichier\n')

        # Fetch bugs from JIRA
        url = req.urlopen(self.bugs_report_url)
        xmldoc = parse(url)
        for item in xmldoc.iterfind('channel/item'):
            bug_id = item.findtext('key')
            bugs += [bug_id]
        
        # Fetch files from Git
        if not os.path.exists(self.git_local_repo_path):
            # Cloning HIVE repository: takes a couple of minutes
            git.Git(self.git_local_repo_folder).clone(self.git_remote_repo_path)
        else:
            git.Repo(self.git_local_repo_path).remotes.origin.pull()
        # Iterate over Git repo's commits
        for commit in git.Repo(self.git_local_repo_path).iter_commits():
            jira_id = self.parse_jira_id(commit)
            if not jira_id in bugs:
                continue

            files = commit.stats.files
            for file in files:
                if not self.to_consider(file):
                    continue
                    
                # Print results in CSV output file
                output_file.write(jira_id + ',' + file + '\n')

        output_file.close() # Save output file


    def parse_jira_id(self, commit):
        jira_id = re.search('HIVE-[0-9]+', commit.message)
        return jira_id.group() if jira_id else None


    def to_consider(self, file):
        file_ext = os.path.splitext(file)[-1].lower()
        return file_ext in ['.cpp', '.java'] # Only C++ and Java files are considered


    def get_collected_bugs(self):
        if not os.path.exists(self.bug_files_path):
            return None
        
        bug_files = set() # Set of bugs_id,file pairs
        # Input CSV file in format bug_id;file_path
        input_file = open(self.bug_files_path, 'r')
        for line in input_file.read().splitlines()[1:]:
            line_values = line.split(',')
            if len(line_values) <= 1:
                continue
                
            bug_file = (line_values[0], line_values[1])
            bug_files.add(bug_file) # Add bug_id,file pair to set

        return bug_files

    
    def collect_vars(self):
        if not (os.path.exists(self.bug_files_path) and \
                os.path.exists(self.git_local_repo_path)):
            return

        # Previously collected bugs
        collected_bugs = self.get_collected_bugs()

        # Initialize Understand project's folder
        if os.path.exists(self.und_project):
            shutil.rmtree(self.und_project)
        os.mkdir(self.und_project)

        # Build output file's header
        output_file = open(self.files_vars_path, 'w')
        output_file.write(self.labelize_collected_vars())
        
        # Fetch files' versions from Git: takes severals minutes
        git_repo = git.Repo(self.git_local_repo_path)
        git_repo.git.reset('--hard') # Reset local repo

        for branch in git_repo.remote().refs:
            branch_name = branch.name
            # Ignore branches not mentioning 'branch' nor 'release'
            if 'branch' not in branch_name and 'release' not in branch_name:
                continue

            branch_version = re.search('[0-9]+\.[0-9]+\.[0-9]*', branch_name)
            if not branch_version:
                continue

            version = branch_version.group() # HIVE's version related to branch
            git_repo.git.checkout(branch_name) # Restore local repo to given branch

            # Iterate over all files in repo
            for blob in git_repo.tree().traverse():
                f = blob.path # Path to file related to blob in repo tree
                if not self.to_consider(f):
                    continue

                # Only iterate over last commit of each file
                for commit in git_repo.iter_commits(paths = f, max_count = 1):
                    # Add file's version content as code file in Understand project
                    code_file_path = self.und_project + '/' + os.path.basename(f)
                    code_file = open(code_file_path, 'wb')
                    code_file.write((commit.tree / f).data_stream.read())
                    code_file.close()

                    # Generate metrics with Understand
                    subprocess.run([self.und_exe, self.und_analyze_commands_path])
                    metrics = open(self.metrics_file_path, 'r').readlines()
                    if len(metrics) < 1: # No metrics were generated
                        continue
                    
                    file_metrics = ','.join(metrics[1].split(',')[2:])
                    
                    # Delete code file
                    os.remove(code_file_path)
                    # Check if file's version has bug
                    bug_detected = (self.parse_jira_id(commit), f) in collected_bugs
                    # Print results in CSV output file
                    line_start = version + ',' + commit.hexsha + ',' + f + ',' + str(bug_detected)
                    output_file.write(line_start + ',' + file_metrics)


        git_repo.git.reset('--hard') # Reset local repo
        output_file.close() # Save output file


    def labelize_collected_vars(self):
        # Return the header for collected vars output file
        labels = 'Version,CommitId,Fichier,ContientBogue,'
        subprocess.run([self.und_exe, self.und_create_commands_path])
        metrics_file_header = open(self.metrics_file_path, 'r').readlines()[0]
        labels += ','.join(metrics_file_header.split(',')[2:])

        return labels
