from re import X
import joblib
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
from sklearn.metrics import auc, roc_curve, precision_score, recall_score


class Validator:
    validate_rf = False # Random forest model must be validated
    validate_lr = False # Logistic regression model must be validated
    # Path (without extension) to CSV file representing the model's validation dataset
    validation_dataset_path = './validation_files_vars'
    cleaned_dataset_path = './cleaned_files_vars.csv'
    # Random forest model dump file path (without extension)
    rf_model_path = './rf_model'
    # Logistic regression model dump file path (without extension)
    lr_model_path = './lr_model'
    # Count of models to validate
    models_count = 10


    def __init__(self, validate_rf, validate_lr):
        self.validate_rf = validate_rf
        self.validate_lr = validate_lr


    def validate_model(self):
        if not (self.validate_rf or self.validate_lr):
            return

        # Axis for line plots
        x = np.array([i for i in range(1, self.models_count + 1)]) # One tick per model on X axis
        auc = np.zeros((2, self.models_count)) # AUC per model per algorithm
        precision = np.zeros((2, self.models_count)) # Precision per model per algorithm
        recall = np.zeros((2, self.models_count)) # Recall per model per algorithm

        # Validate X (X = models_count) previously constructed models
        for i in range(1, self.models_count + 1):
            dataset_path = self.validation_dataset_path + '_' + str(i) + '.csv'
            if not os.path.exists(dataset_path):
                break

            dataset_file = open(dataset_path, 'r')
            dataset = [l.split(',') for l in dataset_file.read().splitlines()]
            features = [i[1:] for i in dataset] # Features of each item in dataset
            X_val = np.array([list(map(lambda f: float(f), fs)) for fs in features]) # Features in tensor format
            classes = [i[0] for i in dataset] # Classes of each item in dataset
            y_val = np.array([float(c) for c in classes]) # Classes in tensor format

            # Get AUC, precision and recall of each model of each algorithm
            if self.validate_rf:
                auc[0][i - 1], precision[0][i - 1], recall[0][i - 1] = self.validate_rf_model(X_val, y_val, i)
            if self.validate_lr:
                auc[1][i - 1], precision[1][i - 1], recall[1][i - 1] = self.validate_lr_model(X_val, y_val, i)

        self.display_plot(x, 'AUC', auc) # Display line plot for AUC of each model
        self.display_plot(x, 'Precision', precision) # Display line plot for precision of each model
        self.display_plot(x, 'Recall', recall) # Display line plot for recall of each model
        self.display_nomogram() # Display nomogram for visualizing importance of each metric
        self.get_feature_importances()

    def display_plot(self, x, y_label, Y):
        plt.figure() # Initialize plot
        plt.plot(x, Y[0], label = 'Random Forest') # Display line 1
        plt.plot(x, Y[1], label = 'Logistic Regression') # Display line 2
        plt.legend() # Display legend
        plt.xlabel('Model') # Display label of X axis
        plt.ylabel(y_label) # Display label of Y axis
        plt.savefig(y_label + '_plot.png') # Save plot into a .png file


    def display_nomogram(self):
        print('TODO: (average importance of metrics for all models of same algorithm ?)')

    def get_feature_importances(self):
        lr_feature_data = []
        rf_feature_data = []

        for i in range(1, self.models_count + 1):
            if self.validate_rf:
                model_path = self.rf_model_path + '_' + str(i) + '.dump'
                if not os.path.exists(model_path):
                    return

                # Load model previously constructed with Random Forest classifier
                rf_model = joblib.load(model_path)
                rf_feature_data.append(rf_model.feature_importances_)

            if self.validate_lr:
                model_path = self.lr_model_path + '_' + str(self.models_count) + '.dump'
                if not os.path.exists(model_path):
                    return

                # Load model previously constructed with Random Forest classifier
                lr_model = joblib.load(model_path)
                lr_feature_data.append(lr_model.coef_[0])

        lr_feature_importances = np.array(lr_feature_data)
        rf_feature_importances = np.array(rf_feature_data)
        self.print_feature_importances(np.average(rf_feature_importances, axis=0), 'rf')
        self.print_feature_importances(np.average(lr_feature_importances, axis=0), 'lr')

    def print_feature_importances(self, feature_importances, model):
        file_header = open(self.cleaned_dataset_path, 'r').readlines()[0]
        importance_header = file_header.split(',')[4:]
        # Create data object to plot
        importances = pd.DataFrame(data={
            'Attributes': importance_header,
            'Importance': feature_importances})
        # Plot the importances
        plt.figure()
        plt.bar(x=importances['Attributes'], height=importances['Importance'])
        plt.title('Feature importances')
        plt.xticks(rotation='vertical', size=3)
        plt.tight_layout()
        plt.savefig(model + '_feature_importances.png')  # Save plot into a .png file

    def calculate_scores(self, truths, predictions):
        # Calculate ROC curve for AUC
        fpr, tpr, thresholds = roc_curve(truths, predictions)
        # Calculate Precision
        precision = precision_score(truths, predictions, zero_division = 0)
        # Calculate Recall
        recall = recall_score(truths, predictions, zero_division = 0)

        return auc(fpr, tpr), precision, recall


    def validate_rf_model(self, dataset_features, dataset_classes, model_idx):
        model_path = self.rf_model_path + '_' + str(model_idx) + '.dump'
        if not os.path.exists(model_path):
            return

        # Load model previously constructed with Random Forest classifier
        rf_model = joblib.load(model_path)
        # Predict validation set
        predictions = rf_model.predict(dataset_features)
        # Print performance scores
        return self.calculate_scores(dataset_classes, predictions)


    def validate_lr_model(self, dataset_features, dataset_classes, model_idx):
        model_path = self.lr_model_path + '_' + str(model_idx) + '.dump'
        if not os.path.exists(model_path):
            return

        # Load model previously constructed with Logistic Regression classifier
        lr_model = joblib.load(model_path)
        # Predict validation set
        predictions = lr_model.predict(dataset_features)
        # Print performance scores
        return self.calculate_scores(dataset_classes, predictions)