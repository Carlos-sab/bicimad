import io
import re
import pytest
import requests
from pathlib import Path

from bicimad import UrlEMT

FIXTURE_DIR = Path(__file__).parent.resolve() / 'data'

FILES = pytest.mark.datafiles(
    FIXTURE_DIR / 'emt.html',
    FIXTURE_DIR / 'trips_22_11_November-csv.zip',
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
def data_html(files):
    """Fixture para leer el archivo HTML"""
    with open(files['emt.html']) as f:
            return f.read()

@pytest.fixture
def data_zip(files):
    """Fixture para leer el archivo ZIP"""
    with open(files['trips_22_11_November-csv.zip'], 'rb') as f:
            return f.read()

#Fixtures para mocks de requests
@pytest.fixture
def mock_get_valid_html(monkeypatch, data_html):
    """Fixture para mockear requests.get con una respuesta válida de HTML"""
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = data_html.encode('utf-8')

    monkeypatch.setattr(requests, 'get', lambda url: mock_response)

    return mock_response

@pytest.fixture
def mock_get_valid_zip(monkeypatch, data_zip):
    """Fixture para mockear requests.get con una respuesta válida de ZIP"""
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = data_zip

    monkeypatch.setattr(requests, 'get', lambda url: mock_response)

    return mock_response

@pytest.fixture
def mock_get_error(monkeypatch):
    """Fixture para mockear requests.get con una respuesta de error"""
    mock_response = requests.Response()
    mock_response.status_code = 404
    mock_response._content = None

    monkeypatch.setattr(requests, 'get', lambda url: mock_response)
    return mock_response

# Fixture para la instancia de UrlEMT
@pytest.fixture
def url_emt_instance(monkeypatch):
    """Fixture que crea una instancia de UrlEMT con un mock de enlaces válidos"""
    monkeypatch.setattr(UrlEMT, 'select_valid_urls', lambda: [
        "https://opendata.emtmadrid.es/getattachment/45f51cef-9296-4afe-b42e-d8d5bca3c548/"
        "trips_22_11_November-csv.aspx",
        'https://opendata.emtmadrid.es/51ba4be6-596f-41d3-8bab-634c4be569c5/trips_21_10_October-csv.aspx',
        "https://opendata.emtmadrid.es/getattachment/trips_22_03_march-csv.aspx",
    ])

    return UrlEMT()

# Tests del metodo 'UrlEMT.get_url'
@pytest.mark.parametrize("month, year, expected_url", [
    (11, 22, "https://opendata.emtmadrid.es/getattachment/45f51cef-9296-4afe-b42e-d8d5bca3c548/"
             "trips_22_11_November-csv.aspx"),
    (10, 21, 'https://opendata.emtmadrid.es/51ba4be6-596f-41d3-8bab-634c4be569c5/trips_21_10_October-csv.aspx'),
    (3, 22, "https://opendata.emtmadrid.es/getattachment/trips_22_03_march-csv.aspx"),
])
def test_get_url_valid_cases(url_emt_instance, month, year, expected_url):
    """Prueba que get_url devuelva la URL correcta para casos válidos."""
    assert url_emt_instance.get_url(month, year) == expected_url

@pytest.mark.parametrize("month, year", [
    (0, 23),  # Mes fuera de rango
    (13, 23),  # Mes fuera de rango
    (1, 20),  # Año no válido
    (1, 24),  # Año no válido
])
def test_get_url_invalid_cases(url_emt_instance, month, year):
    """Prueba que get_url levante ValueError para casos no válidos."""
    with pytest.raises(ValueError):
        url_emt_instance.get_url(month, year)

@pytest.mark.parametrize("month, year, expected_error", [
    (4, 23, "No existe un enlace valido para el mes 4 del año 23"),
    (9, 23, "No existe un enlace valido para el mes 9 del año 23"),
    (12, 22, "No existe un enlace valido para el mes 12 del año 22"),
])
def test_get_url_no_valid_link_found(url_emt_instance, month, year, expected_error):
    """Prueba que get_url levante ValueError si no encuentra un enlace válido."""
    with pytest.raises(ValueError, match=expected_error):
        url_emt_instance.get_url(month, year)

@pytest.mark.parametrize(
    "expected_urls", [
        {
            'https://opendata.emtmadrid.es/getattachment/45f51cef-9296-4afe-b42e-d8d5bca3c548/'
            'trips_22_11_November-csv.aspx',
            'https://opendata.emtmadrid.es/getattachment/trips_22_03_march-csv.aspx',
            'https://opendata.emtmadrid.es/getattachment/51ba4be6-596f-41d3-8bab-634c4be569c5/'
            'trips_21_10_October-csv.aspx'
        }
    ]
)
@FILES
def test_select_valid_urls(mock_get_valid_html, data_html, expected_urls):
    """Prueba que select_valid_urls devuelva los enlaces correctos"""
    result = UrlEMT.select_valid_urls()
    assert result == expected_urls

def test_select_valid_urls_connection_error(mock_get_error):
    """Prueba que select_valid_urls maneje errores de conexión correctamente"""
    with pytest.raises(ConnectionError, match=re.escape(r"Failed to connect to https://opendata.emtmadrid.es/"
                                                        r"Datos-estaticos/Datos-generales-(1), status code: 404")):
        UrlEMT.select_valid_urls()

# Tests del metodo 'UrlEMT.get_lins'
@pytest.mark.parametrize(
    "expected_links", [
        {
            'https://opendata.emtmadrid.es/getattachment/45f51cef-9296-4afe-b42e-d8d5bca3c548/'
            'trips_22_11_November-csv.aspx',
            'https://opendata.emtmadrid.es/getattachment/trips_22_03_march-csv.aspx',
            'https://opendata.emtmadrid.es/getattachment/51ba4be6-596f-41d3-8bab-634c4be569c5/'
            'trips_21_10_October-csv.aspx'
        }
    ]
)
@FILES
def test_get_links(data_html, expected_links):
    """Prueba que get_links extraiga los enlaces correctos"""
    result = UrlEMT.get_links(data_html)
    assert result == expected_links

#Test del metodo 'UrlEMT.get_name_csv'
@pytest.mark.parametrize(
    "month, year, expected_names", [
        (1, 21, "trips_21_01_January.csv"),
        (9, 25, "trips_25_09_September.csv"),
        (10, 22, "trips_22_10_October.csv"),
        (12, 23, "trips_23_12_December.csv")
    ]
)
def test_get_name_csv(month, year, expected_names):
    """Prueba que get_name_csv genere los nombres de archivo correctos"""
    result = UrlEMT.get_name_csv(month, year)
    assert result == expected_names

#Test del metodo 'UrlEMT.get_csv'
@pytest.mark.parametrize(
    "month, year, expected_error", [
        (11, 22, "Failed to connect to https://opendata.emtmadrid.es/getattachment/"
                 "45f51cef-9296-4afe-b42e-d8d5bca3c548/trips_22_11_November-csv.aspx, status code: 404"),
    ]
)
def test_get_csv_invalid_url(url_emt_instance, mock_get_error, month, year, expected_error):
    """Prueba que get_csv maneje errores de conexión correctamente"""
    with pytest.raises(ConnectionError, match=re.escape(expected_error)):
        url_emt_instance.get_csv(month, year)

@pytest.mark.parametrize(
    "month, year, expected_headers", [
        (11, 22, [
        "fecha", "idBike", "fleet", "trip_minutes", "geolocation_unlock", "address_unlock",
        "unlock_date", "locktype", "unlocktype", "geolocation_lock", "address_lock", "lock_date",
        "station_unlock", "dock_unlock", "unlock_station_name", "station_lock", "dock_lock", "lock_station_name"
        ]
         )
    ]
)
@FILES
def test_get_csv_valid_url(url_emt_instance, mock_get_valid_zip, month, year, expected_headers):
    """Prueba que get_csv procese correctamente un archivo ZIP con los encabezados correctos"""
    result = url_emt_instance.get_csv(month, year)

    # Verifica que el resultado es una instancia de StringIO
    assert isinstance(result, io.StringIO)

    # Obtener los encabezados del CSV
    headers = result.readline().strip().split(';')

    # Verifica que las columnas del CSV coinciden con los títulos esperados
    assert headers == expected_headers, f"Headers do not match. Expected: {expected_headers}, but got: {headers}"

