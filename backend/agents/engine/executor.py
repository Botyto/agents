from dataclasses import dataclass
from typing import Callable
from .agent import AutogenAgent
from .builder import AgentWithToolsBuilder


@dataclass(frozen=True)
class Context:
    prompt: str
    on_msg: Callable[[AutogenAgent, str], None]


def execute_task(context: Context):
    builder = AgentWithToolsBuilder(
        toolsets=[],
        config_File_or_env=None,
        config_file_location=None,
        builder_model=None,
        agent_model=None,
        builder_model_tags=None,
        agent_model_tags=None,
        max_agents=5,
    )
    agent_list, cached_configs = builder.build(
        building_task=context.prompt,
        default_llm_config=None,
        coding=True,
        code_execution_config=None,
        use_oai_assistant=False,
        user_proxy=None,
        max_agents=None,
    )
    # ...
