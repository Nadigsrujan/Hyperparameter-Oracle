from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import threading
import time
import numpy as np

# Try to import real Oracle, fallback to mock if DLL not available
try:
    from oracle_interface import OracleInterface
    print("[INFO] Using real Oracle interface with C DSA backend")
except Exception as e:
    from oracle_interface_mock import OracleInterface
    print(f"[WARNING] DLL not available ({e}), using mock Oracle interface")
    
from model_trainer import DatasetLoader, ModelTrainer
from comparison_engine import ComparisonEngine
from ai_assistant import AIHyperparameterAssistant
from config_storage import ConfigurationStorage
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Global state
oracle_state = {
    'oracle': None,
    'trainer': None,
    'ai_assistant': None,  # AI-powered hyperparameter assistant
    'config_storage': None,  # Configuration storage manager
    'running': False,
    'current_iteration': 0,
    'max_iterations': 50,
    'history': [],
    'best_config': None,
    'best_score': 0.0,
    'comparison_data': None,
    'custom_dataset': None,  # Store custom dataset info
    'dataset_info': None,  # Current dataset information
    'use_ai': False  # Whether AI suggestions are enabled
}

# Auto-initialize AI assistant from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if api_key and api_key != 'sk-your-api-key-here':
    print("[INFO] OpenAI API key found in environment, initializing AI assistant...")
    oracle_state['ai_assistant'] = AIHyperparameterAssistant(api_key=api_key)
    if oracle_state['ai_assistant'].enabled:
        oracle_state['use_ai'] = True
        print("[INFO] ✓ AI Assistant AUTO-ENABLED from .env file!")
        print("[INFO] AI will intelligently suggest hyperparameters")
    else:
        print("[WARNING] AI Assistant failed to initialize")
else:
    print("[INFO] No API key in .env file. AI mode disabled (using DSA-only mode)")
    print("[INFO] To enable AI: Add your OpenAI API key to .env file")

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload for custom datasets"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': 'Only CSV files are allowed'}), 400
        
        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Try to load and validate the CSV
        try:
            custom_data = DatasetLoader.load_from_csv(filepath)
            
            # Store the custom dataset info
            oracle_state['custom_dataset'] = {
                'filepath': filepath,
                'data': custom_data,
                'filename': filename
            }
            
            return jsonify({
                'status': 'success',
                'message': f'Dataset uploaded successfully: {filename}',
                'dataset_info': {
                    'filename': filename,
                    'samples': custom_data['n_samples'],
                    'features': custom_data['n_features'],
                    'classes': custom_data['n_classes']
                }
            })
            
        except ValueError as e:
            # Clean up the file if validation fails
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'status': 'error', 'message': str(e)}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Upload failed: {str(e)}'}), 500

