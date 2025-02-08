import requests

API_KEY = "ace11da998954c09aec14380b4ab481b"  # Replace with your real API key
CITY = "London"  # Change this to test with different cities

url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
response = requests.get(url).json()

# Print the response to debug
print(response)

# Check if 'weather' exists in response
if "weather" in response:
    weather_description = response['weather'][0]['description']
    temperature = response['main']['temp']
    print(f"The weather in {CITY} is {weather_description} with a temperature of {temperature}°C.")
else:
    print(f"Error: Weather data not found. Response: {response}")
