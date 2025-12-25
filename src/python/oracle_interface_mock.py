import random
import numpy as np

# Mock Oracle Interface (fallback when DLL is not available)
class OracleInterface:
    """
    Mock implementation of Oracle interface for testing without compiled DLL.
    Uses simple random-based suggestions.
    """
    def __init__(self):
        self.configs = {}
        self.next_id = 0
        self.best_params = None
        self.best_score = 0.0
        self.unique_count = 0
        
    def close(self):
        pass
    
    def register_config(self, params):
        """Register a configuration and return its ID"""
        # Convert to tuple for hashability
        param_tuple = tuple(params)
        
        # Check if already registered
        if param_tuple in self.configs:
            return -1  # Duplicate
        
        # Register new config
        config_id = self.next_id
        self.configs[param_tuple] = {
            'id': config_id,
            'params': params,
            'score': 0.0
        }
        self.next_id += 1
        self.unique_count += 1
        
        return config_id
    
    def update_score(self, config_id, score):
        """Update score for a configuration"""
        for config in self.configs.values():
            if config['id'] == config_id:
                config['score'] = score
                
                # Track best
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = config['params']
                break
    
    def get_next_suggestion(self, param_count):
        """Get next hyperparameter suggestion"""
        if self.best_params is not None and random.random() < 0.7:
            # 70% of the time, explore near best params
            suggestion = []
            for param in self.best_params:
                # Add small random noise
                noise = random.gauss(0, 0.1)
                new_val = param + noise
                # Clip to [0, 1]
                new_val = max(0.0, min(1.0, new_val))
                suggestion.append(new_val)
            return suggestion[:param_count]
        else:
            # 30% of the time, random exploration
            return [random.random() for _ in range(param_count)]
    
    def get_stats(self):
        """Get Oracle statistics"""
        return {
            "unique_configs": self.unique_count,
            "best_recent": self.best_score
        }
