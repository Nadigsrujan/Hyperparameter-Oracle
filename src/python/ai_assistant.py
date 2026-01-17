"""
AI Assistant for Hyperparameter Selection
Uses OpenAI to intelligently suggest hyperparameters based on dataset characteristics
"""

import os
import json
from openai import OpenAI

class AIHyperparameterAssistant:
    def __init__(self, api_key=None):
        """Initialize the AI assistant with OpenAI API key"""
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("[WARNING] No OpenAI API key provided. AI suggestions disabled.")
            self.enabled = False
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
                print("[INFO] AI Assistant enabled with OpenAI")
            except Exception as e:
                print(f"[WARNING] Failed to initialize OpenAI: {e}")
                self.enabled = False
                self.client = None
    
    def get_hyperparameter_suggestions(self, dataset_info, history=None):
        """
        Get AI-powered hyperparameter suggestions
        
        Args:
            dataset_info: Dictionary with dataset characteristics
            history: Optional list of previous configurations and their scores
        
        Returns:
            Dictionary with suggested hyperparameters
        """
        if not self.enabled:
            return self._get_default_suggestions()
        
        try:
            # Prepare context for AI
            context = self._prepare_context(dataset_info, history)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert machine learning engineer specializing in hyperparameter optimization for SVM classifiers. 
                        Your task is to suggest optimal hyperparameters based on dataset characteristics and historical performance.
                        Always respond with valid JSON only, no markdown or extra text."""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse response
            suggestions = json.loads(response.choices[0].message.content)
            return self._validate_suggestions(suggestions)
            
        except Exception as e:
            print(f"[WARNING] AI suggestion failed: {e}")
            return self._get_default_suggestions()
    
    def _prepare_context(self, dataset_info, history):
        """Prepare context string for AI"""
        context = f"""
Dataset Characteristics:
- Samples: {dataset_info.get('samples', 'unknown')}
- Features: {dataset_info.get('features', 'unknown')}
- Classes: {dataset_info.get('classes', 'unknown')}
- Dataset Name: {dataset_info.get('name', 'custom')}

Task: Suggest optimal hyperparameters for this dataset. You can choose between 'mlp' (Neural Network) or 'rf' (Random Forest).

Hyperparameter Search Space (4 Layers):

1. Training / Optimization:
   - model_type: 'mlp' or 'rf'
   - learning_rate_init: 0.0001 to 0.1 (log scale, MLP only)
   - batch_size: 16, 32, 64, 128, 256 (MLP only)
   - optimizer: 'adam', 'sgd', 'lbfgs' (MLP only, mapped to solver)
   - momentum: 0.0 to 0.99 (MLP with sgd only)
   - max_iter: 100 to 1000 (Epochs)

2. Model Architecture:
   - hidden_layer_sizes: List of integers, e.g. [100], [50, 50], [100, 50, 25] (MLP only)
   - activation: 'relu', 'tanh', 'logistic' (MLP only)
   - n_estimators: 50 to 500 (RF only)
   - max_depth: 3 to 30 or null (RF only)
   - min_samples_split: 2 to 20 (RF only)

3. Regularization:
   - alpha: 0.0001 to 0.1 (L2 penalty, MLP only)
   - early_stopping: boolean (MLP only)
   - criterion: 'gini', 'entropy' (RF only)

4. Data & Execution:
   - scaling: 'standard', 'minmax', 'none'
   - class_weight: 'balanced' or null
   
"""
        
        if history and len(history) > 0:
            context += "\nPrevious Configurations and Performance:\n"
            # Show last 5 configurations
            for entry in history[-5:]:
                 # Simplified view for token limit
                context += f"- Acc: {entry['accuracy']:.4f}, Model: {entry['params'].get('model_type', 'unknown')}, Params: {json.dumps(entry['params'])}\n"
            
            best = max(history, key=lambda x: x['accuracy'])
            context += f"\nBest so far: Acc {best['accuracy']:.4f} with {best['params']}\n"
        
        context += """
