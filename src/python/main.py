import time
import random

# Try to import real Oracle, fallback to mock if DLL not available
try:
    from oracle_interface import OracleInterface
except Exception:
    from oracle_interface_mock import OracleInterface
    print("[WARNING] Using mock Oracle interface (DLL not available)")
    
from model_trainer import DatasetLoader, ModelTrainer

def main():
    print("==============================================")
    print("   Hyperparameter Oracle (DSA-Driven AutoML)  ")
    print("==============================================")
    
    # 1. Initialize Oracle (C Backend)
    oracle = OracleInterface()
    
    # 2. Load Data
    print("[Python] Loading Dataset (Iris)...")
    loader = DatasetLoader('iris')
    trainer = ModelTrainer(loader)
    
    # 3. Optimization Loop
    iterations = 50
    best_acc = 0.0
    best_config = None
    
    print(f"[Python] Starting Optimization Loop ({iterations} iterations)...")
    print("-" * 60)
    print(f"{'Iter':<5} | {'Acc':<8} | {'C':<8} | {'Gamma':<8} | {'DSA Stats'}")
    print("-" * 60)
    
    # Initial random config
    current_params = [random.random(), random.random()]
    
    for i in range(iterations):
        # A. Register Config in Oracle
        config_id = oracle.register_config(current_params)
        
        if config_id == -1:
            # Duplicate or full, get new suggestion immediately
            current_params = oracle.get_next_suggestion(2)
            continue
            
        # B. Train & Evaluate
        acc, duration, real_params = trainer.evaluate(current_params)
        
        # C. Feedback to Oracle
        oracle.update_score(config_id, acc)
        
        # D. Logging
        stats = oracle.get_stats()
        print(f"{i+1:<5} | {acc:.4f}   | {real_params['C']:.4f}   | {real_params['gamma']:.4f}   | Unique: {stats['unique_configs']}")
        
        if acc > best_acc:
            best_acc = acc
            best_config = real_params
            
        # E. Get Next Suggestion from Oracle (DSA Magic)
        current_params = oracle.get_next_suggestion(2)
        
    print("-" * 60)
    print("Optimization Complete.")
    print(f"Best Accuracy: {best_acc:.4f}")
    print(f"Best Config: {best_config}")
    
    oracle.close()

if __name__ == "__main__":
    main()
