import os
import logging
import json
from typing import Dict, Any

try:
    from google.adk.agents.llm_agent import LlmAgent
    from google.adk.tools import Tool
except ImportError:
    LlmAgent = None
    Tool = None

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Gemini-powered summarization for schema-specific content using Google ADK"""

    def __init__(self, api_key: str = None, project_id: str = None):
        """
        Initialize Gemini agent using Google ADK

        Args:
            api_key: Google AI API key (defaults to GEMINI_API_KEY env var)
            project_id: Google Cloud project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
        """
        if LlmAgent is None:
            raise ImportError(
                "google-adk package not installed. Install with: pip install google-adk"
            )

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Initialize the ADK agent with Gemini model
        self.agent = LlmAgent(
            model="gemini-2.0-flash-exp",
            name="video_content_analyzer",
            instruction="""You are a video content analyzer. Your task is to:
1. Analyze video transcription and OCR text
2. Extract relevant information based on the provided schema
3. Generate a JSON object that matches the Notion database schema exactly
4. Return ONLY valid JSON without any markdown formatting or code blocks""",
            tools=[],  # Add custom tools here if needed
        )

        logger.info("Gemini summarizer initialized with Google ADK agent")

    def summarize(
        self, transcription: str, ocr_text: str, schema: Dict, user_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Generate schema-specific summary from video content using ADK agent

        Args:
            transcription: Audio transcription from Whisper
            ocr_text: Text extracted from video frames via OCR
            schema: Notion database schema defining output structure
            user_prompt: Optional user-provided context or instructions

        Returns:
            Structured data matching the Notion schema
        """
        logger.info("Building prompt for Gemini agent")
        prompt = self._build_prompt(transcription, ocr_text, schema, user_prompt)

        logger.info("Sending request to ADK agent for summarization")
        response_text = self._call_agent(prompt)

        logger.info("Parsing agent response")
        structured_data = self._parse_response(response_text, schema)

        return structured_data

    def _build_prompt(
        self, transcription: str, ocr_text: str, schema: Dict, user_prompt: str
    ) -> str:
        """
        Construct prompt with schema, transcription, OCR text, and user prompt

        Args:
            transcription: Audio transcription
            ocr_text: OCR extracted text
            schema: Notion database schema
            user_prompt: User-provided instructions

        Returns:
            Complete prompt for the agent
        """
        prompt_parts = [
            "# Output Schema",
            "Generate a JSON object matching this Notion database schema:",
            json.dumps(schema, indent=2),
            "",
            "# Video Content",
            "",
            "## Transcription (Audio)",
            transcription or "(No transcription available)",
            "",
            "## On-Screen Text (OCR)",
            ocr_text or "(No text detected)",
        ]

        if user_prompt:
            prompt_parts.extend(["", "# Additional Instructions", user_prompt])

        prompt_parts.extend(
            [
                "",
                "# Task",
                "Analyze the video content above and generate a JSON object that matches the provided schema.",
                "Extract relevant information from both the transcription and on-screen text.",
                "Return ONLY valid JSON without any markdown formatting or code blocks.",
            ]
        )

        return "\n".join(prompt_parts)

    def _call_agent(self, prompt: str) -> str:
        """
        Call ADK agent to process the prompt

        Args:
            prompt: The prompt to send to the agent

        Returns:
            Response text from the agent

        Raises:
            Exception: If the agent call fails
        """
        try:
            # Send prompt to the agent
            response = self.agent.run(prompt)

            # Extract text from response
            if hasattr(response, "text"):
                return response.text
            elif isinstance(response, dict):
                return response.get("text", str(response))
            else:
                return str(response)

        except Exception as e:
            logger.error(f"ADK agent call failed: {str(e)}")
            raise

    def _parse_response(self, response_text: str, schema: Dict) -> Dict[str, Any]:
        """
        Parse agent response into structured data matching Notion schema

        Args:
            response_text: JSON response from agent
            schema: Expected Notion schema structure

        Returns:
            Parsed and validated structured data

        Raises:
            ValueError: If response cannot be parsed or doesn't match schema
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            # Parse JSON response
            data = json.loads(cleaned_text)

            # Basic validation - ensure it's a dictionary
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data)}")

            # Validate against schema
            self._validate_schema(data, schema)

            logger.info(f"Successfully parsed response with {len(data)} fields")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from agent: {e}")

    def _validate_schema(self, data: Dict, schema: Dict) -> None:
        """
        Validate parsed response against Notion schema structure

        Args:
            data: Parsed data from agent
            schema: Expected Notion schema

        Raises:
            ValueError: If data doesn't match schema requirements
        """
        if not schema:
            # No schema provided, skip validation
            logger.debug("No schema provided, skipping validation")
            return

        # Extract property definitions from schema
        properties = schema.get("properties", {})

        if not properties:
            logger.debug("Schema has no properties defined, skipping validation")
            return

        # Check for required fields (if specified in schema)
        missing_fields = []
        for prop_name, prop_config in properties.items():
            # Check if field is required (Notion schemas may have this flag)
            is_required = prop_config.get("required", False)

            if is_required and prop_name not in data:
                missing_fields.append(prop_name)

        if missing_fields:
            raise ValueError(
                f"Missing required fields in response: {', '.join(missing_fields)}"
            )

        # Validate field types if specified
        type_errors = []
        for field_name, field_value in data.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")

                if expected_type:
                    # Basic type validation
                    type_map = {
                        "string": str,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }

                    expected_python_type = type_map.get(expected_type)

                    if expected_python_type and not isinstance(
                        field_value, expected_python_type
                    ):
                        type_errors.append(
                            f"{field_name}: expected {expected_type}, got {type(field_value).__name__}"
                        )

        if type_errors:
            raise ValueError(f"Type validation errors: {'; '.join(type_errors)}")

        logger.debug(f"Schema validation passed for {len(data)} fields")
