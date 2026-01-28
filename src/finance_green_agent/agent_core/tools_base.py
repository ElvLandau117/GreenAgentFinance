import json
import os
import re
import traceback
from abc import ABC, abstractmethod

from model_library.base import LLM, ToolBody, ToolDefinition

from .logger import get_logger

tool_logger = get_logger(__name__)


class Tool(ABC):
    name: str
    description: str
    input_arguments: dict
    required_arguments: list[str]

    def __init__(self, *args, **kwargs):
        super().__init__()

    def get_tool_definition(self) -> ToolDefinition:
        body = ToolBody(
            name=self.name,
            description=self.description,
            properties=self.input_arguments,
            required=self.required_arguments,
        )
        return ToolDefinition(name=self.name, body=body)

    @abstractmethod
    def call_tool(self, arguments: dict, *args, **kwargs) -> list[str]:
        pass

    async def __call__(self, arguments: dict = None, *args, **kwargs) -> list[str]:
        tool_logger.info(
            f"[TOOL: {self.name.upper()}] Calling with arguments: {arguments}"
        )
        try:
            tool_result = await self.call_tool(arguments, *args, **kwargs)
            tool_logger.info(
                f"[TOOL: {self.name.upper()}] Returned: {tool_result}"
            )
            if self.name == "retrieve_information":
                return {
                    "success": True,
                    "result": tool_result["retrieval"],
                    "usage": tool_result["usage"],
                }
            return {"success": True, "result": json.dumps(tool_result)}
        except Exception as e:
            is_verbose = os.environ.get("FINANCE_GREEN_VERBOSE", "0") == "1"
            error_msg = str(e)
            if is_verbose:
                error_msg += f"\nTraceback: {traceback.format_exc()}"
            tool_logger.warning(
                f"[TOOL: {self.name.upper()}] Error: {error_msg}"
            )
            return {"success": False, "result": error_msg}


class RetrieveInformation(Tool):
    name: str = "retrieve_information"
    description: str = (
        "Retrieve information from stored documents using a prompt with {{key}} placeholders."
    )
    input_arguments: dict = {
        "prompt": {
            "type": "string",
            "description": "Prompt containing {{key}} placeholders for cached docs.",
        },
        "input_character_ranges": {
            "type": "object",
            "description": "Optional character ranges per key.",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "integer"},
            },
        },
    }
    required_arguments: list[str] = ["prompt"]

    async def call_tool(self, arguments: dict, data_storage: dict, model: LLM, *args, **kwargs):
        prompt: str = arguments.get("prompt")
        input_character_ranges = arguments.get("input_character_ranges", {}) or {}

        if not re.search(r"{{[^{}]+}}", prompt):
            raise ValueError(
                "Prompt must include at least one key in the format {{key}}."
            )

        keys = re.findall(r"{{([^{}]+)}}", prompt)
        formatted_data = {}

        for key in keys:
            if key not in data_storage:
                raise KeyError(
                    f"Key '{key}' not found in data storage. Available keys: {', '.join(data_storage.keys())}"
                )

            doc_content = data_storage[key]
            if key in input_character_ranges:
                char_range = input_character_ranges[key]
                if len(char_range) == 0:
                    formatted_data[key] = doc_content
                elif len(char_range) != 2:
                    raise ValueError(
                        f"Character range for key '{key}' must be two integers or empty list."
                    )
                else:
                    start_idx = int(char_range[0])
                    end_idx = int(char_range[1])
                    formatted_data[key] = doc_content[start_idx:end_idx]
            else:
                formatted_data[key] = doc_content

        formatted_prompt = re.sub(r"{{([^{}]+)}}", r"{\1}", prompt)
        try:
            prompt = formatted_prompt.format(**formatted_data)
        except KeyError as exc:
            raise KeyError(
                f"Key {str(exc)} not found in data storage. Available keys: {', '.join(data_storage.keys())}"
            )

        response = await model.query(prompt)
        return {
            "retrieval": response.output_text_str,
            "usage": {**response.metadata.model_dump()},
        }
