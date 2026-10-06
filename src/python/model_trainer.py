from sklearn.datasets import load_iris, load_wine, load_digits
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import time

class DatasetLoader:
    def __init__(self, name='iris', custom_data=None):
        """
        Initialize dataset loader
        
        Args:
            name: Name of built-in dataset ('iris', 'wine', 'digits') or 'custom'
            custom_data: Dict with 'X' and 'y' arrays for custom datasets
        """
        self.name = name
        
        if name == 'custom' and custom_data is not None:
            # Load custom dataset
            self.X = custom_data['X']
            self.y = custom_data['y']
        elif name == 'iris':
            data = load_iris()
            self.X = data.data
            self.y = data.target
        elif name == 'wine':
            data = load_wine()
            self.X = data.data
            self.y = data.target
        elif name == 'digits':
            data = load_digits()
            self.X = data.data
            self.y = data.target
        else:
            raise ValueError(f"Unknown dataset: {name}")
        
        # Validate data shapes
        if len(self.X) != len(self.y):
            raise ValueError("Features and target must have the same number of samples")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
    
    @staticmethod
    def load_from_csv(csv_path):
        """
        Load dataset from CSV file
        
        Expected format: All columns are features except the last column which is the target
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            dict with 'X' and 'y' arrays
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            if df.empty:
                raise ValueError("CSV file is empty")
            
            if len(df.columns) < 2:
                raise ValueError("CSV must have at least 2 columns (features + target)")
            
            # Last column is target, rest are features
            X = df.iloc[:, :-1].values
            y_raw = df.iloc[:, -1].values
            
            # Encode target labels if they're strings
            if y_raw.dtype == object or isinstance(y_raw[0], str):
                le = LabelEncoder()
                y = le.fit_transform(y_raw)
            else:
                y = y_raw.astype(int)
            
            # Convert features to float
            X = X.astype(float)
            
            # Check for NaN values
            if np.isnan(X).any():
                raise ValueError("CSV contains NaN values in features. Please clean your data.")
            
            if np.isnan(y).any():
                raise ValueError("CSV contains NaN values in target. Please clean your data.")
            
            return {
                'X': X,
                'y': y,
                'n_samples': X.shape[0],
                'n_features': X.shape[1],
                'n_classes': len(np.unique(y))
            }
            
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty or invalid")
        except Exception as e:
            raise ValueError(f"Error loading CSV: {str(e)}")

class ModelTrainer:
    def __init__(self, dataset):
        self.dataset = dataset

    def evaluate(self, params):
        """
        Evaluate a hyperparameter configuration
        
        Args:
            params: Can be either:
                    - List [C, gamma] (legacy, normalized 0-1)
                    - Dictionary with full hyperparameters
        
        Returns:
            accuracy, duration, full_params_dict
        """
        # Handle both legacy and new formats
        if isinstance(params, dict):
            # New format: full hyperparameter dictionary
            svm_params = self._prepare_svm_params(params)
            full_params = params.copy()
        else:
            # Legacy format: normalized [C, gamma] list
            c_val = 0.1 + (params[0] * 99.9)
            gamma_val = 0.001 + (params[1] * 0.999)
            svm_params = {
                'C': c_val, 
                'gamma': gamma_val,
                'kernel': 'rbf',
                'degree': 3,
                'coef0': 0.0,
                'shrinking': True
            }
            full_params = svm_params.copy()
        
        try:
            model = SVC(**svm_params)
            
            start_time = time.time()
            model.fit(self.dataset.X_train, self.dataset.y_train)
            preds = model.predict(self.dataset.X_test)
            acc = accuracy_score(self.dataset.y_test, preds)
            duration = time.time() - start_time
            
            return acc, duration, full_params
            
        except Exception as e:
            print(f"[ERROR] Model evaluation failed: {e}")
            # Return poor score on failure
            return 0.0, 0.0, full_params
    
    def _prepare_svm_params(self, params):
        """Prepare SVM parameters from AI suggestions"""
        svm_params = {}
        
        # C parameter
        svm_params['C'] = params.get('C', 1.0)
        
        # Gamma parameter (can be float or 'scale'/'auto')
        gamma = params.get('gamma', 'scale')
        svm_params['gamma'] = gamma
        
        # Kernel
        svm_params['kernel'] = params.get('kernel', 'rbf')
        
        # Degree (only for poly kernel)
        if svm_params['kernel'] == 'poly':
            svm_params['degree'] = params.get('degree', 3)
        
        # Coef0 (for poly and sigmoid kernels)
        if svm_params['kernel'] in ['poly', 'sigmoid']:
            svm_params['coef0'] = params.get('coef0', 0.0)
        
        # Shrinking
        svm_params['shrinking'] = params.get('shrinking', True)
        
        # Class weight
        class_weight = params.get('class_weight', None)
        if class_weight:
            svm_params['class_weight'] = class_weight
        
        return svm_params
