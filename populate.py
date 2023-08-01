import random
import pandas as pd

# Charger le fichier cleaned_files_vars.csv (à adapter selon le chemin de votre fichier)
cleaned_data = pd.read_csv('cleaned_files_vars.csv')

# Définir la fonction pour générer les nouvelles métriques aléatoires
def generate_random_metrics(row):
    version = row['Version']
    file_path = row['Fichier']

    # Métriques pour chaque version
    lines_added = random.randint(0, 1000)
    lines_deleted = random.randint(0, 500)
    commits_changed = random.randint(0, 50)
    bug_fixing_commits = random.randint(0, commits_changed)
    commits_before_version = random.randint(0, 100)
    developers_changed = random.randint(1, 10)
    developers_before_version = random.randint(1, 20)
    average_time_between_changes = random.uniform(1.0, 10.0)
    average_developer_expertise = random.uniform(1.0, 100.0)
    minimum_developer_expertise = random.uniform(1.0, average_developer_expertise)

    # Ajouter les nouvelles métriques à la ligne
    row['LinesAdded'] = lines_added
    row['LinesDeleted'] = lines_deleted
    row['CommitsChanged'] = commits_changed
    row['BugFixingCommits'] = bug_fixing_commits
    row['CommitsBeforeVersion'] = commits_before_version
    row['DevelopersChanged'] = developers_changed
    row['DevelopersBeforeVersion'] = developers_before_version
    row['AverageTimeBetweenChanges'] = average_time_between_changes
    row['AverageDeveloperExpertise'] = average_developer_expertise
    row['MinimumDeveloperExpertise'] = minimum_developer_expertise

    return row

# Utiliser la fonction sur chaque ligne du dataframe pour générer les nouvelles métriques aléatoires
new_metrics_data = cleaned_data.apply(generate_random_metrics, axis=1)

# Sauvegarder les nouvelles métriques dans un nouveau fichier csv (à adapter selon le chemin souhaité)
new_metrics_data.to_csv('finale_vars_r.d.csv', index=False)
