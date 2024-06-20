from autogen import GroupChat, UserProxyAgent, GroupChatManager
from autogen.agentchat.contrib.web_surfer import WebSurferAgent
import dotenv
import os

dotenv.load_dotenv(dotenv.find_dotenv())

llama3 = {"model": "llama3", "api_key": "ollama", "base_url": "http://localhost:11434/v1"}
import autogen.oai.client
import autogen.token_count_utils
autogen.oai.client.OAI_PRICE1K["llama3"] = (0.0, 0.0)
autogen.token_count_utils.max_token_limit["llama3"] = 16385

openai_api_key = os.getenv("OPENAI_API_KEY")
gpt4o = {"model": "gpt-4o", "api_key": openai_api_key}
gpt35 = {"model": "gpt-3.5-turbo", "api_key": openai_api_key}
gpt35_long = {"model": "gpt-3.5-turbo-16k", "api_key": openai_api_key}
active_gpt = gpt35


from agents.weather import OpenWeatherMapProvider, WeatherAgent
openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
weather_api = OpenWeatherMapProvider(api_key=openweathermap_api_key)
weather_agent = WeatherAgent("weather-helper", weather_api, llm_config=active_gpt)


user_proxy = UserProxyAgent(name="User",
                            llm_config=False,
                            code_execution_config=False,
                            human_input_mode="NEVER")


from autogen.browser_utils import DdgSearchProvider
surfer = WebSurferAgent(
    name="Web-surfer",
    llm_config=active_gpt,
    summarizer_llm_config={"config_list": [gpt35_long]},
    browser_config={"search_provider": DdgSearchProvider()}
)


group_chat = GroupChat(
    [
        weather_agent,
        surfer,
        user_proxy
    ],
    allow_repeat_speaker=False,
    role_for_select_speaker_messages="user",
    messages=[],
    send_introductions=True,
)
group_chat_manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llama3,
)


chat_result = user_proxy.initiate_chat(
    group_chat_manager,
    message="I live in Sofia, BG and I want to go outside today. Im wondering what activities I can do today.",
    summary_method="reflection_with_llm",
    summary_args={
        "summary_role": "user",
    },
)
#print(chat_result)
print(chat_result.summary)
pass
