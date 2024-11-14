# BiciMad - Bicycle Usage Analysis

`BiciMad` is a class designed to analyze the usage of shared bicycles in the city of Madrid. This class allows querying various statistics about bicycle usage based on historical data, providing information such as total usage hours per day, usage hours by day of the week, and the number of trips.

## Data Description
The `BiciMad` class uses a historical dataset containing information about trips made in Madrid's shared bicycle system. Each record includes:
* **date** (Date): The date when the trip took place.

* **idbike** (Bike ID): The unique identifier of the bike used for the trip.

* **fleet** (Fleet): The fleet to which the bike belongs.

* **trip_minutes** (Trip Duration in Minutes): The duration of the trip in minutes.

* **geolocation_unlock** (Unlock Geolocation): The geographic coordinates of the starting point of the trip.

* **address_unlock** (Unlock Address): The postal address where the bike was unlocked.

* **unlock_date** (Unlock Date and Time): The exact date and time when the trip began.

* **locktype** (Lock Type): The status of the bike before the trip. It can be docked at a station or freely locked at any location.

* **unlocktype** (Unlock Type): The status of the bike after the trip.

* **geolocation_lock** (Lock Geolocation): The geographic coordinates of the end point of the trip.

* **address_lock** (Lock Address): The postal address where the bike was locked.

* **lock_date** (Lock Date and Time): The exact date and time when the trip ended.

* **station_unlock** (Unlock Station Number): The station number where the bike was docked before the trip, if applicable.

* **dock_unlock** (Unlock Dock): The dock at the station where the bike was docked before the trip, if applicable.

* **unlock_station_name** (Unlock Station Name): The name of the station where the bike was docked before the trip, if applicable.

* **station_lock** (Lock Station Number): The station number where the bike was docked after the trip, if applicable.

* **dock_lock** (Lock Dock): The dock at the station where the bike was docked after the trip, if applicable.

* **lock_station_name** (Lock Station Name): The name of the station where the bike was docked after the trip, if applicable.

Processing this data enables detailed statistical insights into bicycle usage.

## Project Structure

The package `bicimad` contains two main classes:

### 1. BiciMad

This class handles the download and processing of CSV files. Some of its key functionalities include:

- Automatic data download.
- Processing and cleaning of downloaded data.
- Extraction of essential information such as dates, bicycle identifiers, trip durations, and start/end locations of the trips.

### 2. UrlEMT

This class is responsible for managing URLs and other configuration aspects necessary for data downloads.


## Installation

To install and use this package, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/bicimad-analysis.git
   ```

2. **Navigate to the project directory**:
   ```bash
   cd bicimad-analysis
   ```

3. **Install the required dependencies**:
   Make sure you have Python installed. Then, run the following command to install all necessary packages:
   ```bash
   pip install -r requirements.txt
   ```

## Class Usage

### Initialization
Create an instance of the `BiciMad` class by providing the required parameters:

```python
from bicimad import BiciMad

# Create an instance of BiciMad with desired parameters
bicimad_inst = BiciMad(2, 23)
```

### Use Cases

1. **Total Bicycle Usage Hours per Day of the Month**

   This method returns the total usage hours of bicycles for each day of a specified month.

   ```python
   horas_uso = bicimad_inst.day_time()
   print(horas_uso)
   ```
   **Example Output:**
   ```
   date
   2023-02-01    4160.538500
   2023-02-02    3435.122333
   2023-02-03    3456.311667
   ...
   ```

2. **Total Bicycle Usage Hours by Day of the Week**

   This method provides the average bicycle usage hours for each day of the week (Monday to Sunday).

   ```python
   usos_semanal = bicimad_inst.weekday_time()
   print(usos_semanal)
   ```
   **Example Output:**
   ```
   day
   M     6494.488500
   T     5626.440667
   W    10349.659667
   Th    9412.645333
   F     8958.274000
   Sa    6781.029667
   Su    6267.562167
   ```

3. **Total Number of Bicycle Trips per Day of the Month**

   This method returns the total number of trips made each day of the month.

   ```python
   num_usos = bicimad_inst.day_trip_count()
   print(num_usos)
   ```
   **Example Output:**
   ```
   date
   2023-02-01    11442
   2023-02-02    11069
   2023-02-03    10166
   ...
   ```

4. **Total Number of Bicycle Trips by Day of the Week**

   Returns the average number of trips made for each day of the week.

   ```python
   num_usos_semanal = bicimad_inst.weekday_trip_count()
   print(num_usos_semanal)
   ```
   **Example Output:**
   ```
   day
   M    16789
   T    15823
   W    17456
   Th   17234
   F    19045
   Sa   12034
   Su   10345
   ```

5. **Average Trip Duration per Day of the Month**

   This method calculates the average duration of trips for each day.

   ```python
   duracion_promedio = bicimad_inst.average_trip_duration_per_day()
   print(duracion_promedio)
   ```
   **Example Output:**
   ```
   date
   2023-02-01    35.4
   2023-02-02    33.7
   ...
   ```

6. **Average Trip Duration by Day of the Week**

   Shows the average duration of trips for each day of the week.

   ```python
   duracion_promedio_semanal = bicimad_inst.average_trip_duration_per_weekday()
   print(duracion_promedio_semanal)
   ```
   **Example Output:**
   ```
   day
   M    37.2
   T    35.1
   W    38.5
   Th   36.8
   F    40.0
   Sa   25.7
   Su   28.4
   ```

## Testing Features
To verify the correct functionality of the `BiciMad` class, sample data and examples are provided to test each method and validate the results. 

To run the unit tests for this package, you need to have the pytest library installed. Once installed, navigate to the project root directory and run the following command:

```bash
pytest
```
This will execute the test cases defined in `test_BiciMad.py` and `test_UrlEMT.py`.

## License
This project is licensed under the MIT License. For more details, refer to the `LICENSE` file.