@app.route('/api/configure-ai', methods=['POST'])
def configure_ai():
    """Configure AI assistant with OpenAI API key"""
    try:
        data = request.json
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'status': 'error', 'message': 'No API key provided'}), 400
        
        # Initialize AI assistant
        oracle_state['ai_assistant'] = AIHyperparameterAssistant(api_key=api_key)
        
        if oracle_state['ai_assistant'].enabled:
            oracle_state['use_ai'] = True
            return jsonify({
                'status': 'success',
                'message': 'AI assistant configured successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to initialize AI assistant'
            }), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize the Oracle with a dataset"""
    try:
        data = request.json
        dataset_name = data.get('dataset', 'iris')
        
        # Initialize Oracle with fallback to mock if DLL fails
        try:
            oracle_state['oracle'] = OracleInterface()
        except (OSError, FileNotFoundError) as dll_error:
            # DLL failed, use mock Oracle
            print(f"[WARNING] DLL loading failed during initialization: {dll_error}")
            print("[INFO] Falling back to mock Oracle interface")
            from oracle_interface_mock import OracleInterface as MockOracle
            oracle_state['oracle'] = MockOracle()
        
        # Load Dataset and Trainer
        if dataset_name == 'custom':
            # Use uploaded custom dataset
            if oracle_state['custom_dataset'] is None:
                return jsonify({
                    'status': 'error', 
                    'message': 'No custom dataset uploaded. Please upload a CSV file first.'
                }), 400
            
            custom_data = oracle_state['custom_dataset']['data']
            loader = DatasetLoader(name='custom', custom_data=custom_data)
            
            oracle_state['trainer'] = ModelTrainer(loader)
            
            # Initialize configuration storage
            oracle_state['config_storage'] = ConfigurationStorage()
            
            # Store dataset info for AI
            oracle_state['dataset_info'] = {
                'name': oracle_state['custom_dataset']['filename'],
                'samples': custom_data['n_samples'],
                'features': custom_data['n_features'],
                'classes': custom_data['n_classes']
            }
            oracle_state['config_storage'].set_dataset_info(oracle_state['dataset_info'])
            
            # Reset state
            oracle_state['history'] = []
            oracle_state['current_iteration'] = 0
            oracle_state['best_score'] = 0.0
            oracle_state['best_config'] = None
            oracle_state['running'] = False
            
            return jsonify({
                'status': 'success',
                'message': f'Oracle initialized with custom dataset: {oracle_state["custom_dataset"]["filename"]}',
                'dataset_info': {
                    'name': oracle_state['custom_dataset']['filename'],
                    'samples': custom_data['n_samples'],
                    'features': custom_data['n_features'],
                    'train_size': loader.X_train.shape[0],
                    'test_size': loader.X_test.shape[0]
                },
                'ai_enabled': oracle_state['use_ai']
            })
        else:
            # Use built-in dataset
            loader = DatasetLoader(dataset_name)
            oracle_state['trainer'] = ModelTrainer(loader)
            
            # Initialize configuration storage
            oracle_state['config_storage'] = ConfigurationStorage()
            
            # Store dataset info for AI
            oracle_state['dataset_info'] = {
                'name': dataset_name,
                'samples': loader.X.shape[0],
                'features': loader.X.shape[1],
                'classes': len(np.unique(loader.y))
            }
            oracle_state['config_storage'].set_dataset_info(oracle_state['dataset_info'])
            
            # Reset state
            oracle_state['history'] = []
            oracle_state['current_iteration'] = 0
            oracle_state['best_score'] = 0.0
            oracle_state['best_config'] = None
            oracle_state['running'] = False
            
            return jsonify({
                'status': 'success',
                'message': f'Oracle initialized with {dataset_name} dataset',
                'dataset_info': {
                    'name': dataset_name,
                    'samples': loader.X.shape[0],
                    'features': loader.X.shape[1],
                    'train_size': loader.X_train.shape[0],
                    'test_size': loader.X_test.shape[0]
                },
                'ai_enabled': oracle_state['use_ai']
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_optimization():
    """Start the optimization loop"""
    try:
        data = request.json
        oracle_state['max_iterations'] = data.get('iterations', 50)
        
        if oracle_state['oracle'] is None:
            return jsonify({'status': 'error', 'message': 'Oracle not initialized'}), 400
        
        if oracle_state['running']:
            return jsonify({'status': 'error', 'message': 'Optimization already running'}), 400
        
        # Start optimization in background thread
        oracle_state['running'] = True
        thread = threading.Thread(target=run_optimization_loop)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success', 'message': 'Optimization started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_optimization():
    """Stop the optimization loop"""
    oracle_state['running'] = False
    return jsonify({'status': 'success', 'message': 'Optimization stopped'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current optimization status"""
    if oracle_state['oracle'] is None:
        return jsonify({'initialized': False})
    
    stats = oracle_state['oracle'].get_stats() if oracle_state['oracle'] else {}
    
    return jsonify({
        'initialized': True,
        'running': oracle_state['running'],
        'current_iteration': oracle_state['current_iteration'],
        'max_iterations': oracle_state['max_iterations'],
        'best_score': oracle_state['best_score'],
        'best_config': oracle_state['best_config'],
        'unique_configs': stats.get('unique_configs', 0),
        'best_recent': stats.get('best_recent', 0.0)
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get optimization history"""
    return jsonify({
        'history': oracle_state['history'][-100:]  # Last 100 entries
    })

@app.route('/api/comparison', methods=['POST'])
def run_comparison():
    """Run comparison with other optimization methods"""
    try:
        data = request.json
        iterations = data.get('iterations', 30)
        dataset_name = data.get('dataset', 'iris')
        
        # Initialize comparison engine
        engine = ComparisonEngine(dataset_name, iterations)
        
        # Run comparison in background
        def run_comparison_async():
            try:
                print("[INFO] Starting background comparison task...")
                results = engine.run_all_comparisons()
                oracle_state['comparison_data'] = results
                print("[INFO] Comparison task completed successfully.")
            except Exception as e:
                print(f"[ERROR] Comparison task failed: {e}")
                oracle_state['comparison_data'] = {'error': str(e)}
        
        thread = threading.Thread(target=run_comparison_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success', 'message': 'Comparison started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/comparison/results', methods=['GET'])
def get_comparison_results():
    """Get comparison results"""
    if oracle_state['comparison_data'] is None:
        return jsonify({'status': 'pending'})
    
    return jsonify({
        'status': 'complete',
        'data': oracle_state['comparison_data']
    })

def run_optimization_loop():
    """Background optimization loop with AI suggestions"""
    oracle = oracle_state['oracle']
    trainer = oracle_state['trainer']
    ai_assistant = oracle_state['ai_assistant']
    config_storage = oracle_state['config_storage']
    use_ai = oracle_state['use_ai'] and ai_assistant is not None
    
    print(f"\n[INFO] Starting optimization with AI {'ENABLED' if use_ai else 'DISABLED'}")
    
    # Initial config
    if use_ai:
        # Get AI suggestion for first iteration
        current_params = ai_assistant.get_hyperparameter_suggestions(
            oracle_state['dataset_info'],
            history=None
        )
        reasoning = current_params.get('reasoning', 'Initial AI suggestion')
    else:
        # Random config (legacy mode)
        current_params = [random.random(), random.random()]
        reasoning = 'Random exploration'
    
    for i in range(oracle_state['max_iterations']):
        if not oracle_state['running']:
            break
        
        # For AI mode, current_params is dict; for legacy, it's list
        if use_ai:
            # Register config (Normalized params for Oracle DSA)
            # Map complex dict parameters to a flat list of 40 doubles
            def normalize_params(p):
                arr = [0.0] * 40
                
                # Index 0: Model Type (0.0=MLP, 1.0=RF)
                arr[0] = 0.0 if p.get('model_type') == 'mlp' else 1.0
                
                if p.get('model_type') == 'mlp':
                    # MLP Hyperparameters (indices 1-19)
                    # 1. Learning Rate (Log scale 0.0001 - 0.1)
                    lr = float(p.get('learning_rate_init', 0.001))
                    arr[1] = (np.log10(lr) + 4) / 3 # -4 to -1 -> 0 to 1
                    
                    # 2. Batch Size (16-256)
                    bs = int(p.get('batch_size', 32)) if str(p.get('batch_size')) != 'auto' else 32
                    arr[2] = (bs - 16) / (256 - 16)
                    
                    # 3. Optimizer (Adam=0, SGD=0.5, LBFGS=1)
                    opt = p.get('optimizer', 'adam')
                    arr[3] = 0.0 if opt == 'adam' else (0.5 if opt == 'sgd' else 1.0)
                    
                    # 4. Momentum (0-1)
                    arr[4] = float(p.get('momentum', 0.9))
                    
                    # 5. Layers (approximate complexity 0-1)
                    layers = p.get('hidden_layer_sizes', [100])
                    total_neurons = sum(layers) if isinstance(layers, list) else 100
                    arr[5] = min(total_neurons / 500, 1.0)
                    
                    # 6. Activation (Relu=0, Tanh=0.5, Logistic=1)
                    act = p.get('activation', 'relu')
                    arr[6] = 0.0 if act == 'relu' else (0.5 if act == 'tanh' else 1.0)
                    
                    # 7. Alpha (Log scale 0.0001 - 0.1)
                    alpha = float(p.get('alpha', 0.0001))
                    arr[7] = (np.log10(alpha) + 4) / 3
                    
                    # 8. Early Stopping
                    arr[8] = 1.0 if p.get('early_stopping') else 0.0
                    
                else: # RF
                    # RF Hyperparameters (indices 20-29)
                    # 20. N Estimators (50-500)
                    n = int(p.get('n_estimators', 100))
                    arr[20] = (n - 50) / 450
                    
                    # 21. Max Depth (3-30)
                    d = p.get('max_depth')
                    d = 30 if d is None else int(d)
                    arr[21] = (d - 3) / 27
                    
                    # 22. Min Samples Split (2-20)
                    s = int(p.get('min_samples_split', 2))
                    arr[22] = (s - 2) / 18
                    
                    # 23. Criterion (Gini=0, Entropy=1)
                    arr[23] = 0.0 if p.get('criterion') == 'gini' else 1.0
                
                # Shared / Data Params (indices 30-39)
                # 30. Scaling (None=0, Standard=0.5, MinMax=1)
                sc = p.get('scaling', 'standard')
                arr[30] = 0.0 if sc == 'none' else (0.5 if sc == 'standard' else 1.0)
                
                # 31. Class Weight (None=0, Balanced=1)
                arr[31] = 1.0 if p.get('class_weight') == 'balanced' else 0.0
                
                return arr

            normalized_params = normalize_params(current_params)
            config_id = oracle.register_config(normalized_params)
        else:
            # Legacy mode
            legacy_params = [0.0] * 40
            legacy_params[0] = current_params[0] # Just map 0-1 to something
            config_id = oracle.register_config(legacy_params)
            reasoning = 'Random exploration'
        
        if config_id == -1:
            # Duplicate found
            print(f"[INFO] Duplicate configuration detected, getting new suggestion")
            if use_ai:
                # Get new AI suggestion
                current_params = ai_assistant.get_hyperparameter_suggestions(
                    oracle_state['dataset_info'],
                    history=oracle_state['history']
                )
                reasoning = current_params.get('reasoning', 'AI suggestion after duplicate')
            else:
                current_params = oracle.get_next_suggestion(2)
            continue
        
        # Train and evaluate
        acc, duration, real_params = trainer.evaluate(current_params)
        
        # Update Oracle
        oracle.update_score(config_id, acc)
        
        # Save to configuration storage
        if config_storage:
            config_storage.add_configuration(
                iteration=i + 1,
                params=real_params,
                score=acc,
                duration=duration,
                reasoning=reasoning if use_ai else None
            )
        
        # Update state
        oracle_state['current_iteration'] = i + 1
        
        stats = oracle.get_stats()
        
        history_entry = {
            'iteration': i + 1,
            'accuracy': acc,
            'duration': duration,
            'params': real_params,
            'unique_configs': stats['unique_configs'],
            'timestamp': time.time(),
            'reasoning': reasoning if use_ai else None
        }
        
        oracle_state['history'].append(history_entry)
        
        if acc > oracle_state['best_score']:
            oracle_state['best_score'] = acc
            oracle_state['best_config'] = real_params
        
        if use_ai:
            # Let AI decide next configuration based on history
            current_params = ai_assistant.get_hyperparameter_suggestions(
                oracle_state['dataset_info'],
                history=oracle_state['history']
            )
            reasoning = current_params.get('reasoning', 'AI suggestion')
        else:
            # Legacy DSA-based suggestion
            # 1. Get raw float parameters from C Oracle
            raw_params = oracle.get_next_suggestion(40)
            
            # 2. Denormalize validation to dictionary
            def denormalize_params(arr):
                p = {}
                
                # Model Type
                if arr[0] < 0.5:
                    p['model_type'] = 'mlp'
                    
                    # MLP Params
                    # Learning Rate: 0-1 -> 1e-4 to 1e-1
                    p['learning_rate_init'] = float(10 ** (3 * arr[1] - 4))
                    
                    # Batch Size: 0-1 -> 16 to 256
                    p['batch_size'] = int(arr[2] * 240 + 16)
                    
                    # Optimizer
                    if arr[3] < 0.33: p['optimizer'] = 'adam'
                    elif arr[3] < 0.66: p['optimizer'] = 'sgd'
                    else: p['optimizer'] = 'lbfgs'
                    
                    # Momentum
                    p['momentum'] = float(arr[4])
                    
                    # Layers
                    n_neurons = int(arr[5] * 500) + 10
                    p['hidden_layer_sizes'] = [n_neurons]
                    
                    # Activation
                    if arr[6] < 0.33: p['activation'] = 'relu'
                    elif arr[6] < 0.66: p['activation'] = 'tanh'
                    else: p['activation'] = 'logistic'
                    
                    # Alpha
                    p['alpha'] = float(10 ** (3 * arr[7] - 4))
                    
                    # Early Stopping
                    p['early_stopping'] = bool(arr[8] > 0.5)
                    
                else:
                    p['model_type'] = 'rf'
                    
                    # RF Params
                    p['n_estimators'] = int(arr[20] * 450 + 50)
                    p['max_depth'] = int(arr[21] * 27 + 3)
                    p['min_samples_split'] = int(arr[22] * 18 + 2)
                    p['criterion'] = 'entropy' if arr[23] > 0.5 else 'gini'
                
                # Shared Params
                if arr[30] < 0.33: p['scaling'] = 'none'
                elif arr[30] < 0.66: p['scaling'] = 'standard'
                else: p['scaling'] = 'minmax'
                
                p['class_weight'] = 'balanced' if arr[31] > 0.5 else None
                
                return p

            current_params = denormalize_params(raw_params)
            reasoning = 'DSA Probabilistic Suggestion'
        
        # Small delay to prevent overwhelming the system
        time.sleep(0.1)
    
    oracle_state['running'] = False
    
    # Finalize experiment (save all data)
    if config_storage:
        config_storage.finalize()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
