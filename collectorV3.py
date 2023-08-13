import pandas as pd
import git
from datetime import datetime

# Charger les informations de base à partir du fichier CSV "cleaned_files_vars.csv"
base_info_df = pd.read_csv("cleaned_files_vars.csv")

# Variables du repo Git
git_repo_name = 'hive'
git_remote_repo_path = 'https://github.com/apache/' + git_repo_name
git_local_repo_folder = 'C:/Users/elwin/OneDrive/Documents/ETS/mglDevops/'
git_local_repo_path = git_local_repo_folder + git_repo_name

# Ouvrir le repo git
repo = git.Repo(git_local_repo_path)

# Fonction pour récupérer les informations des commits pour un fichier et sa version spécifique
def get_file_version_commits(file, version):
    file_version_commits = []
    for commit in repo.iter_commits():
        if file in commit.stats.files and version in commit.message:
            commit_info = {
                "CommitId": commit.hexsha,
                "Author": commit.author.name,
                "Message": commit.message,
                "Timestamp": datetime.fromtimestamp(commit.authored_date).strftime('%Y-%m-%d %H:%M:%S')
            }
            file_version_commits.append(commit_info)
    return file_version_commits

# Liste pour stocker les métriques pour chaque fichier et sa version
all_file_metrics = []

# Parcourir chaque ligne du fichier "cleaned_files_vars.csv" pour analyser chaque fichier et sa version
for _, row in base_info_df.iterrows():
    fichier = row['Fichier']
    version = row['Version']
    # Utiliser la fonction pour récupérer les commits spécifiques pour le fichier et la version
    file_version_commits = get_file_version_commits(fichier, version)
    # Calculer les métriques à partir des commits spécifiques
    num_commits = len(file_version_commits)
    num_lignes_ajoutees = sum(commit['LignesAjoutees'] for commit in file_version_commits)
    num_lignes_supprimees = sum(commit['LignesSupprimees'] for commit in file_version_commits)
    # Calculer le nombre de commits de correction de bug
    mots_cles_correction = ["fix", "bug"]
    num_commits_correction_bug = sum(1 for commit in file_version_commits if any(mot_cle in commit['Message'].lower() for mot_cle in mots_cles_correction))
    # Le nombre de développeurs qui ont changé le fichier F dans la version V.
    num_developpeurs_version_v = len(set(commit['Author'] for commit in file_version_commits))
    # Le nombre de développeurs qui ont changé le fichier F dans la version V et toutes les versions avant V.
    all_file_version_commits = get_file_version_commits(fichier, version)
    num_developpeurs_avant_version_v = len(set(commit['Author'] for commit in all_file_version_commits))
    
    # Ajouter les autres métriques ici...

    # Stocker les métriques dans un dictionnaire
    metrics = {
        "Fichier": fichier,
        "Version": version,
        "NombreCommits": num_commits,
        "LignesAjoutees": num_lignes_ajoutees,
        "LignesSupprimees": num_lignes_supprimees,
        "CommitsCorrectionBug": num_commits_correction_bug,
        "DeveloppeursVersionV": num_developpeurs_version_v,
        "DeveloppeursAvantVersionV": num_developpeurs_avant_version_v
        # Ajouter les autres métriques ici...
    }
    all_file_metrics.append(metrics)

# Créer un DataFrame à partir des métriques pour chaque fichier et sa version
final_df = pd.DataFrame(all_file_metrics)

# Sauvegarder les données dans un fichier CSV
final_df.to_csv("finale_Vars.csv", index=False)
