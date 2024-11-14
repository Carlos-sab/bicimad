import io
import pytest
from pathlib import Path
import pandas as pd

from bicimad import BiciMad, UrlEMT

FIXTURE_DIR = Path(__file__).parent.resolve() / 'data'

FILES = pytest.mark.datafiles(
    FIXTURE_DIR / 'trips_22_11_November.csv',
    FIXTURE_DIR / 'dataframe.txt',
)


# Fixtures relacionadas con los archivos
@pytest.fixture
def files(datafiles):
    """Fixture para cargar los archivos desde datafiles"""
    d = dict()
    for fname in datafiles.iterdir():
        d[fname.name] = fname.as_posix()
    return d

@pytest.fixture
def data_csv(files):
    """Fixture para leer el archivo csv"""
    with open(files['trips_22_11_November.csv']) as f:
            return io.StringIO(f.read())

@pytest.fixture
def expected_result_df(files):
    """Fixture de el dataframe de salida esperado"""
    with open(files['dataframe.txt']) as f:
            return pd.read_csv(f, sep=';', index_col=0, parse_dates=["fecha", "lock_date", "unlock_date"])

# Fixture para la instancia de UrlEMT
@pytest.fixture
def url_emt_instance(monkeypatch, data_csv):
    """Fixture que crea una instancia de UrlEMT con un mock de enlaces válidos"""
    monkeypatch.setattr(UrlEMT, 'select_valid_urls', lambda: None)
    monkeypatch.setattr(UrlEMT, 'get_csv', lambda self, month, year: data_csv)
    return UrlEMT()

#Tests del metodo 'BiciMad.get_data'
@FILES
def test_get_data(url_emt_instance, expected_result_df):
    """
    Testea el metodo 'get_data' de la clase BiciMad. Verifica que la salida sea un DataFrame de pandas
    y que coincida con el DataFrame esperado.
    """
    result = BiciMad.get_data(11, 22)
    assert isinstance(result, pd.DataFrame)
    assert result.equals(expected_result_df)

#Tests del metodo 'BiciMad.csv_to_df'
@FILES
def test_csv_to_df(data_csv, expected_result_df):
    """
    Testea el metodo 'csv_to_df' de la clase BiciMad. Comprueba que convierte correctamente un archivo CSV
    en un DataFrame de pandas y que este sea igual al DataFrame esperado.
    """
    result = BiciMad.csv_to_df(data_csv)
    assert isinstance(result, pd.DataFrame)
    assert result.equals(expected_result_df)

#Tests del metodo 'BiciMad.data'
@FILES
def test_data(url_emt_instance):
    """
    Testea la propiedad 'data' de la clase BiciMad. Verifica que el valor de 'data' sea igual a '_data'
    dentro de la instancia de BiciMad.
    """
    bicimad_inst = BiciMad(11,22)
    result = bicimad_inst.data
    assert result.equals(bicimad_inst._data)

#Test del metodo 'BiciMad.get_most_popular_stations
@FILES
def test_get_most_popular_stations(url_emt_instance):
    """
    Testea el metodo 'get_most_popular_stations' de la clase BiciMad. Verifica que devuelva las estaciones
    más populares correctamente.
    """
    bicimad_inst = BiciMad(11,22)
    result = bicimad_inst.get_most_popular_stations()
    assert result == {'Calle Manuel Silvela', 'Calle Alcala'}

#Test del metodo 'BiciMad.get_uses_from_most_populars'
@FILES
def test_get_uses_from_most_populars(url_emt_instance):
    """
    Testea el metodo 'get_uses_from_most_populars' de la clase BiciMad. Verifica que devuelva el número
    correcto de usos de las estaciones más populares.
    """
    bicimad_inst = BiciMad(11,22)
    result = bicimad_inst.get_uses_from_most_populars()
    assert result == 4

#Test del metodo 'BiciMad.resume'
@FILES
def test_resume(url_emt_instance):
    """
    Testea el metodo 'resume' de la clase BiciMad. Verifica que la salida sea un objeto pd.Series con los datos
    esperados para el resumen del mes y año indicados.
    """
    bicimad_inst = BiciMad(11,22)

    expected_output_data = {
        'year': 22,
        'month': 11,
        'total_uses': 6,
        'total_time': '0.708333333333333',
        'most_popular_station': {'Calle Manuel Silvela', 'Calle Alcala'},
        'uses_from_most_popular': 4
    }
    expected_output_series = pd.Series(expected_output_data, dtype=object)

    result = bicimad_inst.resume()
    assert isinstance(result, pd.Series)

    for field in expected_output_series.index:
        if field == 'total_time':
            assert round(float(result[field]), 4) == round(float(expected_output_series[field]), 4), \
                f"El campo '{field}' no coincide después de redondear: {result[field]} vs {expected_output_series[field]}"
        else:
            assert result[field] == expected_output_series[field], \
                f"El campo '{field}' no coincide: {result[field]} vs {expected_output_series[field]}"

