# %%
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

#wczytanie klucza api
load_dotenv()
API_KEY = os.getenv('API_KEY')

dzis = datetime.now().strftime('%Y-%m-%d')


URL = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={dzis}&end_date={dzis}&api_key={API_KEY}"

#zapytanie do serwera

response = requests.get(URL)

print("status połączenia:", response.status_code)

# %%
dane = response.json()

print("Główne sekcje w paczce to:", dane.keys())


# %%
#sprawdzamy łączną liczbę obiektów
liczba_asteroid = dane['element_count']
print(f"Liczba asteroid zidentyfikowanych dzisiaj: {liczba_asteroid}")

#liczba asteroid dla konkretnej daty
lista_asteroid = dane['near_earth_objects'][dzis]

#pierwszy element na liście
pierwsza_asteroida = lista_asteroid[0]

#sprawdzenie udostepnionych parametrow pierwszej asteroidy
print("Dane ukryte w pierwszej asteroidze:")
print(pierwsza_asteroida.keys())

# %%
import pandas as pd 
#zmiana listy na df
df = pd.DataFrame(lista_asteroid)

df.head()

# %%
#czyszczenie

#definiujemy listę kolumn, ktore chcemy zostawic
df = pd.DataFrame(lista_asteroid)

potrzebne_kolumny = [
    'name', 
    'absolute_magnitude_h', 
    'is_potentially_hazardous_asteroid', 
    'estimated_diameter', 
    'close_approach_data'
]

#nadpisanie tabeli odfiltrowana wersją

df = df[potrzebne_kolumny]

#wyciagniecie na probe srednicy zeby zobaczyc jak gleboko zagniezdzone sa nasze dane

srednica_pierwszej = df['estimated_diameter'].iloc[0]
print(srednica_pierwszej)

# %%
#tworzymy nowa kolumne wyciagajac dane z glebi slownika za pomoca lambda, bierzemy najwieksza szacowana wielkosc w metrach
df['diameter_meters_max'] = df['estimated_diameter'].apply(lambda x: x['meters']['estimated_diameter_max'])

#usuniecie starej zagniezdzonej kolumny

df = df.drop('estimated_diameter', axis=1)

df.head()


# %%
# wyciągamy prędkość w kilometrach na sekundę
# Krok po kroku: wejdź do listy [0] -> wejdź do 'relative_velocity' -> wejdź do 'kilometers_per_second'

df['velocity_km_s'] = df['close_approach_data'].apply(lambda x: x[0]['relative_velocity']['kilometers_per_second'])

#wyciagamy odległość ominięcia Ziemi w kilometrach
df['miss_distance_km'] = df['close_approach_data'].apply(lambda x: x[0]['miss_distance']['kilometers'])

#usuwamy stara zagniezdzona kolumne

df = df.drop('close_approach_data', axis=1)

#konwertujemy nowe kolumny na format liczbowy
# NASA API zwraca te dwie wartości jako tekst (string), co uniemożliwiłoby nam późniejsze wyliczenia i wykresy w Power BI

df['velocity_km_s'] = df['velocity_km_s'].astype(float)
df['miss_distance_km'] = df['miss_distance_km'].astype(float)

df.head()



# %%
# 1. Zamieniamy dystans na liczbę całkowitą (int), co usunie notacje naukową
df['miss_distance_km'] = df['miss_distance_km'].astype(int)

# 2. Zaokrąglamy prędkość obiektu do 2 miejsc po przecinku dla lepszej czytelności
df['velocity_km_s'] = df['velocity_km_s'].round(2)

# 3. Dodatkowo instruujemy Pandasa, żeby ewentualne inne duże liczby float 
# wyświetlał w standardowym formacie, a nie naukowym
pd.set_option('display.float_format', lambda x: f'{x:.2f}')

# 4. Sprawdzamy ostateczny wygląd naszej tabeli
df.head()

# %%
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

#wymuszamy ponowne wczytaniie pliku .env
load_dotenv(override=True)

#zaciagamy dane do logowania z .env
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Budujemy tzw. Connection String 

connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

#tworzymy silnik bazy danych

engine = create_engine(connection_string)

#  Wysyłamy tabelę (df) do bazy pod nazwą 'asteroidy_dzisiaj'
try:
    df.to_sql('asteroidy_dzisiaj', con=engine, if_exists='append', index=False)
    print("Sukces, dane załadowane w bazie SQL")
except Exception as e:
    print(f"Błąd połączenia lub zapisu: {e}")







# %%



