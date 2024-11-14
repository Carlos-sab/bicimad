import io
import re
import zipfile
from typing import TextIO
from urllib.parse import urljoin

import pandas as pd
import requests


class UrlEMT:
    """Clase para gestionar y obtener URLs de la EMT."""

    EMT = r"https://opendata.emtmadrid.es/"
    GENERAL = r"/Datos-estaticos/Datos-generales-(1)"

    def __init__(self):
        self.enlaces_validos = UrlEMT.select_valid_urls()

    def get_url(self, month: int, year: int) -> str:
        """
        Obtiene la URL específica para el mes y año indicados.

        :param month: Mes en formato numérico (1-12).
        :param year: Año en formato numérico (21, 22 o 23).
        :raises ValueError: Si el mes o año no son válidos o si no se encuentra un enlace válido.
        :returns: URL del archivo ZIP correspondiente al mes y año indicados.
        """
        if not (1 <= month <= 12):
            raise ValueError("El mes debe ser un número entre 1 y 12.")
        if year not in [21, 22, 23]:
            raise ValueError("El año debe ser 21, 22 o 23.")

        search_str = f"{year}_{month:02}"
        for url in self.enlaces_validos:
            if search_str in url:
                return url
        raise ValueError(f"No existe un enlace valido para el mes {month} del año {year}")

    def get_csv(self, month: int, year: int) -> TextIO:
        """
        Descarga un archivo ZIP desde una URL, extrae un archivo CSV del ZIP y lo devuelve como un flujo de texto
        (TextIO).

        :param month: Mes en formato numérico (1-12).
        :param year: Año en formato numérico (21, 22 o 23).
        :raises ConnectionError: Si falla la conexión a la URL.
        :returns: Objeto TextIO que contiene el contenido del archivo CSV.
        """
        url = self.get_url(month, year)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise ConnectionError(f"Failed to connect to {url}, status code: {resp.status_code}")

        zip_bytes = io.BytesIO(resp.content)
        zfile = zipfile.ZipFile(zip_bytes)

        name_csv = self.get_name_csv(month, year)
        with zfile.open(name_csv) as f:
            contents = f.read()
            content_str = contents.decode('utf-8')
            csv_stream = io.StringIO(content_str)

        return csv_stream

    @staticmethod
    def select_valid_urls() -> set[str]:
        """
        Selecciona las URLs válidas de la página de datos estáticos de EMT.

        :raises ConnectionError: Si falla la conexión a la página de datos generales.
        :returns: Lista de URLs válidas que contienen los archivos ZIP.
        """
        url = urljoin(UrlEMT.EMT, UrlEMT.GENERAL)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise ConnectionError(f"Failed to connect to {url}, status code: {resp.status_code}")

        links = UrlEMT.get_links(resp.text)
        return links

    @staticmethod
    def get_links(html: str) -> set[str]:
        """
        Extrae enlaces válidos de un contenido HTML.

        :param html: Cadena de texto que contiene el contenido HTML.
        :returns: Conjunto de enlaces completos de archivos ZIP.
        """
        # Patrón general para encontrar URLs de csv
        pattern = r'(getattachment/.*?trips_\d{2}_\d{2}_[a-zA-Z]+-csv\.aspx)'

        # Encontrar todas las coincidencias en el HTML
        matches = re.findall(pattern, html)
        return set(f"{UrlEMT.EMT}{link}" for link in matches)

    @staticmethod
    def get_name_csv(month: int, year: int) -> str:
        """
        Genera el nombre del archivo CSV según el mes y año proporcionados.

        :param month: Mes en formato numérico (1-12).
        :param year: Año en formato numérico (21, 22 o 23).
        :returns: Nombre del archivo CSV en formato de cadena.
        """
        month_name_mapping = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        month_name = month_name_mapping[month]
        csv_name = f"trips_{year}_{month:02}_{month_name}.csv"
        return csv_name


