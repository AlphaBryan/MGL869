import git
import os
import re
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


    def __init__(self, bugs_to_collect, vars_to_collect):
        self.bugs_to_collect = bugs_to_collect
        self.vars_to_collect = vars_to_collect


    def collect(self):
        if not (self.bugs_to_collect or self.vars_to_collect):
            return

        if self.bugs_to_collect:
            self.collect_bugs()


    def collect_bugs(self):
        bugs = [] # List of bugs
        # Output CSV file in format bug_id;file_path
        output_file = open('./bug_files.csv', 'w')
        output_file.write('Bogue,Fichier\n')

        # Fetch bugs from JIRA
        url = req.urlopen(self.bugs_report_url)
        xmldoc = parse(url)
        for item in xmldoc.iterfind('channel/item'):
            bug_id = item.findtext('key')
            bugs += [bug_id]
        
        # Fetch files from Git
        if not os.path.exists(self.git_local_repo_path):
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

                output_file.write(bug_id + ',' + file + '\n')

        output_file.close() # Save output file