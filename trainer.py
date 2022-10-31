import joblib
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class Trainer:
    train_rf = False # Random forest model must be trained
    train_lr = False # Logistic regression model must be trained
    # Path to CSV file representing the full dataset
    dataset_path = './cleaned_files_vars.csv'
    # Path to CSV file representing the model's validation dataset
    validation_dataset_path = './validation_files_vars.csv'
    # Random forest classifier: parameters must be tuned
    rf_classifier = RandomForestClassifier(max_depth = 2, random_state = 0)
    # Logistic regression classifier: parameters must be tuned
    lr_classifier = LogisticRegression(max_iter = 5000, solver = 'lbfgs', random_state = 16)
    # Random forest model dump file path
    rf_model_path = './rf_model.dump'
    # Logistic regression model dump file path
    lr_model_path = './lr_model.dump'


    def __init__(self, train_rf, train_lr):
        self.train_rf = train_rf
        self.train_lr = train_lr


    def train_model(self):
        if not (self.train_rf or self.train_lr or \
                os.path.exists(self.dataset_path)):
            return

        dataset_file = open(self.dataset_path, 'r')
        dataset_lines = dataset_file.read().splitlines()[1:] # Header is excluded
        # Dataset with dependant variable at index 0 and independent variables at indexes 1,...
        dataset = [l.split(',')[3:] for l in dataset_lines]
        features = [i[1:] for i in dataset] # Features of each item in dataset
        X = np.array([list(map(lambda f: float(f if f else '0'), fs)) for fs in features]) # Features in tensor format
        classes = [i[0] for i in dataset] # Classes of each item in dataset
        y = np.array([float(c == 'True') for c in classes]) # Classes in tensor format
        # Split dataset into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size = 0.3)
        # Save validation set in a file for next step of pipeline
        validation_dataset_file = open(self.validation_dataset_path, 'w')
        for c, fs in zip(y_val, X_val):
            validation_dataset_file.write(str(c) + ',' + ','.join([str(f) for f in fs]) + '\n')
        validation_dataset_file.close()

        if self.train_rf:
            self.train_rf_model(X_train, y_train)
        if self.train_lr:
            self.train_lr_model(X_train, y_train)


    def train_rf_model(self, dataset_features, dataset_classes):
        # Construct model with Random Forest classifier
        rf_model = self.rf_classifier.fit(dataset_features, dataset_classes)
        # Save contructed model into a file for next step of pipeline
        joblib.dump(rf_model, self.rf_model_path)


    def train_lr_model(self, dataset_features, dataset_classes):
        # Scale data features to help convergance
        scaled_dataset_features = StandardScaler().fit_transform(dataset_features)
        # Construct model with Logistic Regression classifier
        lr_model = self.lr_classsifier.fit(scaled_dataset_features, dataset_classes)
        # Save contructed model into a file for next step of pipeline
        joblib.dump(lr_model, self.lr_model_path)