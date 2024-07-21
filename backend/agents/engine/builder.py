from typing import Any, Dict, List, Optional, Tuple, Type, Union
from autogen import ConversableAgent
from autogen.agentchat.contrib.agent_builder import AgentBuilder
from autogen.agentchat.contrib.capabilities.agent_capability import AgentCapability


class AgentWithCapabilitiesBuilder(AgentBuilder):
    capabilities: List[AgentCapability]

    def __init__(
        self,
        capabilities: Optional[List[AgentCapability]] = [],
        config_file_or_env: Optional[str] = "OAI_CONFIG_LIST",
        config_file_location: Optional[str] = "",
        builder_model: Optional[Union[str, list]] = [],
        agent_model: Optional[Union[str, list]] = [],
        builder_model_tags: Optional[list] = [],
        agent_model_tags: Optional[list] = [],
        max_agents: Optional[int] = 5,
    ):
        super().__init__(
            config_file_or_env=config_file_or_env,
            config_file_location=config_file_location,
            builder_model=builder_model,
            agent_model=agent_model,
            builder_model_tags=builder_model_tags,
            agent_model_tags=agent_model_tags,
            max_agents=max_agents,
        )
        self.capabilities = capabilities or []

    AGENT_CAPABILITIES_PROMPT = """# Your goal
Considering the following task, what capabilities should the following expert have (if any).

# Expert name
{name}

# Available capabilities
{capabilities}

# Task requirement
- Only reply the names of the capabilities, separated by ",".
For example: YoutubeCapability, WebSurferCapability, ... """

    def _build_agent_capabilities(self, config: Dict[str, Any]):
        print(f"Preparing capabilities for {config['name']}", flush=True)
        capabilities_text = ", ".join(
            cap.__class__.__name__
            for cap in self.capabilities
        )
        resp_agent_capabilities = (
            self.builder_model.create(
                messages=[
                    {
                        "role": "user",
                        "content": self.AGENT_CAPABILITIES_PROMPT.format(**config, capabilities=capabilities_text),
                    }
                ]
            )
            .choices[0]
            .message.content
        )
        capabilities_list = [
            agent_name.strip()
            for agent_name in resp_agent_capabilities.split(",")
        ]
        capabilities_list = [
            cap
            for cap in self.capabilities
            if cap.__class__.__name__ in capabilities_list
        ]
        return capabilities_list

    def _agent_expand_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config["capabilities"] = self._build_agent_capabilities(config)
        super()._agent_expand_config(config)

    def _build_agents(
        self, use_oai_assistant: Optional[bool] = False, user_proxy: Optional[ConversableAgent] = None, **kwargs
    ) -> Tuple[List[ConversableAgent], Dict]:
        agent_list, cached_configs = super()._build_agents(
            use_oai_assistant=use_oai_assistant, user_proxy=user_proxy, **kwargs
        )
        for agent, config in zip(agent_list, cached_configs):
            if not config["capabilities"]:
                continue
            for cap_class_name in config["capabilities"]:
                cap_class: Type[AgentCapability]|None = next(
                    cap
                    for cap in self.capabilities
                    if cap.__class__.__name__ == cap_class_name
                )
                if cap_class is None:
                    continue
                cap = cap_class()
                cap.add_to_agent(agent)
        return agent_list, cached_configs
