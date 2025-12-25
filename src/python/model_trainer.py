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
        from sklearn.preprocessing import StandardScaler, MinMaxScaler
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'none': None
        }

    def evaluate(self, params):
        """
        Evaluate a hyperparameter configuration
        """
        if not isinstance(params, dict):
             return 0.0, 0.0, {}
        
        full_params = params.copy()
        model_type = params.get('model_type', 'mlp')
        
        try:
            start_time = time.time()
            
            # 1. Data Processing
            X_train = self.dataset.X_train.copy()
            X_test = self.dataset.X_test.copy()
            y_train = self.dataset.y_train
            y_test = self.dataset.y_test
            
            scaling = params.get('scaling', 'none')
            if scaling == 'standard':
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
            elif scaling == 'minmax':
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
                
            # 2. Model Selection
            if model_type == 'mlp':
                from sklearn.neural_network import MLPClassifier
                
                layers = params.get('hidden_layer_sizes', [100])
                if not isinstance(layers, list) or len(layers) == 0:
                    layers = [100]
                layers = [int(x) for x in layers]
                
                optimizer = params.get('optimizer', 'adam')
                if optimizer not in ['adam', 'sgd', 'lbfgs']:
                    optimizer = 'adam'
                
                bs = params.get('batch_size', 'auto')
                if bs != 'auto':
                    try:
                        bs = int(bs)
                    except:
                        bs = 'auto'
                
                model = MLPClassifier(
                    hidden_layer_sizes=tuple(layers),
                    activation=params.get('activation', 'relu'),
                    solver=optimizer,
                    alpha=float(params.get('alpha', 0.0001)),
                    batch_size=bs,
                    learning_rate_init=float(params.get('learning_rate_init', 0.001)),
                    max_iter=int(params.get('max_iter', 200)),
                    momentum=float(params.get('momentum', 0.9)),
                    early_stopping=bool(params.get('early_stopping', False)),
                    random_state=42
                )
                
            elif model_type == 'rf':
                from sklearn.ensemble import RandomForestClassifier
                
                # RF specific params
                n_est = params.get('n_estimators', 100)
                try: n_est = int(n_est)
                except: n_est = 100
                
                depth = params.get('max_depth')
                if depth in [0, 'null', None, 'None', 'null']: depth = None
                else:
                    try: depth = int(depth)
                    except: depth = None
                
                model = RandomForestClassifier(
                    n_estimators=n_est,
                    max_depth=depth,
                    min_samples_split=int(params.get('min_samples_split', 2)),
                    criterion=params.get('criterion', 'gini') if params.get('criterion') in ['gini', 'entropy'] else 'gini',
                    class_weight=params.get('class_weight') if params.get('class_weight') == 'balanced' else None,
                    random_state=42
                )
            else:
                from sklearn.svm import SVC
                model = SVC(probability=True, random_state=42)

            # 3. Training & Evaluation
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            acc = float(accuracy_score(y_test, preds))
            duration = float(time.time() - start_time)
            
            return acc, duration, full_params
            
        except Exception as e:
            print(f"[ERROR] Model evaluation failed for {model_type}: {e}")
            import traceback
            traceback.print_exc()
            return 0.0, 0.0, full_params
    
    def _prepare_svm_params(self, params):
        return {}
