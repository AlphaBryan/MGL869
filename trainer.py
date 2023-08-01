import joblib
import numpy as np
import os
import pandas as pd
from matplotlib import pyplot
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler


class Trainer:
    train_rf = False # Random forest model must be trained
    train_lr = False # Logistic regression model must be trained
    # Path to CSV file representing the full dataset
    dataset_path = './finale_vars_r.d.csv'
    # Path (without extension) to CSV file representing the model's validation dataset
    validation_dataset_path = './validation_files_vars'
    # Random forest classifier: parameters must be tuned
    rf_classifier = RandomForestClassifier(max_depth = 10, random_state = 42, warm_start = True)
    # Logistic regression classifier: parameters must be tuned
    lr_classifier = LogisticRegression(max_iter = 50000, solver = 'lbfgs', random_state = 42, warm_start = True)
    # Random forest model dump file path (without extension)
    rf_model_path = './rf_model'
    # Random forest starting size
    rf_model_start_size = 100
    # Logistic regression model dump file path (without extension)
    lr_model_path = './lr_model'
    # Number of epochs (iterations) for model reinforcement
    epochs = 10

    def __init__(self, train_rf, train_lr):
        self.train_rf = train_rf
        self.train_lr = train_lr

    def custom_version_to_float(self,version_str):
        return float(version_str.replace('.', ''))
    
    def hash_to_int(self, hash_str):
        return hash(hash_str)

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
            
    def train_model(self):
        if not (self.train_rf or self.train_lr or \
                os.path.exists(self.dataset_path)):
            return

        dataset_file = open(self.dataset_path, 'r')
        dataset_lines = dataset_file.read().splitlines()[1:] # Header is excluded
        # Dataset with dependant variable at index 0 and independent variables at indexes 1,...
        dataset = [l.split(',')[3:] for l in dataset_lines]
        for item in dataset:
            item[1] = self.custom_version_to_float(item[1]) # Convert 'Version' to float using the custom function
            item[2] = self.hash_to_int(item[2]) # Convert 'CommitId' to int using the custom function
        features = [i[1:] for i in dataset] # Features of each item in dataset
        X = np.array([list(map(lambda f: float(f) if self.is_number(f) else 0, fs)) for fs in features], dtype = object) # Features in tensor format
        classes = [i[0] for i in dataset] # Classes of each item in dataset
        y = np.array([float(c.lower() == 'true') for c in classes]) # Classes in tensor format

        sss = StratifiedShuffleSplit(n_splits=self.epochs, test_size=0.3, random_state=42)

        for i, (train_index, val_index) in enumerate(sss.split(X, y), start=1):
            X_train, X_val = X[train_index], X[val_index]
            y_train, y_val = y[train_index], y[val_index]
            
            # Save validation set in a file for next step of pipeline
            validation_dataset_file = open(self.validation_dataset_path + '_' + str(i) + '.csv', 'w')
            for c, fs in zip(y_val, X_val):
                validation_dataset_file.write(str(c) + ',' + ','.join([str(f) for f in fs]) + '\n')
            validation_dataset_file.close()
            
            if self.train_rf: # Train Random Forest model
                self.train_rf_model(X_train, y_train, i)
            if self.train_lr: # Train Logistic Regression model
                self.train_lr_model(X_train, y_train, i)

    def train_rf_model(self, dataset_features, dataset_classes, model_idx):
        self.rf_classifier.set_params(n_estimators = self.rf_model_start_size * model_idx) # Increase forest's size
        # Construct model with Random Forest classifier
        rf_model = self.rf_classifier.fit(dataset_features, dataset_classes)
        # Save contructed model into a file for next step of pipeline
        joblib.dump(rf_model, self.rf_model_path + '_' + str(model_idx) + '.dump')

    def train_lr_model(self, dataset_features, dataset_classes, model_idx):
        if len(set(dataset_classes)) < 2:
            print("Not enough classes in the dataset to train logistic regression model. Skipping.")
            return
        # Scale data features to help convergence
        scaled_dataset_features = StandardScaler().fit_transform(dataset_features)
        # Construct model with Logistic Regression classifier
        lr_model = self.lr_classifier.fit(scaled_dataset_features, dataset_classes)
        # Save contructed model into a file for next step of pipeline
        joblib.dump(lr_model, self.lr_model_path + '_' + str(model_idx) + '.dump')


