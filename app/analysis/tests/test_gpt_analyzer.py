import unittest
from unittest.mock import patch, MagicMock, call
import os
import logging

# Assuming openai library raises these specific errors.
# You might need to create mock error classes if these are not standard
# or if you want to avoid a direct dependency on openai for tests.
# For this example, we'll assume they are importable or can be mocked.
try:
    from openai import APITimeoutError, APIStatusError
    from openai.types.chat import ChatCompletionMessage
    from openai.types.chat.chat_completion import ChatCompletion, Choice
    # For older openai versions, the structure might be different.
    # This example assumes a newer version of the openai library (e.g., v1.x)
except ImportError:
    # Create mock error classes if openai is not installed or these specific errors don't exist
    class APITimeoutError(IOError): pass # Inherit from a standard error
    class APIStatusError(IOError): # Inherit from a standard error
        def __init__(self, message, response, body):
            super().__init__(message)
            self.response = response # Mock response object
            self.status_code = response.status_code # Store status_code from mock response
            self.body = body


    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    # Mock OpenAI response objects if not available
    class ChatCompletionMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content
    
    class Choice:
        def __init__(self, finish_reason, index, message):
            self.finish_reason = finish_reason
            self.index = index
            self.message = message

    class ChatCompletion:
        def __init__(self, id, choices, created, model, object, system_fingerprint, usage):
            self.id = id
            self.choices = choices
            self.created = created
            self.model = model
            self.object = object
            self.system_fingerprint = system_fingerprint
            self.usage = usage


from tenacity import RetryError

# Add the project root to sys.path or ensure app is discoverable
import sys
# This might need adjustment based on how the tests are run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


from app.analysis.gpt_analyzer import GPTAnalyzer

# Disable logging for tests to keep output clean, unless debugging
logging.disable(logging.CRITICAL)

