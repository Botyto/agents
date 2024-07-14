import dotenv
import os

dotenv.load_dotenv(dotenv.find_dotenv())


def litellm_fn_call():
    mistral = {"model": "mistral", "api_key": "ollama", "base_url": "http://localhost:11434/v1"}
    litellm = {"model": "mistral", "api_key": "dummy", "base_url": "http://localhost:4000"}
    import autogen.oai.client
    import autogen.token_count_utils
    autogen.oai.client.OAI_PRICE1K["mistral"] = (0.0, 0.0)
    autogen.token_count_utils.max_token_limit["mistral"] = 8192

    from agents.weather import OpenWeatherMapProvider, WeatherAgent
    openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    weather_api = OpenWeatherMapProvider(api_key=openweathermap_api_key)
    weather_agent = WeatherAgent("weather-helper", weather_api, llm_config=litellm)

    from autogen import UserProxyAgent
    user_proxy = UserProxyAgent(name="User",
                                llm_config=False,
                                code_execution_config=False,
                                human_input_mode="ALWAYS")

    chat_result = user_proxy.initiate_chat(
        weather_agent,
        message="What's the weather like today in Sofia, BG?",
    )
    print(chat_result.summary)
    pass


def whisper_test():
    wav_path = "C:/Users/DESKTOP/Desktop/short.ogg"
    from api.oai_whisper import WhisperClient, MEDIUM
    client = WhisperClient(MEDIUM)
    result = client.transcribe(wav_path)
    print(result)
    pass


if __name__ == "__main__":
    # litellm_fn_call()
    whisper_test()
