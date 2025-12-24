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

Task: Suggest optimal SVM hyperparameters for this dataset.

Hyperparameters to suggest:
1. C (regularization): Range 0.01 to 100 (log scale)
2. gamma (kernel coefficient): Range 0.001 to 1 (log scale) or 'scale'/'auto'
3. kernel: Choose from 'rbf', 'linear', 'poly', 'sigmoid'
4. degree (for poly kernel): Integer 2-5
5. coef0 (for poly/sigmoid): Range 0.0 to 1.0
6. shrinking: Boolean (true/false)
7. class_weight: 'balanced' or null

"""
        
        if history and len(history) > 0:
            context += "\nPrevious Configurations and Performance:\n"
            # Show last 5 configurations
            for entry in history[-5:]:
                context += f"- Accuracy: {entry['accuracy']:.4f}, Config: {entry['params']}\n"
            
            best = max(history, key=lambda x: x['accuracy'])
            context += f"\nBest so far: Accuracy {best['accuracy']:.4f} with {best['params']}\n"
        
        context += """
Please suggest the next hyperparameter configuration to try. Consider:
- Dataset size (small datasets may need larger C, simpler kernels)
- Feature dimensionality (high-dimensional data works well with linear/rbf)
- Previous performance (exploit successful regions, explore new areas)

Respond with JSON in this exact format:
{
    "C": <float value>,
    "gamma": <float value or "scale" or "auto">,
    "kernel": <"rbf" or "linear" or "poly" or "sigmoid">,
    "degree": <integer 2-5>,
    "coef0": <float 0.0-1.0>,
    "shrinking": <true or false>,
    "class_weight": <"balanced" or null>,
    "reasoning": "<brief explanation of why these parameters>"
}
"""
        return context
    
    def _get_default_suggestions(self):
        """Return default suggestions when AI is not available"""
        import random
        
        kernels = ['rbf', 'linear', 'poly', 'sigmoid']
        selected_kernel = random.choice(kernels)
        
        return {
            'C': 10 ** random.uniform(-2, 2),  # 0.01 to 100
            'gamma': 10 ** random.uniform(-3, 0) if random.random() > 0.3 else 'scale',
            'kernel': selected_kernel,
            'degree': random.randint(2, 5),
            'coef0': random.uniform(0.0, 1.0),
            'shrinking': random.choice([True, False]),
            'class_weight': 'balanced' if random.random() > 0.5 else None,
            'reasoning': 'Random exploration (AI assistant not available)'
        }
    
    def _validate_suggestions(self, suggestions):
        """Validate and normalize AI suggestions"""
        # Ensure all required fields exist
        defaults = self._get_default_suggestions()
        
        validated = {}
        validated['C'] = float(suggestions.get('C', defaults['C']))
        
        # Handle gamma (can be float or string)
        gamma = suggestions.get('gamma', defaults['gamma'])
        if isinstance(gamma, str) and gamma in ['scale', 'auto']:
            validated['gamma'] = gamma
        else:
            validated['gamma'] = float(gamma)
        
        validated['kernel'] = suggestions.get('kernel', defaults['kernel'])
        if validated['kernel'] not in ['rbf', 'linear', 'poly', 'sigmoid']:
            validated['kernel'] = 'rbf'
        
        validated['degree'] = int(suggestions.get('degree', defaults['degree']))
        validated['coef0'] = float(suggestions.get('coef0', defaults['coef0']))
        validated['shrinking'] = bool(suggestions.get('shrinking', defaults['shrinking']))
        validated['class_weight'] = suggestions.get('class_weight', defaults['class_weight'])
        validated['reasoning'] = suggestions.get('reasoning', 'AI-suggested configuration')
        
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
