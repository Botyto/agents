from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
import copy
from functools import wraps
import inspect
from typing import Callable, ClassVar, Dict, List, Literal, Optional, Tuple, Union
from autogen import OpenAIWrapper
from . import toolset


class AutogenAgent(ConversableAgent):
    DEFAULT_PROMPT: ClassVar[str] = "You are a helpful AI Assistant."
    DEFAULT_DESCRIPTION: ClassVar[str] = "A helpful AI Assistant."
    
    def __init__(
        self,
        name: str,
        toolsets: List[str],
        system_message: Optional[Union[str, List]] = None,
        is_termination_msg: Optional[Callable[[Dict], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = None,
        human_input_mode: Literal["ALWAYS", "NEVER", "TERMINATE"] = "TERMINATE",
        function_map: Optional[Dict[str, Callable]] = None,
        code_execution_config: Union[Dict, Literal[False]] = False,
        llm_config: Optional[Union[Dict, Literal[False]]] = None,
        default_auto_reply: Union[str, Dict] = "",
        description: Optional[str] = None,
        chat_messages: Optional[Dict[Agent, List[Dict]]] = None,
    ):
        if len(toolsets) == 1:
            main_set = toolset.find(toolsets[0])
            if not system_message:
                system_message = main_set.agent_system_prompt
            # TODO override other defaults

        system_message = system_message or self.DEFAULT_PROMPT
        description = description or self.DEFAULT_DESCRIPTION
        super().__init__(
            name=name,
            system_message=system_message,
            is_termination_msg=is_termination_msg,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            human_input_mode=human_input_mode,
            function_map=function_map,
            code_execution_config=code_execution_config,
            llm_config=llm_config,
            default_auto_reply=default_auto_reply,
            description=description,
            chat_messages=chat_messages,
        )

        inner_llm_config = copy.deepcopy(llm_config)

        # Does the decision making
        self._assistant = AssistantAgent(
            self.name + "_inner_assistant",
            system_message=system_message,  # type: ignore[arg-type]
            llm_config=inner_llm_config,
            is_termination_msg=lambda m: False,
        )

        # plays the role of the API
        self._user_proxy = UserProxyAgent(
            self.name + "_inner_user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            default_auto_reply="",
            is_termination_msg=lambda m: False,
        )

        if inner_llm_config not in [None, False]:
            self._register_toolsets(toolsets)

        self.register_reply([Agent, None], self.__class__.generate_api_reply, remove_other_reply_funcs=True)
        self.register_reply([Agent, None], ConversableAgent.generate_code_execution_reply)
        self.register_reply([Agent, None], ConversableAgent.generate_function_call_reply)
        self.register_reply([Agent, None], ConversableAgent.check_termination_and_human_reply)

    def _register_toolsets(self, toolsets: List[str]):
        def wrap_tool(tool):
            @wraps(tool)
            def wrapped_tool(*args, **kwargs):
                return tool(self, *args, **kwargs)
            return wrapped_tool
        for set_name in toolsets:
            set = toolset.find(set_name)
            if set.init:
                set.init(self)
            functions = []
            for func in set.functions:
                if func.__name__ in self.function_map:
                    continue
                argspec = inspect.getfullargspec(func)
                if argspec.args and argspec.args[0] == "self":
                    func = wrap_tool(func)
                functions.append(func)
            self._register_functions(functions)

    def _register_functions(self, tools: List[Callable]):
        for tool in tools:
            assert tool.__doc__, f"Tool {tool.__name__} must have a docstring."
            self._assistant.register_for_llm(description=tool.__doc__)(tool)
            self._user_proxy.register_for_execution()(tool)

    def generate_api_reply(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        sender: Optional[Agent] = None,
        config: Optional[OpenAIWrapper] = None,
    ) -> Tuple[bool, Optional[Union[str, Dict[str, str]]]]:
        """Generate a reply using autogen.oai."""
        if messages is None:
            messages = self._oai_messages[sender]

        self._user_proxy.reset()  # type: ignore[no-untyped-call]
        self._assistant.reset()  # type: ignore[no-untyped-call]

        # Clone the messages to give context
        self._assistant.chat_messages[self._user_proxy] = list()
        history = messages[0 : len(messages) - 1]
        for message in history:
            self._assistant.chat_messages[self._user_proxy].append(message)

        self._user_proxy.send(messages[-1]["content"], self._assistant, request_reply=True, silent=True)
        agent_reply = self._user_proxy.chat_messages[self._assistant][-1]
        # print("Agent Reply: " + str(agent_reply))
        proxy_reply = self._user_proxy.generate_reply(
            messages=self._user_proxy.chat_messages[self._assistant], sender=self._assistant
        )
        # print("Proxy Reply: " + str(proxy_reply))

        if proxy_reply == "":  # Was the default reply
            return True, None if agent_reply is None else agent_reply["content"]
        else:
            return True, None if proxy_reply is None else proxy_reply["content"]  # type: ignore[index]
