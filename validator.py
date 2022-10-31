import joblib
import numpy as np
import os
from sklearn.metrics import auc, roc_curve, precision_score, recall_score


class Validator:
    validate_rf = False # Random forest model must be validated
    validate_lr = False # Logistic regression model must be validated
    # Path to CSV file representing the model's validation dataset
    validation_dataset_path = './validation_files_vars.csv'
    # Random forest model dump file path
    rf_model_path = './rf_model.dump'
    # Logistic regression model dump file path
    lr_model_path = './lr_model.dump'


    def __init__(self, validate_rf, validate_lr):
        self.validate_rf = validate_rf
        self.validate_lr = validate_lr


    def validate_model(self):
        if not (self.validate_rf or self.validate_lr or \
                os.path.exists(self.validation_dataset_path)):
            return

        validation_dataset_file = open(self.validation_dataset_path, 'r')
        validation_dataset_line = validation_dataset_file.read().splitlines()
        validation_dataset = [l.split(',') for l in validation_dataset_line]
        features = [i[1:] for i in validation_dataset] # Features of each item in dataset
        X_val = np.array([list(map(lambda f: float(f), fs)) for fs in features]) # Features in tensor format
        classes = [i[0] for i in validation_dataset] # Classes of each item in dataset
        y_val = np.array([float(c) for c in classes]) # Classes in tensor format

        if self.validate_rf:
            self.validate_rf_model(X_val, y_val)
        if self.validate_lr:
            self.validate_lr_model(X_val, y_val)


    def print_scores(self, truths, predictions):
        # Print AUC
        fpr, tpr, thresholds = roc_curve(truths, predictions)
        print('AUC: ' + str(auc(fpr, tpr)))
        # Print Precision
        print('Precision: ' + str(precision_score(truths, predictions, zero_division = 0)))
        # Print Recall
        print('Recall: ' + str(recall_score(truths, predictions, zero_division = 0)))


    def validate_rf_model(self, dataset_features, dataset_classes):
        if not os.path.exists(self.rf_model_path):
            return

        # Load model previously constructed with Random Forest classifier
        rf_model = joblib.load(self.rf_model_path)
        # Predict validation set
        predictions = rf_model.predict(dataset_features)
        # Print performance scores
        self.print_scores(dataset_classes, predictions)


    def validate_lr_model(self, dataset_features, dataset_classes):
        if not os.path.exists(self.lr_model_path):
            return

        # Load model previously constructed with Logistic Regression classifier
        lr_model = joblib.load(self.lr_model_path)
        # Predict validation set
        predictions = lr_model.predict(dataset_features)
        # Print performance scores
        self.print_scores(dataset_classes, predictions)