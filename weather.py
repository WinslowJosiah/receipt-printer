import asyncio
from datetime import datetime
from io import BytesIO
import os
import pathlib
import re
import requests
from requests.exceptions import RequestException
from typing import Any

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from utils import get_font, get_printer

FILEDIR = pathlib.Path(__file__).parent


load_dotenv(".env")


# Get location
try:
    import winsdk.windows.devices.geolocation as wdg
    async def get_lat_long():
        locator = wdg.Geolocator()
        pos = await locator.get_geoposition_async()
        return pos.coordinate.latitude, pos.coordinate.longitude

    try:
        LATITUDE, LONGITUDE = asyncio.run(get_lat_long())
    except PermissionError:
        print(
            "Please allow access to your location. "
            "Using default coordinates."
        )
        LATITUDE, LONGITUDE = 38.897957, -77.036560
except ImportError:
    # try:
    #     r = requests.get("https://ipinfo.io/json")
    #     r.raise_for_status()
    # except RequestException as e:
    #     print("Error getting IP info!")
    #     raise SystemExit(e)

    # LATITUDE, LONGITUDE = map(float, r.json()["loc"].split(","))

    # HACK I wanted to use ipinfo.io to get location info from an IP
    # address, but being in a Wisconsin hospital makes it think I'm in
    # New York City, so that's an unviable option. For now, I'm asking
    # directly for a latitude and longitude.
    latlong = input(
        "Enter latitude and longitude (separated by comma): "
    )
    LATITUDE, LONGITUDE = map(float, latlong.split(","))


# Get formatted location name
try:
    r = requests.get(
        "https://api.opencagedata.com/geocode/v1/json",
        params={
            "key": os.getenv("OPENCAGE_API_KEY"),
            "q": f"{LATITUDE},{LONGITUDE}",
            "language": "en",
            "no_annotations": 1,
            "abbrv": 1,
        },
    )
    r.raise_for_status()
except RequestException as e:
    print("Error getting location name!")
    raise SystemExit(e)
location_components = r.json()["results"][0]["components"]
LOCATION = ", ".join(
    location_components[target]
    for target in (
        "neighborhood", "suburb", "city_district", "village", "town",
        "city", "state", "country",
    )
    if target in location_components
)


# Get weather forecast
try:
    r = requests.get(
        "https://weather.visualcrossing.com/VisualCrossingWebServices/"
        f"rest/services/timeline/{LATITUDE}%2C{LONGITUDE}/next7days",
        params={
            "key": os.getenv("VISUALCROSSING_API_KEY"),
            "unitGroup": "us",
            "iconSet": "icons2",
        },
    )
    r.raise_for_status()
except RequestException as e:
    print("Error getting weather!")
    raise SystemExit(e)
weather = r.json()
current_weather = weather["currentConditions"]
todays_weather = weather["days"][0]


def f_to_c(temp: float):
    return (temp - 32) * 5 / 9


def temperature_text(tempf: float):
    return f"{round(tempf)} F / {round(f_to_c(tempf))} C"


