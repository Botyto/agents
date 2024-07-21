from typing import List, Optional, Union
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
