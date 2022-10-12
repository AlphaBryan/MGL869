import git
import os
import re
import shutil
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
            jira_id = re.search('HIVE-[0-9]+', commit.message)
            if not jira_id or not jira_id.group() in bugs:
                continue

            bug_id = jira_id.group()
            files = commit.stats.files

            for file in files:
                file_ext = os.path.splitext(file)[-1].lower()
                if file_ext not in ['.cpp', '.java']: # Only consider C++ and Java files
                    continue
                
                # Print results in CSV output file
                output_file.write(bug_id + ',' + file + '\n')

        output_file.close() # Save output file

    
    def collect_vars(self):
        if not (os.path.exists(self.bug_files_path) and \
                os.path.exists(self.git_local_repo_path)):
            return

        output_file = open(self.files_vars_path, 'w')
        output_file.write('Version,CommitId,Fichier\n')

        # Initialize Understand project's folder
        if os.path.exists(self.und_project):
            shutil.rmtree(self.und_project)
        os.mkdir(self.und_project)    

        # Fetch files from input file
        files = set() # Set of files
        # Input CSV file in format bug_id;file_path
        input_file = open(self.bug_files_path, 'r')
        for line in input_file.read().splitlines()[1:]:
            line_values = line.split(',')
            if len(line_values) <= 1:
                continue

            files.add(line_values[-1]) # Add file to files set
        
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

            for f in files:
                file_commits = list(git_repo.iter_commits(paths = f)) # File's commits in branch
                if not file_commits: # No commit for file
                    continue

                file_last_commit = sorted(file_commits, key=lambda c: c.committed_datetime)[-1]

                # Add file's version content as code file in Understand project
                code_file_name = version + '_' + f.replace('/', '_')
                code_file = open(self.und_project + '/' + code_file_name, 'wb')
                code_file.write((file_last_commit.tree / f).data_stream.read())
                code_file.close()

                # Print results in CSV output file
                output_file.write(version + ',' + file_last_commit.hexsha + ',' + f + '\n')

        git_repo.git.reset('--hard') # Reset local repo
        output_file.close() # Save output file