class TestGPTAnalyzerRetryLogic(unittest.TestCase):

    def setUp(self):
        # Set minimal environment variables for GPTAnalyzer initialization
        os.environ['OPENAI_API_KEY'] = 'test_api_key' # Needs a dummy key
        self.analyzer = GPTAnalyzer()
        # Ensure client is initialized for tests
        if not self.analyzer.client:
             self.analyzer.client = MagicMock() # Mock the client if not already real (e.g. key was missing)
        
        # Create a mock successful response
        self.mock_chat_message = ChatCompletionMessage(role='assistant', content='{"analysis": [{"coin_symbol": "BTC", "breakout_score": 7, "reason": "Test reason"}]}')
        self.mock_choice = Choice(finish_reason='stop', index=0, message=self.mock_chat_message)
        self.mock_successful_response = ChatCompletion(
            id='chatcmpl-test',
            choices=[self.mock_choice],
            created=1677667500,
            model='gpt-4o-mini',
            object='chat.completion',
            system_fingerprint=None,
            usage=MagicMock() # Mock usage object
        )
        self.mock_successful_response.usage.prompt_tokens = 10
        self.mock_successful_response.usage.completion_tokens = 20
        self.mock_successful_response.usage.total_tokens = 30
        
        # Sample formatted data for analyze method
        self.sample_formatted_data = [{'symbol': 'BTC', 'name': 'Bitcoin', 'price': 50000}]


    @patch('app.analysis.gpt_analyzer.openai.OpenAI') # Patch the client initialization if needed
    def test_initialization_without_api_key(self, mock_openai_class):
        # Temporarily unset API key
        original_api_key = os.environ.pop('OPENAI_API_KEY', None)
        
        with patch('app.analysis.gpt_analyzer.logger.warning') as mock_logger_warning:
            analyzer_no_key = GPTAnalyzer()
            self.assertIsNone(analyzer_no_key.client)
            mock_logger_warning.assert_called_with("OpenAI API key not found, GPT analysis will be disabled")

        # Restore API key if it was originally set
        if original_api_key:
            os.environ['OPENAI_API_KEY'] = original_api_key


    @patch.object(GPTAnalyzer, '_call_openai_api') # Patching the method within the already initialized analyzer
    def test_analyze_success_on_first_try(self, mock_call_openai_api):
        mock_call_openai_api.return_value = self.mock_successful_response
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        mock_call_openai_api.assert_called_once()
        self.assertIn('analysis', result)
        self.assertEqual(result['analysis'][0]['coin_symbol'], "BTC")
        self.assertEqual(result['analysis'][0]['breakout_score'], 7)


    @patch('app.analysis.gpt_analyzer.GPTAnalyzer._call_openai_api') # Patching the method to be called by analyze
    @patch('app.analysis.gpt_analyzer.logger') # Patch logger for asserting warnings
    def test_retry_on_apistatuserror_then_success(self, mock_logger, mock_call_openai_api_method):
        # Setup: Raise APIStatusError twice, then succeed
        # Mocking the response object for APIStatusError
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500 # Simulate server error

        mock_call_openai_api_method.side_effect = [
            APIStatusError("Server error", response=mock_error_response, body=None),
            APIStatusError("Server error", response=mock_error_response, body=None),
            self.mock_successful_response
        ]
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        self.assertEqual(mock_call_openai_api_method.call_count, 3)
        self.assertIn('analysis', result)
        self.assertEqual(result['analysis'][0]['coin_symbol'], "BTC")

        # Check logger calls for retries
        # The tenacity decorator logs a warning before sleep
        # We expect 2 retry warnings
        warning_calls = [c for c in mock_logger.warning.call_args_list if "Retrying OpenAI API call" in c.args[0]]
        self.assertEqual(len(warning_calls), 2)


    @patch('app.analysis.gpt_analyzer.GPTAnalyzer._call_openai_api')
    @patch('app.analysis.gpt_analyzer.logger')
    def test_retry_on_apitimeouterror_then_success(self, mock_logger, mock_call_openai_api_method):
        mock_call_openai_api_method.side_effect = [
            APITimeoutError("Request timed out"),
            self.mock_successful_response
        ]
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        self.assertEqual(mock_call_openai_api_method.call_count, 2)
        self.assertIn('analysis', result)
        self.assertEqual(result['analysis'][0]['coin_symbol'], "BTC")
        
        warning_calls = [c for c in mock_logger.warning.call_args_list if "Retrying OpenAI API call" in c.args[0]]
        self.assertEqual(len(warning_calls), 1)


    @patch('app.analysis.gpt_analyzer.GPTAnalyzer._call_openai_api')
    @patch('app.analysis.gpt_analyzer.logger')
    def test_exhausted_retries_for_apistatuserror(self, mock_logger, mock_call_openai_api_method):
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500
        
        mock_call_openai_api_method.side_effect = APIStatusError("Server error consistently", response=mock_error_response, body=None)
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        # The decorator is set to stop_after_attempt(3)
        self.assertEqual(mock_call_openai_api_method.call_count, 3)
        self.assertIn('error', result)
        self.assertTrue("OpenAI API call failed after multiple retries" in result['error'])
        
        # Check for 2 retry warnings (logs before attempt 2 and 3)
        warning_calls = [c for c in mock_logger.warning.call_args_list if "Retrying OpenAI API call" in c.args[0]]
        # There should be logs for retrying before attempt 2 and before attempt 3
        self.assertEqual(len(warning_calls), 2) 
        # The final error is logged as logger.error by the analyze method's try-except RetryError block.
        error_calls = [c for c in mock_logger.error.call_args_list if "OpenAI API call failed after multiple retries" in c.args[0]]
        self.assertEqual(len(error_calls), 1)


    @patch('app.analysis.gpt_analyzer.GPTAnalyzer._call_openai_api')
    @patch('app.analysis.gpt_analyzer.logger')
    def test_retry_on_400_apistatuserror(self, mock_logger, mock_call_openai_api_method):
        # The current decorator retries on any APIStatusError, regardless of code.
        # This test will confirm that behavior.
        mock_error_response = MagicMock()
        mock_error_response.status_code = 400 # Client error
        
        # It should retry 3 times and then fail if the error persists
        mock_call_openai_api_method.side_effect = APIStatusError("Client error", response=mock_error_response, body=None)
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        self.assertEqual(mock_call_openai_api_method.call_count, 3) # Retries occur
        self.assertIn('error', result)
        self.assertTrue("OpenAI API call failed after multiple retries" in result['error'])
        
        warning_calls = [c for c in mock_logger.warning.call_args_list if "Retrying OpenAI API call" in c.args[0]]
        self.assertEqual(len(warning_calls), 2)


    @patch('app.analysis.gpt_analyzer.GPTAnalyzer._call_openai_api')
    def test_no_retry_on_non_retryable_openai_error(self, mock_call_openai_api_method):
        # Example: AuthenticationError which is a subclass of APIError but not APIStatusError or APITimeoutError
        # For this, we need a mock error that is an APIError but not one of the retryable types.
        class MockAuthenticationError(openai.APIError): # Assuming openai.APIError is base for auth errors
             def __init__(self, message):
                super().__init__(message)
                # Mock attributes if needed, e.g. if the main error handler in GPTAnalyzer tries to access them
                self.response = None 
                self.body = None
                self.request = None


        mock_call_openai_api_method.side_effect = MockAuthenticationError("Invalid API key")
        
        result = self.analyzer.analyze(self.sample_formatted_data)
        
        mock_call_openai_api_method.assert_called_once() # Should not retry
        self.assertIn('error', result)
        self.assertTrue("OpenAI API Error" in result['error']) # Caught by the general openai.APIError handler
        self.assertTrue("Invalid API key" in result['error'])


    def test_analyze_no_client(self):
        self.analyzer.client = None # Simulate no client
        with patch('app.analysis.gpt_analyzer.logger.warning') as mock_logger_warning:
            result = self.analyzer.analyze(self.sample_formatted_data)
            self.assertIn('error', result)
            self.assertEqual(result['error'], "OpenAI client not initialized")
            mock_logger_warning.assert_called_with("GPT analysis skipped: OpenAI client not initialized.")

    def test_analyze_no_formatted_data(self):
        with patch('app.analysis.gpt_analyzer.logger.warning') as mock_logger_warning:
            result = self.analyzer.analyze([]) # Empty data
            self.assertIn('error', result)
            self.assertEqual(result['error'], "No formatted data provided")
            mock_logger_warning.assert_called_with("GPT analysis skipped: No formatted data provided.")


