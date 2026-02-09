import psycopg2
import requests
import time
import sys
DB_HOST = ""
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {'User-Agent': 'TransportAgencyApp/1.0'}
PARAMS = {'format': 'json', 'limit': 1}
DELAY = 1
def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)

def geocode_city(city, country):
    query = f"{city}, {country}"
    response = requests.get(GEOCODER_URL, params={**PARAMS, 'q': query}, headers=HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, city, country FROM directions WHERE latitude IS NULL AND longitude IS NULL ORDER BY id;")
    cities_to_geocode = cur.fetchall()
    total = len(cities_to_geocode)
    if total == 0:
        cur.close()
        conn.close()
        return
    processed = 0
    for city_id, city_name, country_name in cities_to_geocode:
        processed += 1
        print(f"[{processed}/{total}] Ищу '{city_name}, {country_name}'...")
        lat, lon = geocode_city(city_name, country_name)
        cur.execute("UPDATE directions SET latitude = %s, longitude = %s WHERE id = %s", (lat, lon, city_id))
        print(f"   -> Найдено: {lat}, {lon}")
        conn.commit()
        time.sleep(DELAY)
    cur.close()
    conn.close()
    print("Готово!")

if __name__ == "__main__":
    main()