#Test del metodo 'BiciMad.clean'
@FILES
def test_clean(url_emt_instance):
    """
    Testea el metodo 'clean' de la clase BiciMad. Verifica que las filas con valores NaN sean eliminadas y
    que las columnas relevantes estén formateadas correctamente.
    """
    bicimad_inst = BiciMad(11,22)

    # Verifica que las filas con todos los valores NaN han sido eliminadas
    assert not bicimad_inst._data.isnull().all(
        axis=1).any()

    # Verifica que las columnas relevantes se hayan formateado correctamente
    for col_name in ["fleet", "idBike", "station_lock", "station_unlock"]:
        if col_name in bicimad_inst._data.columns:
            # Asegúrate de que las columnas ya no contienen '.0' al final
            assert not bicimad_inst._data[col_name].str.endswith(
                '.0').any()

#Test del metodo 'BiciMad.day_time'
@FILES
def test_day_time(url_emt_instance):
    """
    Testea el metodo 'day_time' de la clase BiciMad. Verifica que la salida sea una serie de pandas con
    las horas de viaje por día, y que coincida con el valor esperado.
    """
    bicimad_inst = BiciMad(11, 22)

    expected_output_data = {
        '01/11/2022': 0.7,
        '02/11/2022': 0.00833333333333333,
    }
    expected_output_series = pd.Series(expected_output_data, dtype=float).rename("trip_hours")
    expected_output_series.index = pd.to_datetime(expected_output_series.index, format='%d/%m/%Y')

    result = bicimad_inst.day_time()

    result_rounded = result.round(5)
    expected_output_series_rounded = expected_output_series.round(5)
    print(result)
    assert isinstance(result, pd.Series)
    assert result_rounded.equals(expected_output_series_rounded)

#Test del metodo 'BiciMad.weekday_time'
@FILES
def test_weekday_time(url_emt_instance):
    """
    Testea el metodo 'weekday_time' de la clase BiciMad. Verifica que devuelva correctamente las horas de
    viaje por día de la semana.
    """
    bicimad_inst = BiciMad(11, 22)

    expected_output_data = {
        'M': 0.7,
        'X': 0.00833333333333333,
    }
    expected_output_series = pd.Series(expected_output_data, dtype=float).rename("trip_hours")
    expected_output_series.index.name = 'dia'

    result = bicimad_inst.weekday_time()

    result_rounded = result.round(5)
    expected_output_series_rounded = expected_output_series.round(5)

    assert isinstance(result, pd.Series)
    assert result_rounded.equals(expected_output_series_rounded)

#Test del metodo 'BiciMad.total_usage_day'
@FILES
def test_total_usage_day(url_emt_instance):
    """
    Testea el metodo 'total_usage_day' de la clase BiciMad. Verifica que devuelva correctamente el número
    total de viajes por día.
    """
    bicimad_inst = BiciMad(11, 22)

    expected_output_data = {
        '01/11/2022': 5,
        '02/11/2022': 1,
    }
    expected_output_series = pd.Series(expected_output_data).rename("Number_trips")
    expected_output_series.index = pd.to_datetime(expected_output_series.index, format='%d/%m/%Y')

    result = bicimad_inst.total_usage_day()

    assert isinstance(result, pd.Series)
    assert result.equals(expected_output_series)

#Test del metodo 'BiciMad.total_usage_day_station_unlock'
@FILES
def test_total_usage_day_station_unlock(url_emt_instance):
    """
    Testea el metodo 'total_usage_day_station_unlock' de la clase BiciMad. Verifica que devuelva el número
    de viajes por día y estación de desbloqueo correctamente.
    """
    bicimad_inst = BiciMad(11, 22)

    expected_data = {
        'index': ['01/11/2022', '01/11/2022', '01/11/2022', '01/11/2022', '02/11/2022'],
        'station_unlock': ['2', '1', '3', '4', '3'],
        'count': [1, 2, 1, 1, 1]
    }
    expected_output = pd.DataFrame(expected_data)
    expected_output.set_index('index', inplace=True)
    expected_output.index.name = 'fecha'
    expected_output.index = pd.to_datetime(expected_output.index, format='%d/%m/%Y')
    expected_output['station_unlock'] = expected_output['station_unlock'].astype(object)

    result = bicimad_inst.total_usage_day_station_unlock()

    assert isinstance(result, pd.DataFrame)

    for idx, row in expected_output.iterrows():
        # Filtrar el dataframe resultante por el índice y station_unlock
        result_row = result[(result.index == idx) & (result['station_unlock'] == row['station_unlock'])]

        # Comparar los valores de count
        assert result_row['count'].iloc[0] == row['count'], (
            f"Para la fecha {idx} y estación {row['station_unlock']}, los valores de 'count' no coinciden."
        )

#Test del metodo 'BiciMad.__str__'
@FILES
def test_str(url_emt_instance):
    """
    Testea el metodo '__str__' de la clase BiciMad. Verifica que la cadena resultante es correcta.
    """
    bicimad_inst = BiciMad(11, 22)
    assert str(bicimad_inst) == "Month: 11, Year: 22"






