import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    weather = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip().title()
        api_key = os.getenv("OPENWEATHER_API_KEY")

        current_url = "https://api.openweathermap.org/data/2.5/weather"
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

        parameters = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }

        try:
            current_response = requests.get(
                current_url,
                params=parameters,
                timeout=10
            )

            if current_response.status_code == 200:
                data = current_response.json()
                condition = data["weather"][0]["main"].lower()

                # Default forecast values
                rain_expected = False
                rain_chance = 0

                forecast_response = requests.get(
                    forecast_url,
                    params=parameters,
                    timeout=10
                )

                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()

                    # Eight forecasts × three hours = next 24 hours
                    next_24_hours = forecast_data["list"][:8]

                    rain_conditions = {
                        "rain",
                        "drizzle",
                        "thunderstorm"
                    }

                    rain_expected = any(
                        item["weather"][0]["main"].lower()
                        in rain_conditions
                        for item in next_24_hours
                    )

                    rain_chance = round(
                        max(
                            item.get("pop", 0)
                            for item in next_24_hours
                        ) * 100
                    )

                if condition == "clear":
                    current_message = "The sky is currently clear and sunny."
                elif condition == "clouds":
                    current_message = "The sky is currently cloudy."
                elif condition in {"rain", "drizzle"}:
                    current_message = "It is currently raining."
                elif condition == "thunderstorm":
                    current_message = "There is currently a thunderstorm."
                elif condition == "snow":
                    current_message = "It is currently snowing."
                else:
                    current_message = (
                        f"Current conditions: "
                        f"{data['weather'][0]['description']}."
                    )

                if rain_expected:
                    forecast_message = (
                        "Rain is expected within the next 24 hours."
                    )
                else:
                    forecast_message = (
                        "No rain is expected within the next 24 hours."
                    )

                weather = {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "description": data["weather"][0]["description"],
                    "condition": condition,
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "current_message": current_message,
                    "forecast_message": forecast_message,
                    "rain_expected": rain_expected,
                    "rain_chance": rain_chance
                }

            elif current_response.status_code == 404:
                error = "City not found. Please check the spelling."

            elif current_response.status_code == 401:
                error = "The API key is invalid or not active yet."

            else:
                error = "Could not retrieve the weather."

        except requests.RequestException:
            error = "Could not connect to the weather service."

    return render_template(
        "index.html",
        weather=weather,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)