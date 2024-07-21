from dataclasses import dataclass
from typing import Callable, Iterable, List


class Toolset:
    name: str
    description: str
    agent_description: str
    agent_system_prompt: str
    preferred_llm: str
    functions: Iterable[Callable]
    init: Callable|None

    def __init__(
        self,
        name: str,
        description: str,
        agent_description: str,
        agent_system_prompt: str,
        preferred_llm: str,
        functions: Iterable[Callable],
        init: Callable|None,
    ):
        self.name = name
        self.description = description
        self.agent_description = agent_description
        self.agent_system_prompt = agent_system_prompt
        self.preferred_llm = preferred_llm
        self.functions = functions
        self.init = init


TOOLSETS: List[Toolset] = []


def register(toolset: Toolset):
    TOOLSETS.append(toolset)


def find(name: str) -> Toolset:
    for toolset in TOOLSETS:
        if toolset.name == name:
            return toolset
    raise ValueError(f"Toolset {name} not found")
