from abc import ABC, abstractmethod
from autogen import Agent
from datetime import datetime
from typing import Annotated, Callable, Dict, List, Literal, Optional, Tuple, Union

from .api import ApiAgent
from api.openweathermap import ExcludeInfo, OneCallResponse, OpenWeatherMapApi, Units


class WeatherProvider(ABC):
    @abstractmethod
    def current(self, location: str) -> dict:
        ...

    @abstractmethod
    def forecast_daily(self, location: str) -> dict:
        ...

    @abstractmethod
    def forecast_hourly(self, location: str) -> dict:
        ...


class OpenWeatherMapProvider(WeatherProvider):
    api: OpenWeatherMapApi
    _latlon_cache: Dict[str, Tuple[float, float]]
    _alerts: bool

    def __init__(self, api_key: str, alerts: bool = False):
        self.api = OpenWeatherMapApi(api_key, units=Units.METRIC)
        self._alerts = alerts
        self._latlon_cache = {}

    def _latlon(self, location: str):
        lower = location.lower()
        result = self._latlon_cache.get(lower)
        if result is None:
            response = self.api.geocode(location)
            if not response:
                raise ValueError(f"Could not find location: {location}")
            result = response[0].lat, response[0].lon
            self._latlon_cache[lower] = result
        return result

    def _process_alerts(self, alerts: List[OneCallResponse.Alert]|None):
        if not alerts:
            return []
        return [a.description for a in alerts]
    
    def _format_response(
            self,
            entry: OneCallResponse.Current|OneCallResponse.Hourly|OneCallResponse.Daily,
            alerts: List[OneCallResponse.Alert]|None,
    ):
        result = {
            "temp_c": entry.temp,
            "wind_meter_per_sec": entry.wind_speed,
            "weather": entry.weather.main,
        }
        if isinstance(entry.rain, float):
            if entry.rain > 0:
                result["rain_mm_per_h"] = entry.rain
        elif entry.rain:
            result["rain_mm_per_h"] = entry.rain.one_h
        if isinstance(entry.snow, float):
            if entry.snow > 0:
                result["snow_mm_per_h"] = entry.snow
        elif entry.snow:
            result["snow_mm_per_h"] = entry.snow.one_h
        if self._alerts and alerts:
            result["alerts"] = self._process_alerts(alerts)
        return result

    def current(self, location: str):
        lat, lon = self._latlon(location)
        response = self.api.one_call(lat, lon, exclude=[ExcludeInfo.MINUTELY, ExcludeInfo.HOURLY, ExcludeInfo.DAILY])
        return self._format_response(response.current, response.alerts)

    def forecast_hourly(self, location: str):
        lat, lon = self._latlon(location)
        response = self.api.one_call(lat, lon, exclude=[ExcludeInfo.CURRENT, ExcludeInfo.MINUTELY, ExcludeInfo.DAILY])
        result = {"hourly": [self._format_response(hour, None) for hour in response.hourly]}
        if self._alerts and response.alerts:
            result["alerts"] = self._process_alerts(response.alerts)
        return result

    def forecast_daily(self, location: str):
        lat, lon = self._latlon(location)
        response = self.api.one_call(lat, lon, exclude=[ExcludeInfo.CURRENT, ExcludeInfo.MINUTELY, ExcludeInfo.HOURLY])
        result = {"daily": [self._format_response(day, None) for day in response.daily]}
        if self._alerts and response.alerts:
            result["alerts"] = self._process_alerts(response.alerts)
        return result


class WeatherAgent(ApiAgent):
    DEFAULT_PROMPT = (
        "You are a helpful AI assistant with access to weather data (via the provided functions). "
        "In fact, your only job is to lookup the weather, so please help out where you can. "
        "Today's date is " + datetime.now().date().isoformat()
    )

    DEFAULT_DESCRIPTION = (
        "A helpful assistant with access to weather data. "
        "Ask them to tell you about the current or forecast weather."
    )

    def __init__(
        self,
        name: str,
        weather_provider: WeatherProvider,
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
        def get_current_weather(location: Annotated[str, "Where to query the weather"]) -> dict:
            """Get the current weather for a location."""
            return weather_provider.current(location)
        
        def get_hourly_forecast(location: Annotated[str, "Where to query the weather"]) -> dict:
            """Get the hourly forecast for a location."""
            return weather_provider.forecast_hourly(location)
        
        def get_daily_forecast(location: Annotated[str, "Where to query the weather"]) -> dict:
            """Get the daily forecast for a location."""
            return weather_provider.forecast_daily(location)

        super().__init__(
            name=name,
            tools=[get_current_weather, get_hourly_forecast, get_daily_forecast],
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
