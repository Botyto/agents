from typing import Dict, List, Tuple
import os
from api.openweathermap import ExcludeInfo, OneCallResponse, OpenWeatherMapApi, Units
from ..engine.toolset import Toolset

ALERTS_ENABLED = False
HAS_API_KEY = bool(os.getenv("OPENWEATHERMAP_API_KEY"))


def _init(agent):
    if hasattr(agent, "_openweathermap"):
        return
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    setattr(agent, "_openweathermap", OpenWeatherMapApi(api_key, Units.METRIC))
    setattr(agent, "_openweathermap_latlon_cache", {})


def _latlon(agent, location: str):
    api: OpenWeatherMapApi = agent._openweathermap
    cache: Dict[str, Tuple[float, float]] = agent._openweathermap_latlon_cache
    lower = location.lower()
    result = cache.get(lower)
    if result is None:
        response = api.geocode(location)
        if not response:
            raise ValueError(f"Could not find location: {location}")
        result = response[0].lat, response[0].lon
        cache[lower] = result
    return result


def _process_alerts(alerts: List[OneCallResponse.Alert]|None):
    if not alerts:
        return []
    return [a.description for a in alerts]


def _format_response(
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
    if ALERTS_ENABLED and alerts:
        result["alerts"] = _process_alerts(alerts)
    return result


def current(agent, location: str):
    api: OpenWeatherMapApi = agent._openweathermap
    lat, lon = _latlon(agent, location)
    response = api.one_call(lat, lon, exclude=[ExcludeInfo.MINUTELY, ExcludeInfo.HOURLY, ExcludeInfo.DAILY])
    return _format_response(response.current, response.alerts)


def forecast_hourly(agent, location: str):
    api: OpenWeatherMapApi = agent._openweathermap
    lat, lon = _latlon(agent, location)
    response = api.one_call(lat, lon, exclude=[ExcludeInfo.CURRENT, ExcludeInfo.MINUTELY, ExcludeInfo.DAILY])
    result = {"hourly": [_format_response(hour, None) for hour in response.hourly]}
    if ALERTS_ENABLED and response.alerts:
        result["alerts"] = _process_alerts(response.alerts)
    return result


def forecast_daily(agent, location: str):
    api: OpenWeatherMapApi = agent._openweathermap
    lat, lon = _latlon(agent, location)
    response = api.one_call(lat, lon, exclude=[ExcludeInfo.CURRENT, ExcludeInfo.MINUTELY, ExcludeInfo.HOURLY])
    result = {"daily": [_format_response(day, None) for day in response.daily]}
    if ALERTS_ENABLED and response.alerts:
        result["alerts"] = _process_alerts(response.alerts)
    return result


toolset = Toolset(
    name="weather",
    description="Enables access to current and forecast weather data",
    agent_description="A helpful assistant with access to weather data. Ask them to tell you about the current or forecast weather.",
    agent_system_prompt="You are a helpful AI assistant with access to weather data (via the provided functions). In fact, your only job is to lookup the weather, so please help out where you can.",
    preferred_llm="mistral",
    functions=tuple(),
    init=_init,
)