class BiciMad:
    """Clase para representar y analizar los datos de uso de BiciMad."""

    def __init__(self, month: int, year: int):
        self._month = month
        self._year = year
        self._data = BiciMad.get_data(month, year)
        self.clean()

    def __str__(self):
        """Devuelve una representación en cadena de la instancia de BiciMad."""
        return f"Month: {self._month}, Year: {self._year}"

    def clean(self) -> None:
        """
        Limpia el DataFrame eliminando filas con todos los valores NaN y
        formateando columnas específicas.
        """
        # Elimina las filas donde todos los valores son NaN
        self._data.dropna(how='all', inplace=True)

        col_names = ["fleet", "idBike", "station_lock", "station_unlock"]
        for col_name in col_names:
            if col_name in self._data.columns:
                self._data[col_name] = self._data[col_name].map(str).str.replace('.0', '', regex=False)

    def resume(self) -> pd.Series:
        """
        Resume los datos de BiciMad en una serie de estadísticas clave.

        :returns: Objeto pd.Series con estadísticas como año, mes, número total de usos, tiempo total, estación más
        popular y usos desde la estación más popular.
        """
        # Crear un objeto de tipo Series con las etiquetas especificadas
        series_data = pd.Series(index=[
            'year',
            'month',
            'total_uses',
            'total_time',
            'most_popular_station',
            'uses_from_most_popular'
        ], dtype=object)

        # Llenar la Series con los valores de las funciones
        series_data['year'] = self._year
        series_data['month'] = self._month
        series_data['total_uses'] = self._data.shape[0]
        series_data['total_time'] = self._data["trip_minutes"].sum() / 60.0
        series_data['most_popular_station'] = self.get_most_popular_stations()
        series_data['uses_from_most_popular'] = self.get_uses_from_most_populars()

        return series_data

    def get_most_popular_stations(self) -> set[str]:
        """
        Identifica las direcciones de las estaciones de desbloqueo más populares.

        :returns: Lista de direcciones de las estaciones de desbloqueo más populares.
        """
        df = self._data
        result = df.groupby('station_unlock').size().reset_index(name='count')

        max_count = result['count'].max()
        top = result[result['count'] == max_count]

        top_stations = top['station_unlock'].tolist()  # Convertir a lista
        filtered_df = df[df['station_unlock'].isin(top_stations)]

        address_unlock_top = set(filtered_df['address_unlock'])

        return address_unlock_top

    def get_uses_from_most_populars(self) -> int:
        """
        Calcula el número total de viajes desde las estaciones de desbloqueo más populares.

        :returns: Entero que representa el número total de viajes desde las estaciones más utilizadas.
        """
        df = self._data
        top_adresses = self.get_most_popular_stations()
        df_filtered = df[df['address_unlock'].isin(top_adresses)]
        return len(df_filtered)

    def day_time(self) -> pd.Series:
        '''
        Calcula el total de tiempo de viaje en horas para cada día.

        :returns: Serie de pandas con el total de horas de viaje por día, donde el índice es de tipo `DatetimeIndex`
        y el nombre de la columna es 'trip_hours'.
        '''
        data = self._data
        horas = data.groupby(data.index)['trip_minutes'].sum() / 60
        horas.index = pd.to_datetime(horas.index)
        horas = horas.rename("trip_hours")
        return horas

    def weekday_time(self) -> pd.Series:
        '''
        Calcula el total de tiempo de viaje en horas para cada día de la semana.

        :returns: Serie de pandas con el total de horas de viaje por cada día de la semana, donde el índice
        es el día en formato de abreviatura en español y el nombre de la columna es 'trip_hours'.
        '''
        data = self._data
        mapping = {'Monday': 'L', 'Tuesday': 'M', 'Wednesday': 'X', 'Thursday': 'J', 'Friday': 'V', 'Saturday': 'S',
                   'Sunday': 'D'}
        data['dia'] = data.index.day_name().map(lambda x: mapping[x])

        horas = data.groupby(data['dia'])['trip_minutes'].sum() / 60
        horas = horas.rename("trip_hours")
        return horas

    def total_usage_day(self) -> pd.Series:
        '''
        Calcula el total de usos de bicicletas para cada día.

        :returns: Serie de pandas con el número total de usos de bicicletas por día, donde el índice es de tipo
        `DatetimeIndex` y el nombre de la columna es 'Number_trips'.
        '''
        data = self._data
        num_usage = data.groupby(data.index.date)["idBike"].size()
        num_usage = num_usage.rename("Number_trips")
        num_usage.index = pd.to_datetime(num_usage.index)
        return num_usage

    def total_usage_day_station_unlock(self) -> pd.DataFrame:
        '''
        Calcula el número total de usos de bicicletas por día y por estación de desbloqueo.

        :returns: DataFrame con tres columnas:
            - 'index' que representa la fecha del día.
            - 'station_unlock' que indica la estación de desbloqueo.
            - 'count' que contiene el número total de usos de bicicletas para cada combinación de día y estación.
        '''
        df = self._data
        df = df.groupby([pd.Grouper(freq='D'), 'station_unlock']).size().reset_index(name='count')
        df.set_index('fecha', inplace=True)
        return df

    @property
    def data(self) -> pd.DataFrame:
        """Devuelve el DataFrame de datos de BiciMad."""
        return self._data

    @staticmethod
    def get_data(month: int, year: int) -> pd.DataFrame:
        """
        Obtiene y carga los datos de un archivo CSV en un DataFrame de pandas.

        :param month: Mes en formato numérico (1-12).
        :param year: Año en formato numérico (21, 22 o 23).
        :returns: DataFrame de pandas con los datos cargados.
        """
        url_emt_instance = UrlEMT()
        csv_file = url_emt_instance.get_csv(month, year)
        df = BiciMad.csv_to_df(csv_file)
        return df

    @staticmethod
    def csv_to_df(data: TextIO) -> pd.DataFrame:
        """
        Lee un archivo CSV desde un flujo de texto y lo convierte en un DataFrame.

        :param data: Objeto TextIO que contiene el contenido CSV, con delimitador de punto y coma (;).
        :returns: DataFrame de pandas con columnas seleccionadas.
        """
        df = pd.read_csv(data, delimiter=";", index_col="fecha", parse_dates=["fecha", "lock_date", "unlock_date"],
                         dayfirst=True)
        df.index = pd.to_datetime(df.index)

        df = df[['idBike', 'fleet', 'trip_minutes', 'geolocation_unlock', 'address_unlock', 'unlock_date', 'locktype',
                 'unlocktype', 'geolocation_lock', 'address_lock', 'lock_date', 'station_unlock', 'unlock_station_name',
                 'station_lock', 'lock_station_name']]

        return df
