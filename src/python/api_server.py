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
            results = engine.run_all_comparisons()
            oracle_state['comparison_data'] = results
        
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
            # Register config (still needs normalized params for Oracle DSA)
            # Use C and gamma as proxy for duplicate detection
            normalized_params = [
                (current_params['C'] - 0.1) / 99.9,
                (current_params.get('gamma', 0.5) if isinstance(current_params.get('gamma'), (int, float)) else 0.5 - 0.001) / 0.999
            ]
            config_id = oracle.register_config(normalized_params)
        else:
            # Legacy mode
            config_id = oracle.register_config(current_params)
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
        
        # Get next suggestion
        if use_ai:
            # Let AI decide next configuration based on history
            current_params = ai_assistant.get_hyperparameter_suggestions(
                oracle_state['dataset_info'],
                history=oracle_state['history']
            )
            reasoning = current_params.get('reasoning', 'AI suggestion')
        else:
            # Legacy DSA-based suggestion
            current_params = oracle.get_next_suggestion(2)
        
        # Small delay to prevent overwhelming the system
        time.sleep(0.1)
    
    oracle_state['running'] = False
    
    # Finalize experiment (save all data)
    if config_storage:
        config_storage.finalize()

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
