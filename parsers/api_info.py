from config_data import config


API_KEY = config.RAPID_API_KEY

url_locations = 'https://hotels4.p.rapidapi.com/locations/v2/search/'
url_hotels = 'https://hotels4.p.rapidapi.com/properties/list'
url_hotel_photo = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
host = 'hotels4.p.rapidapi.com'

headers = {
    'X-RapidAPI-Host': host,
    'X-RapidAPI-Key': API_KEY
  }
