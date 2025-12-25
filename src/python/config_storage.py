"""
Configuration Storage Manager
Stores and manages hyperparameter configurations and results
"""

import json
import os
from datetime import datetime
import csv

class ConfigurationStorage:
    def __init__(self, storage_dir='./experiment_logs'):
        """Initialize storage manager"""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Current experiment ID (timestamp)
        self.experiment_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.experiment_file = os.path.join(storage_dir, f'experiment_{self.experiment_id}.json')
        self.csv_file = os.path.join(storage_dir, f'experiment_{self.experiment_id}.csv')
        
        # In-memory storage
        self.configurations = []
        self.metadata = {
            'experiment_id': self.experiment_id,
            'start_time': datetime.now().isoformat(),
            'dataset_info': None,
            'best_config': None,
            'best_score': 0.0
        }
        
        print(f"[INFO] Experiment logs will be saved to: {self.experiment_file}")
    
    def set_dataset_info(self, dataset_info):
        """Set dataset information for this experiment"""
        self.metadata['dataset_info'] = dataset_info
        self._save()
    
    def add_configuration(self, iteration, params, score, duration, reasoning=None):
        """
        Add a configuration and its result
        
        Args:
            iteration: Iteration number
            params: Dictionary of hyperparameters
            score: Accuracy score achieved
            duration: Time taken to evaluate
            reasoning: Optional AI reasoning for this configuration
        """
        config_entry = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'score': score,
            'duration': duration,
            'reasoning': reasoning
        }
        
        self.configurations.append(config_entry)
        
        # Update best configuration
        if score > self.metadata['best_score']:
            self.metadata['best_score'] = score
            self.metadata['best_config'] = {
                'iteration': iteration,
                'params': params,
                'score': score
            }
        
        # Auto-save periodically
        if len(self.configurations) % 5 == 0:  # Save every 5 iterations
            self._save()
    
    def _save(self):
        """Save to JSON and CSV files"""
        try:
            # Save JSON (complete data)
            data = {
                'metadata': self.metadata,
                'configurations': self.configurations
            }
            
            with open(self.experiment_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save CSV (for easy import to Excel/other tools)
            if self.configurations:
                self._save_csv()
            
        except Exception as e:
            print(f"[ERROR] Failed to save configurations: {e}")
    
    def _save_csv(self):
        """Save configurations to CSV format"""
        try:
            # Get all unique parameter keys
            all_param_keys = set()
            for config in self.configurations:
                all_param_keys.update(config['params'].keys())
            
            param_keys = sorted(all_param_keys)
            
            # Write CSV
            with open(self.csv_file, 'w', newline='') as f:
                fieldnames = ['iteration', 'timestamp', 'score', 'duration'] + param_keys + ['reasoning']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for config in self.configurations:
                    row = {
                        'iteration': config['iteration'],
                        'timestamp': config['timestamp'],
                        'score': config['score'],
                        'duration': config['duration'],
                        'reasoning': config.get('reasoning', '')
                    }
                    
                    # Add parameters
                    for key in param_keys:
                        row[key] = config['params'].get(key, '')
                    
                    writer.writerow(row)
                    
        except Exception as e:
            print(f"[ERROR] Failed to save CSV: {e}")
    
    def finalize(self):
        """Finalize the experiment and save all data"""
        self.metadata['end_time'] = datetime.now().isoformat()
        self.metadata['total_configurations'] = len(self.configurations)
        self._save()
        
        print(f"\n{'='*60}")
        print(f"EXPERIMENT SAVED")
        print(f"{'='*60}")
        print(f"Experiment ID: {self.experiment_id}")
        print(f"Total Configurations: {len(self.configurations)}")
        print(f"Best Score: {self.metadata['best_score']:.4f}")
        print(f"Best Config: {self.metadata['best_config']['params']}")
        print(f"JSON File: {self.experiment_file}")
        print(f"CSV File: {self.csv_file}")
        print(f"{'='*60}\n")
    
    def get_all_configurations(self):
        """Return all configurations"""
        return self.configurations
    
    def get_best_configurations(self, top_n=5):
        """Get top N best configurations"""
        sorted_configs = sorted(
            self.configurations,
            key=lambda x: x['score'],
            reverse=True
        )
        return sorted_configs[:top_n]
    
    def get_summary(self):
        """Get experiment summary"""
        if not self.configurations:
            return "No configurations recorded yet."
        
        scores = [c['score'] for c in self.configurations]
        
        summary = {
            'experiment_id': self.experiment_id,
            'total_configs': len(self.configurations),
            'best_score': max(scores),
            'worst_score': min(scores),
            'avg_score': sum(scores) / len(scores),
            'best_config': self.metadata['best_config'],
            'dataset_info': self.metadata['dataset_info']
        }
        
        return summary
    
    @staticmethod
    def load_experiment(experiment_file):
        """Load a previous experiment from file"""
        try:
            with open(experiment_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load experiment: {e}")
            return None
