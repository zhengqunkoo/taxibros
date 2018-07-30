# TaxiBros
![Build Status][travis badge]
![Coverage Status][coverage badge]
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Instantly query taxi arrival times.

## Installing and running django server
All the following instructions executed from same folder as this `README.md`.
Each instruction is a command, and a description of the command.
1. Install the `taxibros` package.
   ```
   python3 -m pip install --upgrade .
   ```
2. Follow `.env.template` to store all secret keys in a file named `.env`.
   Get your `DJANGO_SECRET_KEY` by:
   ```
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Follow `taxibros/settings/local_settings.py.template` to create your personal
   settings in `taxibros/settings/local_settings.py`.
4. Migrate, as well as synchronize apps without migrations.
   ```
   python3 manage.py makemigrations
   python3 manage.py migrate --run-syncdb
   ```
5. Run server.
   ```
   python3 manage.py runserver`
   ```

## Accessing admin pages
1. Create account.
   ```
   python3 manage.py createsuperuser
   ```
2. Log in at `/admin`.

## Downloading data
1. Run the server (see `Running django server` section).
2. Visit `/daemons` to check number of coordinates and timestamp, or `/admin` and select background_tasks to check if daemon is running
3. Check `logs/debug.log` for debug output. For example:
   ```
   INFO 2018-05-17 12:26:54,905 tasks 8245 140658619733760 Running daemons.download.start_download
   DEBUG 2018-05-17 12:26:54,906 download 8245 140658619733760 start_download
   DEBUG 2018-05-17 12:26:55,219 download 8245 140658619733760 2018-05-17T12:26:46+08:00 4950 healthy
   INFO 2018-05-17 12:26:56,828 tasks 8245 140658619733760 Ran task and deleting daemons.download.start_download

   DEBUG 2018-05-17 12:26:58,045 process_tasks 8245 140658619733760 waiting for tasks
   ...
   ```
* When the `download_timestamps` function is called, there are some
  changes to the database. These changes are removed if a `SIGINT` by `C-C`
  is sent before `download_timestamps` finishes.
* If some background_task/task had error, and fixing the cause of error then
  restarting the server does not fix the issue, then delete task from database.

## Running Tests
Tests are executed using the django manager.
1. Run the test client
   ```
   python3 manage.py test
   ```

## Creating PostGIS database
1. Download dependencies.
   ```
   sudo apt install postgresql-server-dev-9.5 postgresql-9.5-postgis-2.3
   ```
2. Create user and database.
   ```
   sudo -u postgres -i
   psql
   CREATE USER geodjango PASSWORD 'geodjango';
   ALTER ROLE geodjango SUPERUSER;
   CREATE DATABASE geodjango OWNER geodjango;
   exit
   ```

## Installing Open Street Map
1. For more context in map (including street and thoroughfare details), [install PROJ.4 datum shifting files].

## Continuous integration
Automatic CI on each new commit with `.travis.yml` in the repo.
However, sometimes build errors occur (specifically `test_unique_timestamp` fails),
even though it passes on your local machine.
Assuming your `local_settings.py` matches travis' settings in `production.py`,
restart build on Travis CI and pray.

## Coverage testing
1. Generate `.coverage` file.
   ```
   coverage run manage.py test
   ```
2. Optional: show report.
   ```
   coverage report -m
   ```
3. Generate coverage badge. You might have to alias
   `python3 .../path/to/coverage_badge/__main__.py` to `coverage-badge`.
   ```
   coverage-badge -o coverage.svg
   ```

## Code formatting
1. Run with sensible defaults.
   ```
   black .
   ```

## Cache framework
1. Install `memcached` and dev tools.
   ```
   sudo apt install -y memcached libmemcached-dev
   ```
2. Follow guide on [django cache docs].

## Mouse tracking
We use [musjs].
1. Create new mouse database by `python manage.py migrate --database=mouse_db`.
2. Play tracked mouse movements at `/mouse`.

[travis badge]: https://travis-ci.com/zhengqunkoo/taxibros.svg?token=zQpqs1cgYrwMmHCBfnPg&branch=master "From travis-ci."
[coverage badge]: https://github.com/zhengqunkoo/taxibros/raw/master/coverage.svg?sanitize=True "Generated using coverage-badge."
[install PROJ.4 datum shifting files]: https://docs.djangoproject.com/en/2.0/ref/contrib/gis/install/geolibs/#proj4
[django cache docs]: https://docs.djangoproject.com/en/2.0/topics/cache/
[musjs]: https://github.com/ineventapp/musjs
