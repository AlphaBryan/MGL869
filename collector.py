from datetime import datetime
import git
import os
import re
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
    # Path to CSV file listing versions per file per bug
    bug_files_path = './bug_files.csv'
    # Path to CSV file listing independent variables per file's versions
    files_vars_path = './files_vars.csv'
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
        bugs = {} # Dict of affected versions per bug
        output_file = open(self.bug_files_path, 'w')
        output_file.write('BugId,Fichier,Version\n')

        # Fetch bugs from JIRA
        url = req.urlopen(self.bugs_report_url)
        xmldoc = parse(url)
        for item in xmldoc.iterfind('channel/item'):
            bug_id = item.findtext('key')
            affected_versions = [elem.text for elem in item.findall('version')]
            bugs[bug_id] = affected_versions
        
        # Fetch files from Git
        if not os.path.exists(self.git_local_repo_path):
            # Cloning HIVE repository: takes a couple of minutes
            git.Git(self.git_local_repo_folder).clone(self.git_remote_repo_path)
        else:
            git_repo = git.Repo(self.git_local_repo_path)
            git_repo.git.reset('--hard') # Reset local repo
            git_repo.git.checkout('origin/master', force = True) # Restore to origin

        # Iterate over Git repo's commits
        for commit in git.Repo(self.git_local_repo_path).iter_commits():
            jira_id = re.search('HIVE-[0-9]+', commit.message)
            if not (jira_id and jira_id.group() in bugs): # Only consider commits refering to a JIRA bug
                continue

            bug_id = jira_id.group()
            files = commit.stats.files

            for file in files:
                file_ext = os.path.splitext(file)[-1].lower()
                if file_ext not in ['.h', '.cpp', '.java']: # Only consider C++ and Java files
                    continue
                
                for version in bugs[bug_id]: # One line per file's version with bug
                    version = self.parse_version(version) # HIVE's version related to file
                    if not version:
                        continue

                    # Print results in CSV output file
                    output_file.write(bug_id + ',' + os.path.basename(file) + ',' + version + '\n')

        output_file.close() # Save output file


    def parse_version(self, text):
        version = re.search('[0-9]+\.[0-9]+\.[0-9]', text)
        return version.group() if version else None


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

    
    def collect_vars(self):
        if not (os.path.exists(self.bug_files_path) and \
                os.path.exists(self.git_local_repo_path)):
            return

        # Previously collected bugs
        collected_bugs = self.get_collected_bugs()

        # Build output file's header
        output_file_header = 'Version,CommitId,Fichier,ContientBogue,'
        subprocess.run([self.und_exe, self.und_create_commands_path])
        metrics_file_header = open(self.metrics_file_path, 'r').readlines()[0]
        output_file_header += ','.join(metrics_file_header.split(',')[2:])
        output_file = open(self.files_vars_path, 'w')
        output_file.write(output_file_header)
        
        # Fetch files' versions from Git: takes severals minutes
        git_repo = git.Repo(self.git_local_repo_path)
        git_repo.git.reset('--hard') # Reset local repo

        # Iterate over tags of HIVE's versions 2.0.0 and more
        for tag in git_repo.tags: 
            tag_datetime = tag.commit.committed_datetime
            if tag_datetime < datetime(2016, 2, 15, 0, 0, 0, 0, tag_datetime.tzinfo):
                continue # Tags refer to a HIVE's version older than 2.0.0 release (2016-02-15)

            version = self.parse_version(tag.name) # HIVE's version related to tag
            if not version :
                continue

            git_repo.git.checkout(tag.commit.hexsha, force = True) # Restore local repo to tag's commit
            
            # Generate metrics with Understand
            subprocess.run([self.und_exe, self.und_analyze_commands_path])
            metrics_lines = open(self.metrics_file_path, 'r').readlines()
            if len(metrics_lines) < 1: # No metric was generated
                continue

            for line in metrics_lines[1:]:
                line_values = line.split(',')
                if line_values[0] != 'File': # Only consider File metrics
                    continue

                file_name = line_values[1]
                file_metrics = ','.join(line_values[2:])
                file_has_bug = (file_name, version) in collected_bugs
                # Print results in CSV output file
                line_start = version + ',' + tag.commit.hexsha + ',' + file_name
                output_file.write(line_start + ',' + str(file_has_bug) + ',' + file_metrics)

        output_file.close() # Save output file