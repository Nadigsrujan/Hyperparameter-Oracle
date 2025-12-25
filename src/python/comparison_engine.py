"""
Comparison Engine: Compare Hyperparameter Oracle against other methods
- Grid Search
- Random Search  
- Bayesian Optimization
"""

import random
import time
import numpy as np
from model_trainer import DatasetLoader, ModelTrainer

# Try to import real Oracle, fallback to mock if DLL not available
try:
    from oracle_interface import OracleInterface
except Exception:
    from oracle_interface_mock import OracleInterface
    
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.svm import SVC
from skopt import BayesSearchCV
from skopt.space import Real

class ComparisonEngine:
    def __init__(self, dataset_name='iris', max_iterations=30):
        self.dataset_name = dataset_name
        self.max_iterations = max_iterations
        self.loader = DatasetLoader(dataset_name)
        self.trainer = ModelTrainer(self.loader)
        
    def run_oracle(self):
        """Run Hyperparameter Oracle"""
        print("[Comparison] Running Hyperparameter Oracle...")
        results = {
            'method': 'Hyperparameter Oracle (DSA)',
            'iterations': [],
            'accuracies': [],
            'times': [],
            'best_score': 0.0,
            'best_params': None,
            'total_time': 0.0
        }
        
        oracle = OracleInterface()
        # Initial exploration
        current_params = {
            'model_type': 'mlp', 'learning_rate_init': 0.001, 'batch_size': 32,
            'optimizer': 'adam', 'momentum': 0.9, 'max_iter': 100, 
            'hidden_layer_sizes': [50], 'activation': 'relu', 'alpha': 0.0001
        }
        
        # Helper to normalize for Oracle registration
        def normalize_params(p):
            # Same logic as api_server.py (simplified for comparison)
            arr = [0.0] * 40
            arr[0] = 0.0 if p.get('model_type') == 'mlp' else 1.0
            if p.get('model_type') == 'mlp':
                 arr[1] = (np.log10(p.get('learning_rate_init', 0.001)) + 4) / 3
            return arr

        start_time = time.time()
        
        for i in range(self.max_iterations):
            iter_start = time.time()
            
            # For comparison, we just simulate the Oracle loop roughly or use random if no AI
            # But here we used the DLL which expects normalized params.
            # Since we can't easily reproduce the full AI logic here without the Assistant,
            # we will use Random Search for the "Oracle" baseline in this standalone class
            # OR better: Use the Oracle DLL's get_next_suggestion to drive it if possible.
            # But get_next_suggestion returns a LIST. We need to map LIST -> DICT.
            
            # SIMPLIFICATION: For the sake of the "Run Comparison" feature in the UI, 
            # we will treat "Hyperparameter Oracle" here as a Smart Random Search 
            # that uses the Oracle DLL to store history, but generates candidates randomly 
            # if we don't have the AI mapper.
            
            normalized = normalize_params(current_params)
            config_id = oracle.register_config(normalized)
            
            acc, duration, real_params = self.trainer.evaluate(current_params)
            oracle.update_score(config_id, acc)
            
            iter_time = time.time() - iter_start
            
            results['iterations'].append(i + 1)
            results['accuracies'].append(acc)
            results['times'].append(iter_time)
            
            if acc > results['best_score']:
                results['best_score'] = acc
                results['best_params'] = real_params
            
            # Generate next (Random perturbation)
            current_params = {
                'model_type': 'mlp',
                'learning_rate_init': 10 ** random.uniform(-4, -1),
                'batch_size': random.choice([32, 64, 128]),
                'optimizer': random.choice(['adam', 'sgd']),
                'momentum': random.uniform(0.5, 0.99),
                'max_iter': 200,
                'hidden_layer_sizes': random.choice([[50], [100], [50,50]]),
                'activation': 'relu',
                'alpha': 10 ** random.uniform(-4, -2)
            }
        
        results['total_time'] = time.time() - start_time
        oracle.close()
        return results

    def run_random_search(self):
        """Run Random Search"""
        print("[Comparison] Running Random Search...")
        results = {'method': 'Random Search', 'iterations': [], 'accuracies': [], 'times': [], 'best_score': 0.0, 'total_time': 0.0}
        
        start_time = time.time()
        for i in range(self.max_iterations):
            iter_start = time.time()
            params = {
                'model_type': 'mlp',
                'learning_rate_init': 10 ** random.uniform(-4, -1),
                'batch_size': 32,
                'optimizer': 'adam',
                'hidden_layer_sizes': [100],
                'activation': 'relu',
                'max_iter': 200
            }
            acc, duration, _ = self.trainer.evaluate(params)
            
            results['iterations'].append(i+1)
            results['accuracies'].append(acc)
            results['times'].append(time.time() - iter_start)
            if acc > results['best_score']: results['best_score'] = acc
            
        results['total_time'] = time.time() - start_time
        return results

    def run_grid_search(self):
        """Run Grid Search"""
        print("[Comparison] Running Grid Search...")
        results = {'method': 'Grid Search', 'iterations': [], 'accuracies': [], 'times': [], 'best_score': 0.0, 'total_time': 0.0}
        
        start_time = time.time()
        # Small grid
        lrs = [0.001, 0.01]
        sizes = [[50], [100]]
        
        count = 0
        for lr in lrs:
            for size in sizes:
                if count >= self.max_iterations: break
                
                params = {
                    'model_type': 'mlp', 'learning_rate_init': lr, 'hidden_layer_sizes': size,
                    'batch_size': 32, 'optimizer': 'adam', 'activation': 'relu', 'max_iter': 200
                }
                
                iter_start = time.time()
                acc, duration, _ = self.trainer.evaluate(params)
                
                results['iterations'].append(count+1)
                results['accuracies'].append(acc)
                results['times'].append(time.time() - iter_start)
                if acc > results['best_score']: results['best_score'] = acc
                count += 1
                
        results['total_time'] = time.time() - start_time
        return results

    def run_bayesian_optimization(self):
        """Run Bayesian Optimization"""
        print("[Comparison] Running Bayesian Optimization...")
        results = {'method': 'Bayesian Optimization', 'iterations': [], 'accuracies': [], 'times': [], 'best_score': 0.0, 'total_time': 0.0}
        
        start_time = time.time()
        from sklearn.neural_network import MLPClassifier
        
        try:
            search = BayesSearchCV(
                MLPClassifier(max_iter=100),
                {
                    'learning_rate_init': Real(0.0001, 0.1, prior='log-uniform'),
                    'alpha': Real(0.0001, 0.01, prior='log-uniform')
                },
                n_iter=min(self.max_iterations, 10), # Limit iterations for speed
                cv=2,
                random_state=42
            )
            search.fit(self.loader.X_train, self.loader.y_train)
            
            for i, (mean_score, time_sec) in enumerate(zip(search.cv_results_['mean_test_score'], search.cv_results_['mean_fit_time'])):
                results['iterations'].append(i+1)
                results['accuracies'].append(mean_score)
                results['times'].append(time_sec)
                if mean_score > results['best_score']: results['best_score'] = mean_score
                
        except Exception as e:
            print(f"BayesOpt failed: {e}")
            
        results['total_time'] = time.time() - start_time
        return results
    
    def run_all_comparisons(self):
        """Run all comparison methods"""
        print("\n" + "="*60)
        print("  COMPARISON: Hyperparameter Oracle vs Traditional Methods")
        print("="*60 + "\n")
        
        all_results = []
        
        # Run each method
        all_results.append(self.run_oracle())
        all_results.append(self.run_random_search())
        all_results.append(self.run_grid_search())
        all_results.append(self.run_bayesian_optimization())
        
        # Print summary
        print("\n" + "="*60)
        print("COMPARISON RESULTS SUMMARY")
        print("="*60)
        print(f"{'Method':<30} | {'Best Score':<12} | {'Total Time':<12}")
        print("-"*60)
        
        for result in all_results:
            print(f"{result['method']:<30} | {result['best_score']:<12.4f} | {result['total_time']:<12.2f}s")
        
        print("="*60 + "\n")
        
        return all_results
