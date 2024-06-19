from dataclasses import dataclass
import datetime
from enum import Enum
import requests
from typing import Dict, List
from urllib.parse import urlparse, urlunparse


class Units(Enum):
    STANDARD = "standard"
    METRIC = "metric"
    IMPERIAL = "imperial"


class ExcludeInfo(Enum):
    CURRENT = "current"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    ALERTS = "alerts"


SUPPORTED_LANGUAGES = {
    "sq","af","ar","az","eu","be","bg","ca","zh_cn",
    "zh_tw","hr","cz","da","nl","en","fi","fr","gl",
    "de","el","he","hi","hu","is","id","it","ja","kr",
    "ku","la","lt","mk","no","fa","pl","pt","pt_br",
    "ro","ru","sr","sk","sl","sp","sv","th","tr","ua",
    "vi","zu",
}


class OpenWeatherMapApi:
    api_key: str
    units: "Units"
    language: str
    session: requests.Session

    def __init__(self, api_key: str, units: Units = Units.METRIC, language: str = "en"):
        self.api_key = api_key
        self.units = units
        assert language in SUPPORTED_LANGUAGES, f"Unsupported language: {language}"
        self.language = language
        self.session = requests.Session()

    def _get(self, url: str):
        schema, netloc, path, params, query, fragment = urlparse(url)
        if query:
            query += "&"
        query = f"{query}appid={self.api_key}&units={self.units.value}&lang={self.language}"
        url = urlunparse((schema, netloc, path, params, f"{query}&appid={self.api_key}", fragment))
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def one_call(self, lon: float, lat: float, exclude: List[ExcludeInfo] = []):
        exclude_str = ",".join(exclude)
        data = self._get(f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude_str}")
        return OneCallResponse(data)

    def timemachine(self, lon: float, lat: float, dt: datetime.datetime):
        data = self._get(f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&dt={int(dt.timestamp())}")
        return TimemachineResponse(data)

    def day_summary(self, lon: float, lat: float, date: datetime.date):
        data = self._get(f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&dt={date.isoformat()}")
        return DaySummaryResponse(data)
    
    def overview(self, lon: float, lat: float):
        data = self._get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}")
        return OverviewResponse(data)
    
    def geocode(self, query: str, limit: int = 5):
        assert limit <= 5
        data = self._get(f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit={limit}")
        return [GeocodeResponse(item) for item in data]


@dataclass(frozen=True)
class Icon:
    day: str
    night: str
    description: str

    def url(self, size: int = 2, day: bool = True):
        assert size in {2, 4}
        code = self.day if day else self.night
        return f"http://openweathermap.org/img/wn/{code}@{size}x.png"
    
    @classmethod
    def find(self, code: str):
        if len(code) > 2:
            code = code[:2]
        result = ALL_ICONS.get(code)
        if result is not None:
            return result
        return Icon("01d", "01n", "unknown")


ALL_ICONS = {
    "01": Icon("01d", "01n", "clear sky"),
    "02": Icon("02d", "02n", "few clouds"),
    "03": Icon("03d", "03n", "scattered clouds"),
    "04": Icon("04d", "04n", "broken clouds"),
    "09": Icon("09d", "09n", "shower rain"),
    "10": Icon("10d", "10n", "rain"),
    "11": Icon("11d", "11n", "thunderstorm"),
    "13": Icon("13d", "13n", "snow"),
    "50": Icon("50d", "50n", "mist "),
}



@dataclass(frozen=True)
class Condition:
    code: int
    group: str
    description: str
    icon: Icon

    @classmethod
    def find(cls, code: int):
        result = ALL_CONDITIONS.get(code)
        if result is not None:
            return result
        return Condition(code, "Unknown", "unknown", Icon.find("50"))


ALL_CONDITIONS = {
    Condition(200, "Thunderstorm", "thunderstorm with light rain", Icon.find("11")),
    Condition(201, "Thunderstorm", "thunderstorm with rain", Icon.find("11")),
    Condition(202, "Thunderstorm", "thunderstorm with heavy rain", Icon.find("11")),
    Condition(210, "Thunderstorm", "light thunderstorm", Icon.find("11")),
    Condition(211, "Thunderstorm", "thunderstorm", Icon.find("11")),
    Condition(212, "Thunderstorm", "heavy thunderstorm", Icon.find("11")),
    Condition(221, "Thunderstorm", "ragged thunderstorm", Icon.find("11")),
    Condition(230, "Thunderstorm", "thunderstorm with light drizzle", Icon.find("11")),
    Condition(231, "Thunderstorm", "thunderstorm with drizzle", Icon.find("11")),
    Condition(232, "Thunderstorm", "thunderstorm with heavy drizzle", Icon.find("11")),
    Condition(300, "Drizzle", "light intensity drizzle", Icon.find("09")),
    Condition(301, "Drizzle", "drizzle", Icon.find("09")),
    Condition(302, "Drizzle", "heavy intensity drizzle", Icon.find("09")),
    Condition(310, "Drizzle", "light intensity drizzle rain", Icon.find("09")),
    Condition(311, "Drizzle", "drizzle rain", Icon.find("09")),
    Condition(312, "Drizzle", "heavy intensity drizzle rain", Icon.find("09")),
    Condition(313, "Drizzle", "shower rain and drizzle", Icon.find("09")),
    Condition(314, "Drizzle", "heavy shower rain and drizzle", Icon.find("09")),
    Condition(321, "Drizzle", "shower drizzle", Icon.find("09")),
    Condition(500, "Rain", "light rain", Icon.find("10")),
    Condition(501, "Rain", "moderate rain", Icon.find("10")),
    Condition(502, "Rain", "heavy intensity rain", Icon.find("10")),
    Condition(503, "Rain", "very heavy rain", Icon.find("10")),
    Condition(504, "Rain", "extreme rain", Icon.find("10")),
    Condition(511, "Rain", "freezing rain", Icon.find("13")),
    Condition(520, "Rain", "light intensity shower rain", Icon.find("09")),
    Condition(521, "Rain", "shower rain", Icon.find("09")),
    Condition(522, "Rain", "heavy intensity shower rain", Icon.find("09")),
    Condition(531, "Rain", "ragged shower rain", Icon.find("09")),
    Condition(600, "Snow", "light snow", Icon.find("13")),
    Condition(601, "Snow", "snow", Icon.find("13")),
    Condition(602, "Snow", "heavy snow", Icon.find("13")),
    Condition(611, "Snow", "sleet", Icon.find("13")),
    Condition(612, "Snow", "light shower sleet", Icon.find("13")),
    Condition(613, "Snow", "shower sleet", Icon.find("13")),
    Condition(615, "Snow", "light rain and snow", Icon.find("13")),
    Condition(616, "Snow", "rain and snow", Icon.find("13")),
    Condition(620, "Snow", "light shower snow", Icon.find("13")),
    Condition(621, "Snow", "shower snow", Icon.find("13")),
    Condition(622, "Snow", "heavy shower snow", Icon.find("13")),
    Condition(701, "Mist", "mist", Icon.find("50")),
    Condition(711, "Smoke", "smoke", Icon.find("50")),
    Condition(721, "Haze", "haze", Icon.find("50")),
    Condition(731, "Dust", "sand/dust whirls", Icon.find("50")),
    Condition(741, "Fog", "fog", Icon.find("50")),
    Condition(751, "Sand", "sand", Icon.find("50")),
    Condition(761, "Dust", "dust", Icon.find("50")),
    Condition(762, "Ash", "volcanic ash", Icon.find("50")),
    Condition(771, "Squall", "squalls", Icon.find("50")),
    Condition(781, "Tornado", "tornado", Icon.find("50")),
    Condition(800, "Clear", "clear sky", Icon.find("01")),
    Condition(801, "Clouds", "few clouds: 11-25%", Icon.find("02")),
    Condition(802, "Clouds", "scattered clouds: 25-50%", Icon.find("03")),
    Condition(803, "Clouds", "broken clouds: 51-84%", Icon.find("04")),
    Condition(804, "Clouds", "overcast clouds: 85-100%", Icon.find("04")),
}
ALL_CONDITIONS = {cond.code: cond for cond in ALL_CONDITIONS}


class GeocodeResponse:
    name: str
    local_names: Dict[str, str]|None
    lat: float
    lon: float
    country: str
    state: str|None

    def __init__(self, data: dict):
        self.name = data["name"]
        self.local_names = data.get("local_names")
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.country = data["country"]
        self.state = data.get("state")


class OverviewResponse:
    lat: float
    lon: float
    tz: str
    date: datetime.date
    units: Units
    weather_overview: str

    def __init__(self, data: dict):
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.tz = data["timezone"]
        self.date = datetime.date.fromisoformat(data["date"])
        self.units = Units(data["units"])
        self.weather_overview = data["weather_overview"]


class DaySummaryResponse:
    @dataclass
    class CloudsCover:
        afternoon: float

    @dataclass
    class Humidity:
        afternoon: float

    @dataclass
    class Precipitation:
        total: float

    @dataclass
    class Pressure:
        afternoon: float

    @dataclass
    class Temperature:
        min: float
        max: float
        afternoon: float
        night: float
        evening: float
        morning: float

    @dataclass
    class WindDetails:
        speed: float
        direction: float

    @dataclass
    class Wind:
        max: "DaySummaryResponse.WindDetails"

    lat: float
    lon: float
    tz: str
    date: datetime.date
    units: Units
    clouds: "DaySummaryResponse.CloudsCover"
    humidity: "DaySummaryResponse.Humidity"
    precipitation: "DaySummaryResponse.Precipitation"
    pressure: "DaySummaryResponse.Pressure"
    temperature: "DaySummaryResponse.Temperature"
    wind: "DaySummaryResponse.Wind"

    def __init__(self, data: dict):
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.tz = data["timezone"]
        self.date = datetime.date.fromisoformat(data["date"])
        self.units = Units(data["units"])
        self.clouds = self.CloudsCover(data["clouds"]["afternoon"])
        self.humidity = self.Humidity(data["humidity"]["afternoon"])
        self.precipitation = self.Precipitation(data["precipitation"]["total"])
        self.pressure = self.Pressure(data["pressure"]["afternoon"])
        self.temperature = self.Temperature(
            data["temperature"]["min"],
            data["temperature"]["max"],
            data["temperature"]["afternoon"],
            data["temperature"]["night"],
            data["temperature"]["evening"],
            data["temperature"]["morning"],
        )
        self.wind = DaySummaryResponse.Wind(DaySummaryResponse.WindDetails(data["wind"]["speed"], data["wind"]["direction"]))


class WeatherDetails:
    id: int
    main: str
    description: str
    icon: str

    def __init__(self, data: dict):
        self.id = data["id"]
        self.main = data["main"]
        self.description = data["description"]
        self.icon = data["icon"]


class TimemachineResponse:
    class DataPoint:
        dt: int
        sunrise: int
        sunset: int
        temp: float
        feels_like: float
        pressure: float
        humidity: float
        dew_point: float
        uvi: float
        clouds: float
        visibility: float
        wind_speed: float
        wind_deg: float
        weather: WeatherDetails

        def __init__(self, data: dict):
            self.dt = data["dt"]
            self.sunrise = data["sunrise"]
            self.sunset = data["sunset"]
            self.temp = data["temp"]
            self.feels_like = data["feels_like"]
            self.pressure = data["pressure"]
            self.humidity = data["humidity"]
            self.dew_point = data["dew_point"]
            self.uvi = data["uvi"]
            self.clouds = data["clouds"]
            self.visibility = data["visibility"]
            self.wind_speed = data["wind_speed"]
            self.wind_deg = data["wind_deg"]
            self.weather = WeatherDetails(data["weather"])

    lat: float
    lon: float
    timezone: str
    timezone_offset: int
    data: List[DataPoint]

    def __init__(self, data: dict):
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.timezone = data["timezone"]
        self.timezone_offset = data["timezone_offset"]
        self.data = [TimemachineResponse.DataPoint(item) for item in data["data"]]


class OneCallResponse:
    class Rain:
        one_h: float|None

        def __init__(self, data: dict):
            self.one_h = data.get("1h")

    class Snow(Rain):
        pass

    class Current:
        dt: datetime.datetime
        sunrise: datetime.datetime
        sunset: datetime.datetime
        temp: float
        feels_like: float
        pressure: float
        humidity: float
        dew_point: float
        clouds: float
        uvi: float
        visibility: float
        wind_speed: float
        wind_gust: float|None
        wind_deg: float
        rain: "OneCallResponse.Rain"
        snow: "OneCallResponse.Snow"
        weather: WeatherDetails

        def __init__(self, data: dict):
            self.dt = datetime.datetime.fromtimestamp(data["dt"])
            self.sunrise = datetime.datetime.fromtimestamp(data["sunrise"])
            self.sunset = datetime.datetime.fromtimestamp(data["sunset"])
            self.temp = data["temp"]
            self.feels_like = data["feels_like"]
            self.pressure = data["pressure"]
            self.humidity = data["humidity"]
            self.dew_point = data["dew_point"]
            self.clouds = data["clouds"]
            self.uvi = data["uvi"]
            self.visibility = data["visibility"]
            self.wind_speed = data["wind_speed"]
            self.wind_gust = data.get("wind_gust")
            self.wind_deg = data["wind_deg"]
            self.rain = OneCallResponse.Rain(data["rain"])
            self.snow = OneCallResponse.Snow(data["snow"])
            self.weather = WeatherDetails(data["weather"])


    class Minutely:
        dt: datetime.datetime
        precipitation: float
        
        def __init__(self, data: dict):
            self.dt = datetime.datetime.fromtimestamp(data["dt"])
            self.precipitation = data["precipitation"]


    class Hourly:
        dt: datetime.datetime
        temp: float
        feels_like: float
        pressure: float
        humidity: float
        dew_point: float
        uvi: float
        clouds: float
        visibility: float
        wind_speed: float
        wind_gust: float|None
        wind_deg: float
        pop: float
        rain: "OneCallResponse.Rain"
        snow: "OneCallResponse.Snow"
        weather: WeatherDetails

        def __init__(self, data: dict):
            self.dt = datetime.datetime.fromtimestamp(data["dt"])
            self.temp = data["temp"]
            self.feels_like = data["feels_like"]
            self.pressure = data["pressure"]
            self.humidity = data["humidity"]
            self.dew_point = data["dew_point"]
            self.uvi = data["uvi"]
            self.clouds = data["clouds"]
            self.visibility = data["visibility"]
            self.wind_speed = data["wind_speed"]
            self.wind_gust = data.get("wind_gust")
            self.wind_deg = data["wind_deg"]
            self.pop = data["pop"]
            self.rain = OneCallResponse.Rain(data["rain"])
            self.snow = OneCallResponse.Snow(data["snow"])
            self.weather = WeatherDetails(data["weather"])


    class DailyFeelsLike:
        morn: float
        day: float
        eve: float
        night: float

        def __init__(self, data: dict):
            self.morn = data["morn"]
            self.day = data["day"]
            self.eve = data["eve"]
            self.night = data["night"]


    class DailyTemp(DailyFeelsLike):
        min: float
        max: float

        def __init__(self, data: dict):
            super().__init__(data)
            self.min = data["min"]
            self.max = data["max"]


    class Daily:
        dt: datetime.datetime
        sunrise: datetime.datetime
        sunset: datetime.datetime
        moonrise: datetime.datetime
        moonset: datetime.datetime
        moon_phase: float
        summary: str
        temp: "OneCallResponse.DailyTemp"
        feels_like: "OneCallResponse.DailyFeelsLike"
        pressure: float
        humidity: float
        dew_point: float
        wind_speed: float
        wind_gust: float|None
        wind_deg: float
        clouds: float
        uvi: float
        pop: float
        rain: float
        snow: float
        weather: WeatherDetails

        def __init__(self, data: dict):
            self.dt = datetime.datetime.fromtimestamp(data["dt"])
            self.sunrise = datetime.datetime.fromtimestamp(data["sunrise"])
            self.sunset = datetime.datetime.fromtimestamp(data["sunset"])
            self.moonrise = datetime.datetime.fromtimestamp(data["moonrise"])
            self.moonset = datetime.datetime.fromtimestamp(data["moonset"])
            self.moon_phase = data["moon_phase"]
            self.summary = data["summary"]
            self.temp = OneCallResponse.DailyTemp(data["temp"])
            self.feels_like = OneCallResponse.DailyFeelsLike(data["feels_like"])
            self.pressure = data["pressure"]
            self.humidity = data["humidity"]
            self.dew_point = data["dew_point"]
            self.wind_speed = data["wind_speed"]
            self.wind_gust = data.get("wind_gust")
            self.wind_deg = data["wind_deg"]
            self.clouds = data["clouds"]
            self.uvi = data["uvi"]
            self.pop = data["pop"]
            self.rain = data["rain"]
            self.snow = data["snow"]
            self.weather = WeatherDetails(data["weather"])


    class Alert:
        sender_name: str
        event: str
        start: datetime.datetime
        end: datetime.datetime
        description: str
        tags: List[str]

        def __init__(self, data: dict):
            self.sender_name = data["sender_name"]
            self.event = data["event"]
            self.start = datetime.datetime.fromtimestamp(data["start"])
            self.end = datetime.datetime.fromtimestamp(data["end"])
            self.description = data["description"]
            self.tags = data["tags"]


    lat: float
    lon: float
    timezone: str
    timezone_offset: int
    current: Current|None
    minutely: List[Minutely]|None
    hourly: List[Hourly]|None
    daily: List[Daily]|None
    alerts: List[Alert]|None

    def __init__(self, data: dict):
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.timezone = data["timezone"]
        self.timezone_offset = data["timezone_offset"]
        self.current = OneCallResponse.Current(data["current"]) if "current" in data else None
        self.minutely = [OneCallResponse.Minutely(item) for item in data["minutely"]] if "minutely" in data else None
        self.hourly = [OneCallResponse.Hourly(item) for item in data["hourly"]] if "hourly" in data else None
        self.daily = [OneCallResponse.Daily(item) for item in data["daily"]] if "daily" in data else None
        self.alerts = [OneCallResponse.Alert(item) for item in data["alerts"]] if "alerts" in data else None