def temperature_image(
        temperature: Any,
        unit: str,
        size: int,
        font_size: int,
) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)
    font = get_font(__file__, r"ariblk.ttf", font_size)
    subfont = get_font(__file__, r"ariblk.ttf", font_size // 2)

    temptext = str(temperature)
    unittext = "°" + unit
    # Get size of temperature and unit text
    tempbbox = draw.textbbox((0, 0), temptext, font=font)
    unitbbox = draw.textbbox((0, 0), unittext, font=subfont)
    # Get width of temperature and unit text next to each other
    w = (tempbbox[2] - tempbbox[0]) + (unitbbox[2] - unitbbox[0])
    h = (tempbbox[3] - tempbbox[1])

    # Temperature text should be centered
    # NOTE The centering includes the width of the degree text.
    tx = (size - w) // 2 - tempbbox[0]
    ty = (size - h) // 2 - tempbbox[1]
    # Unit text X should be flush with the right of temperature text
    ux = tx + (tempbbox[2] - tempbbox[0])
    # Unit text Y should be flush with the top of temperature text
    uy = ty + unitbbox[1]

    draw.text((tx, ty), temptext, fill=(0, 0, 0), font=font)
    draw.text((ux, uy), unittext,fill=(0, 0, 0), font=subfont)
    img = img.crop((0, ty, size, ty + tempbbox[1] + tempbbox[3]))
    return img


def weather_image(
        icon_path: str,
        temp: float,
        width: int,
) -> Image.Image:
    # Create weather icon
    icon_size = width // 2
    icon = Image.open(icon_path)
    icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    icon = icon.filter(ImageFilter.UnsharpMask(percent=200))

    # Draw icon to side
    img = Image.new("RGBA", (width, icon_size), (255, 255, 255))
    img.alpha_composite(
        icon,
        (0, (img.height - icon.height) // 2),
    )

    # Create text for Fahrenheit temperature
    tempf_img = temperature_image(
        round(temp), "F",
        size=icon_size,
        font_size=icon_size // 2.25,
    )
    img.alpha_composite(
        tempf_img,
        (icon_size, img.height * 2 // 5 - tempf_img.height // 2),
    )

    # Create text for Celsius temperature
    tempc_img = temperature_image(
        round(f_to_c(temp)), "C",
        size=icon_size,
        font_size=icon_size // 4.75,
    )
    img.alpha_composite(
        tempc_img,
        (icon_size, img.height * 7 // 10 - tempc_img.height // 2),
    )

    return img


# Initialize printer
p = get_printer(__file__)
media_width = p.profile.profile_data["media"]["width"]["pixels"]
p.hw("INIT")
p.ln(3)

# Date / location
p.set(bold=True)
p.block_text(datetime.now().strftime("%A, %B %#d, %Y"))
p.set(bold=False)
p.ln()
p.block_text(LOCATION)
p.ln()

# Weather image (icon + temperature)
p.image(weather_image(
    icon_path=FILEDIR
        .joinpath("weather")
        .joinpath(current_weather["icon"] + ".png"),
    temp=current_weather["temp"],
    width=media_width,
))
p.ln()

# Weather description
p.set(double_height=True)
p.block_text(weather["description"])
p.set(normal_textsize=True)
p.ln(2)

# Temperature / "feels like"
p.block_text(f"Condition: {current_weather['conditions']}")
p.ln()
p.block_text(f"Temperature: {temperature_text(current_weather['temp'])}")
p.ln()
p.text(f"Feels like: {temperature_text(current_weather['feelslike'])}")
p.ln(2)

# High / low, precipitation chance, humidity
p.text(f"High: {temperature_text(todays_weather['tempmax'])}")
p.ln()
p.text(f"Low: {temperature_text(todays_weather['tempmin'])}")
p.ln()
p.block_text(f"Precip. chance: {round(todays_weather['precipprob'])}%")
p.ln()
p.block_text(f"Humidity: {round(todays_weather['humidity'])}%")
p.ln(2)

# Sunrise / sunset
sunrise = datetime.fromtimestamp(
    todays_weather["sunriseEpoch"]
).strftime("%I:%M %p")
p.block_text(f"Sunrise: {sunrise}")
p.ln()
sunset = datetime.fromtimestamp(
    todays_weather["sunsetEpoch"]
).strftime("%I:%M %p")
p.block_text(f"Sunset: {sunset}")
p.ln(4)

# Next 7 days forecast
p.set(underline=1, double_width=True, double_height=True)
p.textln("Weather Forecast")
p.set(underline=0, normal_textsize=True)
p.ln()
for day in weather["days"]:
    p.set(invert=True)
    this_datetime = datetime.strptime(day["datetime"], "%Y-%m-%d")
    p.text(this_datetime.strftime("%A, %B %#d, %Y"))
    p.ln()
    p.set(invert=False)

    p.set(bold=True)
    p.block_text(day["description"])
    p.ln(2)
    p.set(bold=False)

    p.text(f"High: {temperature_text(day['tempmax'])}")
    p.ln()
    p.text(f"Low: {temperature_text(day['tempmin'])}")
    p.ln(2)
p.ln(2)

# Weather alerts
alerts = weather.get("alerts", [])
if alerts:
    p.set(underline=1, double_width=True, double_height=True)
    p.textln("Weather Alerts")
    p.set(underline=0, normal_textsize=True)
    p.ln()

    for alert in alerts:
        p.set(invert=True)
        p.block_text(alert["event"])
        p.ln()
        p.set(bold=True, invert=False)
        p.block_text(alert["headline"])
        p.ln()
        p.set(bold=False)
        p.ln()
        description = alert["description"]
        if "\n\n" in description:
            description = re.sub(r"(.)\n(?!\n)", r"\1 ", description)
        for line in description.split("\n"):
            p.block_text(line)
            p.ln()
        p.ln()
    p.ln(3)

# Generation time
generated_time = datetime.now().isoformat(sep=" ", timespec="minutes")
p.block_text(f"Generated: {generated_time}")
p.ln()

# Padding
p.ln(6)
