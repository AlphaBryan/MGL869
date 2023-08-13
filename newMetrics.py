import pandas as pd
import subprocess
import os
from datetime import datetime

# Le mapping des versions vers les noms de tag Git
version_mapping = {
    "versions": {
        "1.2.1": ["release-1.2.1"],
        "2.0.0": ["release-2.0.0"],
        "2.0.1": ["release-2.0.1"],
        "2.1.0": ["release-2.1.0"],
        "2.2.0": ["release-2.2.0"],
        "2.3.0": ["release-2.3.0"],
        "2.3.1": ["release-2.3.1"],
        "2.3.2": ["release-2.3.2"],
        "2.3.3": ["release-2.3.3"],
        "2.3.4": ["release-2.3.4"],
        "2.3.5": ["release-2.3.5", "release-2.3.5-rc0"],
        "2.3.6": ["release-2.3.6"],
        "2.3.7": ["release-2.3.7"],
        "2.3.8": ["release-2.3.8", "release-2.3.8-rc0", "release-2.3.8-rc1", "release-2.3.8-rc2", "release-2.3.8-rc3"],
        "2.3.9": ["release-2.3.9", "release-2.3.9-rc0"],
        "2.4.0": ["rel/storage-release-2.4.0"],
        "2.5.0": ["rel/storage-release-2.5.0"],
        "2.6.0": ["rel/storage-release-2.6.0", "rel/storage-release-2.6.1"],
        "2.7.0": ["rel/storage-release-2.7.0-rc0", "rel/storage-release-2.7.0-rc1"],
        "2.7.2": ["rel/storage-release-2.7.2", "rel/storage-release-2.7.2-rc0", "rel/storage-release-2.7.2-rc1", ],
        "2.7.3": ["rel/storage-release-2.7.3", "rel/storage-release-2.7.3-rc0", "rel/storage-release-2.7.3-rc1", "rel/storage-release-2.7.3-rc2"],
        "2.8.0": ["storage-release-2.8.0-rc0"], 
        "2.8.1": ["storage-release-2.8.1", "storage-release-2.8.1-rc0", "storage-release-2.8.1-rc1", "storage-release-2.8.1-rc2"],
        "2.9.0": [],
        "3.0.0": ["rel/release-3.0.0", "rel/standalone-metastore-release-3.0.0"],
        "3.1.0": ["rel/release-3.1.0"],
        "3.1.2": ["rel/release-3.1.2-rc0"],
        "3.1.3": ["rel/release-3.1.3-rc0", "rel/release-3.1.3-rc1", "rel/release-3.1.3-rc2", "rel/release-3.1.3-rc3"],
        "3.2.0": [],
        "3.3.0": [],
        "3.4.0": [],
        "3.5.0": [],
        "3.6.0": [],
        "3.7.0": [],
        "3.8.0": [],
        "3.9.0": [],
        "4.0.0": ["rel/release-4.0.0-alpha-1", "rel/release-4.0.0-alpha-2", "rel/release-4.0.0-beta-1-rc0"]
    }
}

def get_previous_version(version):
    version_parts = version.split('.')
    last_digit = int(version_parts[-1])
    
    if last_digit > 0:
        version_parts[-1] = str(last_digit - 1)
        return '.'.join(version_parts)
    else:
        for mapped_version, tag_names in version_mapping['versions'].items():
            if version in tag_names:
                index = tag_names.index(version)
                if index > 0:
                    return tag_names[index - 1]
        # Si aucune version précédente n'est trouvée, utilisez la version 1.2.2
        return "1.2.1"

def get_output_from_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='utf-8')
    # print('get_output_from_command:', result)
    return result.stdout.encode('utf-8').decode('utf-8')

def map_version_to_git_tag(version):
    for mapped_version, tag_names in version_mapping['versions'].items():
        # print('map_version_to_git_tag:', mapped_version, tag_names)
        if mapped_version == version:  # Compare with the input version
            # print('map_version_to_git_tag  ss :', mapped_version== version)
            return tag_names[0]
            # for tag_name in tag_names:
            #     command = f'git rev-parse --verify --quiet {tag_name}'
            #     result = get_output_from_command(command)
            #     if result.strip() != "":
            #         return tag_name
    return None  # Si aucun tag ne correspond

# def map_version_to_git_tag(version):
#     for mapped_version, tag_names in version_mapping['versions'].items():
#         if mapped_version == version:  # Compare with the input version
#             print('map_version_to_git_tag:', mapped_version, tag_names)
#             # for tag_name in tag_names:
#             #     command = f'git rev-parse --verify --quiet {tag_name}'
#             #     result = get_output_from_command(command)
#             #     if result.strip() != "":
#             #         return tag_name
#             # break  # Stop searching after finding a match
#     return None  # If no matching tag is found

