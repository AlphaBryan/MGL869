import math
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

        # Remove duplicated rows
        files_vars = pd.read_csv(file_to_clean)
        removed_duplicates = files_vars.drop_duplicates()
        removed_duplicates.to_csv(self.files_vars_no_dupes_path, index = False)

        # Merge File, Class and Method rows of same File into one row
        cleaned_data = removed_duplicates.groupby(["Version", "CommitId", "Fichier", "ContientBogue"], as_index = False).first()

        # Remove columns not needed in our analysis
        columns_to_remove = ["AltAvgLineBlank", "AltAvgLineCode", "AltAvgLineComment", "AltCountLineBlank", "AltCountLineCode", "AltCountLineComment", "CountClassCoupledModified",
                            "CountDeclExecutableUnit", "CountDeclFile", "CountDeclFileCode", "CountDeclFileHeader", "CountDeclInstanceVariablePrivate", "CountDeclInstanceVariableProtected" ,
                            "CountDeclInstanceVariablePublic", "CountDeclMethodAll", "CountDeclMethodConst", "CountDeclMethodFriend", "CountLineInactive",	"CountLinePreprocessor",
                            "CountPathLog", "CountStmtEmpty", "Cyclomatic",	"CyclomaticModified", "CyclomaticStrict", "Essential", "Knots", "MaxEssential",	"MaxEssentialKnots",
                            "MinEssentialKnots", "PercentLackOfCohesionModified"]

        cleaned_data = cleaned_data.drop(columns_to_remove, axis=1)
        cleaned_data.to_csv(self.cleaned_files_vars_path, index=False)
        cleaned_data = pd.read_csv(self.cleaned_files_vars_path)

        # Remove correlated metrics
        data_columns = cleaned_data.keys()
        data_metrics = list(data_columns[5:])

        uncorrelated_metrics = []
        for i in range(len(data_metrics)):
            is_correlated = False
            for j in range(i + 1, len(data_metrics)):
                m_i = cleaned_data[data_metrics[i]].tolist()
                m_j = cleaned_data[data_metrics[j]].tolist()

                correlation_score = spearmanr(m_i, m_j).correlation
                # Correlation is detected if score is above this threshold
                if not math.isnan(correlation_score) and correlation_score > 0.9:
                    is_correlated = True
                    break

            if not is_correlated:
                uncorrelated_metrics += [data_metrics[i]]

        # Save CSV data file without correlated metrics
        cleaned_data.to_csv(self.files_vars_no_correlation_path, 
                            columns = list(data_columns[0:5]) + uncorrelated_metrics, index = False)

