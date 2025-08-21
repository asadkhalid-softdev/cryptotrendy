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
        self.model = os.getenv('GPT_MODEL', 'gpt-5-nano')
        # Maximum context sizes for different models
        self.model_limits = {
            "gpt-4o-mini": 128000, # Updated limit for gpt-4o-mini
            "gpt-4o": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16384,
            "gpt-5-nano": 400000
        }
        self.enable_kucoin_ta = os.getenv('ENABLE_KUCOIN_TA', 'false').lower() == 'true'
        
    def count_tokens(self, text, model):
        """Count tokens for a given text and model"""
        try:
            enc = encoding_for_model(model)
            return len(enc.encode(text))
        except KeyError:
            # Fallback for newer models not directly supported by tiktoken's model registry
            try:
                enc = encoding_for_model("gpt-4") # Use gpt-4 as a fallback encoder
                return len(enc.encode(text))
            except Exception as e:
                print(f"Error getting encoder: {e}. Falling back to basic split.")
                return len(text.split()) # Basic fallback

    def _build_prompt(self, formatted_data):
        """Build the prompt string for GPT analysis."""

        # System message explaining the task and data interpretation
        system_message = f"""
You are a crypto analyst expert. Your task is to evaluate cryptocurrencies based on the provided data and identify potential breakout candidates.
Assign a 'breakout_score' from 0 to 10 for each coin, where 10 represents the highest breakout potential.
Provide a concise 'reason' for each score, highlighting the key factors.
"""

        system_message += """
Output JSON with:
- coin_symbol: Symbol of the cryptocurrency
- breakout_score: Score from 0-10 based on breakout potential
- reason: Brief explanation for the score
- timestamp: Current analysis timestamp

IMPORTANT: Provide a rating for ALL coins that have ANY Reddit mentions, even if they have low breakout potential.
For coins with low potential, you may assign a low score (0-3), but still include them in the results.

Format the output as a valid JSON array.

{
"analysis": [
    {
        "coin_symbol": "BTC",
        "breakout_score": 7,
        "reason": "Reason for BTC score.",
        "timestamp": "2024-01-01 12:00:00"
    }
]
}
"""

        # Format coin data into a string
        coins_data_str = "\nCoin Data:\n"
        for coin in formatted_data:
            coins_data_str += f"- Symbol: {coin.get('symbol', 'N/A')}\n"
            coins_data_str += f"  Name: {coin.get('name', 'N/A')}\n"
            coins_data_str += f"  Price: ${coin.get('price', 'N/A')}\n"
            coins_data_str += f"  Market Cap: ${coin.get('market_cap', 'N/A')}\n"
            coins_data_str += f"  Market Cap Rank: {coin.get('market_cap_rank', 'N/A')}\n"
            coins_data_str += f"  Volume (24h): ${coin.get('volume_24h', 'N/A')}\n"
            coins_data_str += f"  Price Change (24h): {coin.get('price_change_24h', 'N/A')}%\n"
            coins_data_str += f"  Price Change (7d): {coin.get('price_change_7d', 'N/A')}%\n"
            coins_data_str += f"  Trending: {'Yes' if coin.get('is_trending') else 'No'}\n"
            coins_data_str += f"  Social Mentions: {coin.get('social_mentions', 'N/A')}\n"
            coins_data_str += f"  Social Sentiment: {coin.get('social_sentiment', 'N/A')}\n"
            # Conditionally add RSI data if enabled
            if self.enable_kucoin_ta:
                coins_data_str += f"  RSI (1d): {coin.get('rsi_1d', 'N/A')}\n"
                coins_data_str += f"  RSI (7d): {coin.get('rsi_7d', 'N/A')}\n"
            coins_data_str += "\n"

        # Combine system message and coin data for the user prompt content
        prompt_content = coins_data_str

        # Check token count against model limit
        max_tokens = self.model_limits.get(self.model, 4096) # Default fallback limit
        # Estimate tokens for system message and response buffer
        overhead_tokens = self.count_tokens(system_message, self.model) + 500 # Add buffer for response
        available_tokens = max_tokens - overhead_tokens

        content_tokens = self.count_tokens(prompt_content, self.model)

        # If content exceeds available tokens, we might need to truncate or handle it
        # For now, we'll just print a warning if it's close or over
        if content_tokens >= available_tokens:
            print(f"⚠️ Warning: Prompt content ({content_tokens} tokens) might exceed model's available limit ({available_tokens} tokens). Consider reducing MAX_COINS_TO_ANALYZE.")
            # Simple truncation strategy (if needed, could be more sophisticated)
            # estimated_tokens_per_coin = content_tokens / len(formatted_data)
            # max_coins_for_limit = int(available_tokens / estimated_tokens_per_coin)
            # TODO: Implement truncation if strictly necessary

        return system_message, prompt_content

    def analyze(self, formatted_data):
        """Analyze formatted data using GPT"""
        if not self.client:
            print("GPT analysis skipped: OpenAI client not initialized.")
            return {"error": "OpenAI client not initialized"}
        if not formatted_data:
            print("GPT analysis skipped: No formatted data provided.")
            return {"error": "No formatted data provided"}

        system_message, prompt_content = self._build_prompt(formatted_data)

        try:
            print(f"  - Sending {len(formatted_data)} coins to {self.model} for analysis...")
            start_time = datetime.now()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt_content}
                ],
                response_format={"type": "json_object"}, # Enforce JSON output
                temperature=0.2 # Adjust temperature for desired creativity/consistency
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"  - GPT response received in {duration:.2f} seconds.")

            # Extract JSON content
            analysis_json_str = response.choices[0].message.content
            analysis_result = json.loads(analysis_json_str)

            # print(f"  - GPT response: {analysis_result}")

            # Basic validation of the response structure
            if 'analysis' not in analysis_result or not isinstance(analysis_result['analysis'], list):
                print("  ❌ Error: GPT response did not contain the expected 'analysis' list.")
                return {"error": "Invalid response format from GPT", "raw_response": analysis_json_str}

            # Add metadata
            result_with_metadata = {
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model,
                'analysis_time_seconds': duration,
                'analysis': analysis_result['analysis'], # Extract just the list,
            }

            # Optional: Add token usage if available in response object
            if hasattr(response, 'usage') and response.usage:
                 result_with_metadata['token_usage'] = {
                     'prompt_tokens': response.usage.prompt_tokens,
                     'completion_tokens': response.usage.completion_tokens,
                     'total_tokens': response.usage.total_tokens
                 }
                 print(f"  - Token Usage: Prompt={response.usage.prompt_tokens}, Completion={response.usage.completion_tokens}, Total={response.usage.total_tokens}")


            return result_with_metadata

        except openai.APIError as e:
            print(f"  ❌ OpenAI API Error: {e}")
            return {"error": f"OpenAI API Error: {e}"}
        except json.JSONDecodeError as e:
            print(f"  ❌ Error decoding GPT JSON response: {e}")
            print(f"  Raw response: {analysis_json_str}")
            return {"error": "Failed to decode GPT JSON response", "raw_response": analysis_json_str}
        except Exception as e:
            print(f"  ❌ An unexpected error occurred during GPT analysis: {e}")
            return {"error": f"An unexpected error occurred: {e}"} 