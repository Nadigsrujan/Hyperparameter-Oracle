from model_trainer import DatasetLoader, ModelTrainer
import numpy as np
import traceback

def test_trainer():
    try:
        print("Loading Iris dataset...")
        loader = DatasetLoader('iris')
        trainer = ModelTrainer(loader)
        
        # Test MLP parameters
        mlp_params = {
            'model_type': 'mlp',
            'learning_rate_init': 0.001,
            'batch_size': 32,
            'optimizer': 'adam',
            'momentum': 0.9,
            'max_iter': 200,
            'hidden_layer_sizes': [50, 50],
            'activation': 'relu',
            'alpha': 0.0001,
            'early_stopping': False,
            'scaling': 'standard'
        }
        
        print("\nTesting MLP evaluation...")
        acc, duration, params = trainer.evaluate(mlp_params)
        print(f"MLP Result - Accuracy: {acc}, Duration: {duration}")
        if acc == 0.0:
            print("Warning: MLP accuracy is 0.0")
        
        # Test RF parameters
        rf_params = {
            'model_type': 'rf',
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2,
            'criterion': 'gini',
            'scaling': 'none'
        }
        
        print("\nTesting RF evaluation...")
        acc, duration, params = trainer.evaluate(rf_params)
        print(f"RF Result - Accuracy: {acc}, Duration: {duration}")
        if acc == 0.0:
            print("Warning: RF accuracy is 0.0")

    except Exception as e:
        print(f"FATAL ERROR in test script: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_trainer()
