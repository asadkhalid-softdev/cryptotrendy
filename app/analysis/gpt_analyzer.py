import os
import json
import openai
from datetime import datetime
from tiktoken import encoding_for_model

class GPTAnalyzer:
    def __init__(self):
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.client = None
            print("OpenAI API key not found, GPT analysis will be disabled")
        else:
            self.client = openai.OpenAI(api_key=api_key)
            
        # Default to GPT-4o mini (almost free) model
        self.model = "gpt-4o-mini"
        # Maximum context sizes for different models
        self.model_limits = {
            "gpt-4o-mini": 16384,
            "gpt-4o": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16384
        }
        
    def count_tokens(self, text, model):
        """Count tokens for a given text and model"""
        try:
            enc = encoding_for_model(model)
            return len(enc.encode(text))
        except KeyError:
            # Fallback to cl100k_base for newer models not directly supported
            enc = encoding_for_model("gpt-4")
            return len(enc.encode(text))
        
    def analyze(self, prompt):
        """Send prompt to GPT and get analysis"""
        if not self.client:
            return {
                'error': 'OpenAI API key not configured',
                'timestamp': datetime.now().isoformat()
            }
            
        if not prompt or prompt == "No data available for analysis.":
            return {
                'error': 'No data available for analysis',
                'timestamp': datetime.now().isoformat()
            }
            
        try:
            # Calculate tokens in the input
            system_prompt = "You are a clever and professional crypto analyst that analyzes cryptocurrency data and provides breakout potential scores."
            system_tokens = self.count_tokens(system_prompt, self.model)
            user_tokens = self.count_tokens(prompt, self.model)
            total_input_tokens = system_tokens + user_tokens
            
            # Get the model's token limit
            model_limit = self.model_limits.get(self.model, 8000)
            
            # Calculate available tokens (model limit - input tokens)
            # Reserve some tokens to ensure we stay within limits (1000 tokens buffer)
            available_tokens = model_limit - total_input_tokens - 1000
            max_tokens = max(1, min(available_tokens, 8000))  # Reasonable default max
            
            print(f"System tokens: {system_tokens}")
            print(f"User prompt tokens: {user_tokens}")
            print(f"Total input tokens: {total_input_tokens}")
            print(f"Model token limit: {model_limit}")
            print(f"Available tokens for response: {available_tokens}")
            print(f"Using max_tokens: {max_tokens}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=max_tokens
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                # Look for JSON array in the response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    analysis_data = json.loads(json_str)
                else:
                    # If no JSON array is found, try to parse the entire response
                    analysis_data = json.loads(content)
                    
                return {
                    'analysis': analysis_data,
                    'raw_response': content,
                    'token_info': {
                        'input_tokens': total_input_tokens,
                        'max_output_tokens': max_tokens
                    },
                    'timestamp': datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                return {
                    'error': 'Failed to parse JSON from GPT response',
                    'raw_response': content,
                    'token_info': {
                        'input_tokens': total_input_tokens,
                        'max_output_tokens': max_tokens
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'error': f'OpenAI API error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            } 