Please suggest the next configuration. 
Respond with JSON in this exact format:
{
    "model_type": "mlp" or "rf",
    "learning_rate_init": <float>,
    "batch_size": <int>,
    "optimizer": "adam" or "sgd" or "lbfgs",
    "momentum": <float>,
    "max_iter": <int>,
    "hidden_layer_sizes": <list of ints>,
    "activation": "relu" or "tanh" or "logistic",
    "n_estimators": <int>,
    "max_depth": <int or null>,
    "min_samples_split": <int>,
    "alpha": <float>,
    "early_stopping": <bool>,
    "criterion": "gini" or "entropy",
    "scaling": "standard" or "minmax" or "none",
    "class_weight": "balanced" or null,
    "reasoning": "A concise set of 3-4 lines explaining the technical changes. Explicitly describe the logical progression from the first iteration to this one (e.g., 'Since iteration 1, we narrowed down the hidden layers to [100,50]. Now, we are increasing the learning rate slightly to overcome the stall observed in the last 2 rounds')."
}
IMPORTANT: Provide values for ALL keys. Keep reasoning concise, technical, and explain the progression from the start. (max 50 words).
"""
        return context
    
    def _get_default_suggestions(self):
        """Return default suggestions when AI is not available"""
        import random
        
        model_type = random.choice(['mlp', 'rf'])
        
        return {
            'model_type': model_type,
            'learning_rate_init': 0.001,
            'batch_size': random.choice([32, 64, 128]),
            'optimizer': random.choice(['adam', 'sgd']),
            'momentum': 0.9,
            'max_iter': 200,
            'hidden_layer_sizes': random.choice([[100], [50, 50], [100, 50]]),
            'activation': 'relu',
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2,
            'alpha': 0.0001,
            'early_stopping': True,
            'criterion': 'gini',
            'scaling': 'standard',
            'class_weight': None,
            'reasoning': 'Random exploration (AI assistant not available)'
        }
    
    def _validate_suggestions(self, suggestions):
        """Validate and normalize AI suggestions"""
        defaults = self._get_default_suggestions()
        validated = {}
        
        # Copy relevant fields
        keys = ['model_type', 'learning_rate_init', 'batch_size', 'optimizer', 'momentum', 'max_iter', 
                'hidden_layer_sizes', 'activation', 'n_estimators', 'max_depth', 'min_samples_split', 
                'alpha', 'early_stopping', 'criterion', 'scaling', 'class_weight', 'reasoning']
                
        for key in keys:
            validated[key] = suggestions.get(key, defaults.get(key))
            
        return validated
    
    def analyze_results(self, all_configurations):
        """
        Use AI to analyze all configurations and provide insights
        
        Args:
            all_configurations: List of all tried configurations with scores
        
        Returns:
            String with AI-generated insights
        """
        if not self.enabled or not all_configurations:
            return "Insufficient data or AI not available for analysis."
        
        try:
            # Prepare summary
            best = max(all_configurations, key=lambda x: x['score'])
            worst = min(all_configurations, key=lambda x: x['score'])
            avg_score = sum(c['score'] for c in all_configurations) / len(all_configurations)
            
            context = f"""
Analyzed {len(all_configurations)} hyperparameter configurations:

Best Configuration:
- Score: {best['score']:.4f}
- Parameters: {best['params']}

Worst Configuration:
- Score: {worst['score']:.4f}
- Parameters: {worst['params']}

Average Score: {avg_score:.4f}

All Configurations Summary:
"""
            # Add sample of configurations
            for i, config in enumerate(all_configurations[:10], 1):
                context += f"{i}. Score: {config['score']:.4f}, Params: {config['params']}\n"
            
            context += """
Based on these results, provide:
1. Key insights about what hyperparameters work well
2. Patterns you notice in successful configurations
3. Recommendations for future optimization
4. Any warnings about overfitting or convergence

Keep the response concise and actionable.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ML expert analyzing hyperparameter optimization results. Provide clear, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[WARNING] AI analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
