from dataclasses import dataclass
from typing import List

from model_library.registry_utils import get_registry_model

from .agent import Agent
from .utils import create_override_config
from .tools_base import RetrieveInformation
from ..tools.offline_web_search import OfflineGoogleWebSearch
from ..tools.offline_edgar_search import OfflineEdgarSearch
from ..tools.parse_cached_html import ParseCachedHtml


@dataclass
class Parameters:
    model_name: str
    max_turns: int
    tools: List[str]
    llm_config: dict


def get_agent(parameters: Parameters) -> Agent:
    available_tools = {
        "google_web_search": OfflineGoogleWebSearch,
        "retrieve_information": RetrieveInformation,
        "parse_cached_html": ParseCachedHtml,
        "edgar_search": OfflineEdgarSearch,
    }

    selected_tools = {}
    for tool in parameters.tools:
        if tool not in available_tools:
            raise ValueError(
                f"Tool {tool} not found. Available tools: {list(available_tools.keys())}"
            )
        selected_tools[tool] = available_tools[tool]()

    model = get_registry_model(
        parameters.model_name, create_override_config(**parameters.llm_config)
    )
    return Agent(tools=selected_tools, llm=model, max_turns=parameters.max_turns)