if __name__ == '__main__':
    unittest.main()

# Note: Mocking OpenAI's response objects like ChatCompletion, Choice, ChatCompletionMessage
# can be complex due to their nested structure and potential use of Pydantic models in newer versions.
# The mock objects provided here are simplified. For robust tests, consider:
# 1. Using actual (but controlled) instances if the library allows easy construction.
# 2. More detailed MagicMock configurations to mimic behavior.
# 3. Using a dedicated mocking library for OpenAI API calls if available.
# The APIStatusError was also mocked with a status_code attribute for the test.
# Ensure the mock objects are compatible with how they are accessed in gpt_analyzer.py.
# For example, `response.usage.prompt_tokens` requires `response.usage` to be a mock that has these attributes.
# The current mocks `MagicMock()` for usage, which is flexible.
# The `APIStatusError` mock constructor was simplified; real `APIStatusError` requires specific arguments.
# The tests for retry on 400 error confirm the current decorator behavior. If stricter retry (e.g. only 5xx)
# is desired, the decorator in GPTAnalyzer needs to be changed, and this test adjusted.
# The `MockAuthenticationError` is a placeholder; use the actual error type from `openai` if available and distinct.
# `openai.error.AuthenticationError` was used in older versions. Newer versions might use `openai.AuthenticationError`.
# The current `openai.APIError` catch-all in `analyze` might catch it.
# The setUp method creates a default successful response. Individual tests can override side_effect or return_value.
# The `sys.path.insert` is a common way to handle imports in tests when running files directly.
# For a structured test suite, using `python -m unittest discover` with proper `__init__.py` files is better.
# Test for `test_initialization_without_api_key` added to ensure the logger warning is called.
# The mock for `APIStatusError` was enhanced to include a `status_code` via a mock `response` object.
# This allows the retry logic to potentially inspect `e.response.status_code` if it were designed to.
# However, the current `retry_if_exception_type` only checks the type, not attributes.
# The provided test for 400 error reflects this: it will retry because it's an APIStatusError.
# If the requirement was "only retry 5xx", the decorator in gpt_analyzer.py would need:
# `retry=retry_if_exception(lambda e: isinstance(e, APIStatusError) and e.response.status_code >= 500 or isinstance(e, APITimeoutError))`
# or a custom retry condition function.
# The current solution tests the code *as written*.
# Corrected `MockAuthenticationError` to inherit from `openai.APIError` for more accurate type checking.
# The mock OpenAI response objects have been made more realistic for newer openai versions.
# `logging.disable(logging.CRITICAL)` is used to silence logs during tests.Okay, I have created the unit test file `app/analysis/tests/test_gpt_analyzer.py` with the specified test cases.

