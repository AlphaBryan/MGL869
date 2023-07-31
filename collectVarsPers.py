import os
import understand as und
import git

# ...

def collect_vars(self):
    if not (os.path.exists(self.bug_files_path) and \
            os.path.exists(self.git_local_repo_path)):
        return

    # Previously collected bugs
    collected_bugs = self.get_collected_bugs()

    # Build output file's header
    output_file_header = 'Version,CommitId,Fichier,ContientBogue,'
    metrics_file_header = open(self.metrics_file_path, 'r').readlines()[0]
    output_file_header += ','.join(metrics_file_header.split(',')[3:])
    output_file = open(self.files_vars_path, 'w')
    output_file.write(output_file_header)

    # Fetch files' versions from Git
    git_repo = git.Repo(self.git_local_repo_path)
    git_repo.git.reset('--hard')  # Reset local repo

    # Iterate over tags of HIVE's versions 2.0.0 and more: takes several hours
    for tag in git_repo.tags:
        version = self.parse_version(tag.name)  # HIVE's version related to tag
        if not version or int(version[0]) < 2:
            continue

        git_repo.git.checkout(tag.commit.hexsha, force=True)  # Restore local repo to tag's commit

        # Generate metrics with Understand Python API
        project = und.open(self.git_local_repo_path)
        for file in project.ents('File'):
            file_name = file.longname()
            if not file_name.endswith(('.h', '.cpp', '.java')):  # Only consider C++ and Java files
                continue

            file_metrics = ','.join(get_file_metrics(file))
            file_has_bug = (file_name, version) in collected_bugs
            # Print results in CSV output file
            line_start = version + ',' + tag.commit.hexsha + ',' + file_name
            output_file.write(line_start + ',' + str(file_has_bug) + ',' + file_metrics)

        project.close()

    output_file.close()  # Save output file

def get_file_metrics(file):
    metrics = []
    # Collect the metrics you need from the file entity
    # For example:
    metrics.append(str(file.metric('CountInput')))
    metrics.append(str(file.metric('CountOutput')))
    metrics.append(str(file.metric('CountPath')))
    metrics.append(str(file.metric('MaxNesting')))
    # Add more metrics as needed

    return metrics

# lauch the file code 
