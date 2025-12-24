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
        current_params = [random.random(), random.random()]
        
        start_time = time.time()
        
        for i in range(self.max_iterations):
            iter_start = time.time()
            
            config_id = oracle.register_config(current_params)
            
            if config_id == -1:
                current_params = oracle.get_next_suggestion(2)
                continue
            
            acc, duration, real_params = self.trainer.evaluate(current_params)
            oracle.update_score(config_id, acc)
            
            iter_time = time.time() - iter_start
            
            results['iterations'].append(i + 1)
            results['accuracies'].append(acc)
            results['times'].append(iter_time)
            
            if acc > results['best_score']:
                results['best_score'] = acc
                results['best_params'] = real_params
            
            current_params = oracle.get_next_suggestion(2)
        
        results['total_time'] = time.time() - start_time
        oracle.close()
        
        return results
    
    def run_random_search(self):
        """Run Random Search"""
        print("[Comparison] Running Random Search...")
        results = {
            'method': 'Random Search',
            'iterations': [],
            'accuracies': [],
            'times': [],
            'best_score': 0.0,
            'best_params': None,
            'total_time': 0.0
        }
        
        start_time = time.time()
        
        for i in range(self.max_iterations):
            iter_start = time.time()
            
            # Random parameters
            params = [random.random(), random.random()]
            acc, duration, real_params = self.trainer.evaluate(params)
            
            iter_time = time.time() - iter_start
            
            results['iterations'].append(i + 1)
            results['accuracies'].append(acc)
            results['times'].append(iter_time)
            
            if acc > results['best_score']:
                results['best_score'] = acc
                results['best_params'] = real_params
        
        results['total_time'] = time.time() - start_time
        
        return results
    
    def run_grid_search(self):
        """Run Grid Search (limited by max_iterations)"""
        print("[Comparison] Running Grid Search...")
        results = {
            'method': 'Grid Search',
            'iterations': [],
            'accuracies': [],
            'times': [],
            'best_score': 0.0,
            'best_params': None,
            'total_time': 0.0
        }
        
        start_time = time.time()
        
        # Create grid based on max_iterations
        grid_size = int(np.sqrt(self.max_iterations))
        c_values = np.logspace(-1, 2, grid_size)
        gamma_values = np.logspace(-3, 0, grid_size)
        
        iteration = 0
        for c in c_values:
            for gamma in gamma_values:
                if iteration >= self.max_iterations:
                    break
                
                iter_start = time.time()
                
                # Normalize to 0-1 range
                c_norm = (np.log10(c) + 1) / 3  # -1 to 2 -> 0 to 1
                gamma_norm = (np.log10(gamma) + 3) / 3  # -3 to 0 -> 0 to 1
                
                params = [c_norm, gamma_norm]
                acc, duration, real_params = self.trainer.evaluate(params)
                
                iter_time = time.time() - iter_start
                
                results['iterations'].append(iteration + 1)
                results['accuracies'].append(acc)
                results['times'].append(iter_time)
                
                if acc > results['best_score']:
                    results['best_score'] = acc
                    results['best_params'] = real_params
                
                iteration += 1
            
            if iteration >= self.max_iterations:
                break
        
        results['total_time'] = time.time() - start_time
        
        return results
    
    def run_bayesian_optimization(self):
        """Run Bayesian Optimization"""
        print("[Comparison] Running Bayesian Optimization...")
        results = {
            'method': 'Bayesian Optimization',
            'iterations': [],
            'accuracies': [],
            'times': [],
            'best_score': 0.0,
            'best_params': None,
            'total_time': 0.0
        }
        
        start_time = time.time()
        
        # Use skopt's BayesSearchCV
        search = BayesSearchCV(
            SVC(),
            {
                'C': Real(0.1, 100, prior='log-uniform'),
                'gamma': Real(0.001, 1, prior='log-uniform')
            },
            n_iter=self.max_iterations,
            cv=3,
            random_state=42
        )
        
        # Fit will internally iterate
        search.fit(self.loader.X_train, self.loader.y_train)
        
        # Extract iteration data from cv_results_
        for i, (mean_score, params, fit_time) in enumerate(zip(
            search.cv_results_['mean_test_score'],
            search.cv_results_['params'],
            search.cv_results_['mean_fit_time']
        )):
            results['iterations'].append(i + 1)
            results['accuracies'].append(mean_score)
            results['times'].append(fit_time)
            
            if mean_score > results['best_score']:
                results['best_score'] = mean_score
                results['best_params'] = params
        
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