The file includes:
1.  Imports for `unittest`, `unittest.mock.patch`, `GPTAnalyzer`, OpenAI errors, and `tenacity.RetryError`.
2.  Mock classes for OpenAI objects (`ChatCompletionMessage`, `Choice`, `ChatCompletion`, `APIStatusError`) to ensure tests can run without a live OpenAI dependency or if the exact error/object structures aren't easily importable/usable in a test environment. These mocks are simplified.
3.  A `TestGPTAnalyzerRetryLogic` class.
4.  A `setUp` method to initialize `GPTAnalyzer` and create mock successful responses.
5.  Test cases:
    *   `test_initialization_without_api_key`: Checks behavior when API key is missing.
    *   `test_analyze_success_on_first_try`: Tests successful API call via the `analyze` public method.
    *   `test_retry_on_apistatuserror_then_success`: Tests retry on `APIStatusError` (simulating 500) then success, checking call counts and logger warnings.
    *   `test_retry_on_apitimeouterror_then_success`: Similar, for `APITimeoutError`.
    *   `test_exhausted_retries_for_apistatuserror`: Tests that `RetryError` is handled (returned as an error dict) after all attempts for a persistent `APIStatusError`.
    *   `test_retry_on_400_apistatuserror`: Confirms that the current retry logic *does* retry on a 400 `APIStatusError` as per the implemented decorator.
    *   `test_no_retry_on_non_retryable_openai_error`: Tests that a non-configured error (like a mocked `AuthenticationError`) doesn't trigger retries and is handled by the general `APIError` catch.
    *   `test_analyze_no_client`: Tests behavior when `analyzer.client` is None.
    *   `test_analyze_no_formatted_data`: Tests behavior with empty input data.
6.  Patching is used for `openai.OpenAI` (for initialization test), `GPTAnalyzer._call_openai_api` (to control its behavior during retry tests), and `app.analysis.gpt_analyzer.logger` (to assert log calls).
7.  `sys.path.insert` is used to ensure the `app` module is discoverable; this is a common pattern for standalone test execution but might be handled by test runners in larger setups.
8.  Logging is disabled during tests using `logging.disable(logging.CRITICAL)`.

The tests focus on the retry logic within `GPTAnalyzer` by mocking the direct API call method (`_call_openai_api`) and observing its interaction with the `analyze` method and the tenacity retry mechanism.

Final check of the created file content: The file `app/analysis/tests/test_gpt_analyzer.py` has been created with the detailed unit tests as described above.
