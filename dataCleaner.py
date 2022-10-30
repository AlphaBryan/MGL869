import pandas as pd


class DataCleaner:
    clean_file = False

    def __init__(self, clean_file):
        self.clean_file = clean_file

    def clean_data(self, file_to_clean):
        if not self.clean_file:
            return

        files_vars = pd.read_csv(file_to_clean)
        removed_duplicates = files_vars.drop_duplicates()
        removed_duplicates.to_csv('files_vars_no_dupes.csv', index=False)

        cleaned_data = removed_duplicates.groupby(["Version", "CommitId", "Fichier", "ContientBogue"], as_index=False).first()
        cleaned_data.to_csv('cleaned_files_vars.csv', index=False)
