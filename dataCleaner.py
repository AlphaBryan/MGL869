import pandas as pd
from scipy.stats import spearmanr 


class DataCleaner:
    clean_file = False
    # Path to CSV data file without duplicates
    files_vars_no_dupes_path = 'files_vars_no_dupes.csv'
    # Path to CSV data file with Class/Method metrics merged with File metrics
    cleaned_files_vars_path = 'cleaned_files_vars.csv'
    # Path to CSV data file without correlated metrics
    files_vars_no_correlation_path = 'files_vars_no_correlation.csv'

    def __init__(self, clean_file):
        self.clean_file = clean_file

    def clean_data(self, file_to_clean):
        if not self.clean_file:
            return

        files_vars = pd.read_csv(file_to_clean)
        removed_duplicates = files_vars.drop_duplicates()
        removed_duplicates.to_csv(self.files_vars_no_dupes_path, index=False)

        cleaned_data = removed_duplicates.groupby(["Version", "CommitId", "Fichier", "ContientBogue"], as_index=False).first()
        cleaned_data.to_csv(self.cleaned_files_vars_path, index=False)

