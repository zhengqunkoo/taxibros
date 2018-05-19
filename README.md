# TaxiBros
Instantly query taxi arrival times.

## Running django server
All the following instructions executed from same folder as this `README.md`.
Each instruction is a command, and a description of the command.
1. Follow `.env.template` to store all secret keys in a file named `.env`.
<<<<<<< HEAD
   Get your `DJANGO_SECRET_KEY` by running this command:
   ```
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. `python3 manage.py runserver`

## Installing package
1. Install the `taxibros` module.
=======
   Get your `DJANGO_SECRET_KEY` by:
   ```
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. Migrate, as well as synchronize apps without migrations.
   ```
   python3 manage.py makemigrations
   python3 manage.py migrate --run-syncdb
   ```
2. Run server.
   ```
   python3 manage.py runserver`
   ```

## Accessing admin pages
1. Create account.
>>>>>>> cf43a0d65c561ed1663197006341e6cfa8475aab
   ```
   python3 manage.py createsuperuser
   ```
<<<<<<< HEAD

## Dowloading data
1. Make a data folder.
=======
2. Log in at `/admin`.

## Downloading data
1. Run the server (see `Running django server` section).
2. Visit `/daemons` to start a daemon. **Do this only once, else you have multiple daemons.**
   - Daemons are scheduled to run at some time.
   - Daemons persist in the database after server restart.
   - If you run this command:
     ```
     python3 manage.py process_tasks --queue taxi-availability
     ```
     * If current time exceeds a daemon's scheduled time, it will run.
     * Then they are replaced by a new daemon scheduled in the future.
3. Check `logs/debug.log` for debug output. For example:
   ```
   INFO 2018-05-17 12:26:54,905 tasks 8245 140658619733760 Running daemons.download.start_download
   DEBUG 2018-05-17 12:26:54,906 download 8245 140658619733760 start_download
   DEBUG 2018-05-17 12:26:55,219 download 8245 140658619733760 2018-05-17T12:26:46+08:00 4950 healthy
   INFO 2018-05-17 12:26:56,828 tasks 8245 140658619733760 Ran task and deleting daemons.download.start_download

   DEBUG 2018-05-17 12:26:58,045 process_tasks 8245 140658619733760 waiting for tasks
   ...
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

[install PROJ.4 datum shifting files]: https://docs.djangoproject.com/en/2.0/ref/contrib/gis/install/geolibs/#proj4