def get_file_path_from_name(file_name, version):
    command = ['git', 'ls-tree', '-r', version]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    lines = result.stdout.strip().split('\n')
    
    for line in lines:
        parts = line.split()
        if len(parts) >= 4 and file_name in parts[3]:
            return parts[3]  
    
    return file_name

# WORKING
# opitmisation possible, get le vrai version et file path dans au debut et pas a chaque fois
def get_added_deleted_lines(file_path, prev_version, version):
    # git_version = map_version_to_git_tag(version)
    # file_path = get_file_path_from_name(file_path, git_version) 
    prev_git_version = map_version_to_git_tag(prev_version)
    result = subprocess.run(['git', 'diff', '--numstat', prev_git_version, version, '--', file_path], capture_output=True, text=True, encoding='utf-8')
    lines = result.stdout.split('\n')
    added, deleted = 0, 0
    for line in lines:
        parts = line.split()
        if len(parts) == 3:
            added += int(parts[0])
            deleted += int(parts[1])
    return added, deleted

# WORKING
def get_bug_fixing_commits(file_path, version): 
    # keywords = ["fix", "bug", "patch", "error", "crash", "problem", "defect", "fault", "repair", "should"]
    command = f'git log --oneline --grep="fix\|bug\|patch\|error\|crash\|problem\|defect\|fault\|repair\|should" {version} -- {file_path}'
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    num_commits = len(result.stdout.split('\n')) - 1
    return num_commits

def get_commits_changing_file(file_path, version):
    command = f'git log --oneline {version} -- {file_path}'
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    num_commits = len(result.stdout.split('\n')) - 1
    return num_commits


def get_avg_time_between_commits(file_path, version):
    result = subprocess.run(['git', 'log', '--pretty=%ct', version, '--', file_path], capture_output=True, text=True, encoding='utf-8')
    timestamps = [int(t) for t in result.stdout.split('\n') if t]
    diffs = [timestamps[i] - timestamps[i+1] for i in range(len(timestamps)-1)]
    return 0 if not diffs else sum(diffs) / len(diffs)


def get_developer_expertise(file_path, version):
    result = subprocess.run(['git', 'log', '--pretty=%an', version, '--', file_path], capture_output=True, text=True, encoding='utf-8')
    devs = set(result.stdout.split('\n'))
    expertise = {}
    for dev in devs:
        dev_result = subprocess.run(['git', 'log', '--oneline', version, '--author='+dev], capture_output=True, text=True, encoding='utf-8')
        if dev_result.stdout is not None:
            expertise[dev] = len(dev_result.stdout.split('\n')) - 1

    if len(expertise) > 0:
        return sum(expertise.values()) / len(expertise), min(expertise.values())
    else:
        return 0, 0

def get_developers_changing_file(file_path, version):
    result = subprocess.run(['git', 'log', '--pretty=%an', version, '--', file_path], capture_output=True, text=True, encoding='utf-8')
    devs = set(result.stdout.split('\n'))
    return len(devs)

def main():
    git_local_repo_path = 'C:/Users/bryan/Documents/GitHub/hive'
    files_vars_path = 'C:/Users/bryan/Documents/GitHub/ETS/MGL869/cleaned_files_vars.csv'
    
    os.chdir(git_local_repo_path)
    subprocess.run(['git', 'pull', 'origin', 'master'])
    
    df = pd.read_csv(files_vars_path)
    df = df.head(5)

    for index, row in df.iterrows():
        print(index)
        file_path = row['Fichier']
        version = row['Version']
        prev_version = get_previous_version(version)
    
        git_version = map_version_to_git_tag(version)
        file_path = get_file_path_from_name(file_path, git_version) 
        print(file_path)
        
        df.at[index, 'AddedLines'], df.at[index, 'DeletedLines'] = get_added_deleted_lines(file_path, prev_version, git_version) # Lignes ajoutées et supprimées
        df.at[index, 'NumCommits'] = get_commits_changing_file(file_path, git_version) # Commits qui ont modifié le fichier
        df.at[index, 'BugFixingCommits'] = get_bug_fixing_commits(file_path, git_version) # Commits qui ont fix un bug
        df.at[index, 'DevelopersCount'] = get_developers_changing_file(file_path, git_version) #Dev qui ont modifié le fichier
        df.at[index, 'AvgTimeBetweenCommits'] = get_avg_time_between_commits(file_path, git_version) # Temps moyen entre les commits
        df.at[index, 'AvgDeveloperExpertise'], df.at[index, 'MinDeveloperExpertise'] = get_developer_expertise(file_path, git_version) # Expertise des devs qui ont modifié le fichier
        
    output_path = 'C:/Users/bryan/Documents/GitHub/ETS/MGL869/cleaned_files_newMetrics.csv'
    df.to_csv(output_path, index=False)
    print(df)

if __name__ == "__main__":
    main()
