# TaxiBros
Instantly query taxi arrival times.

## Running django server
All the following instructions executed from same folder as this `README.md`.
Each instruction is a command, and a description of the command.
1. Follow `.env.template` to store all secret keys in a file named `.env`.
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
   ```
   python3 manage.py createsuperuser
   ```
2. Log in at `/admin`.

## Downloading data
1. Run the server (see `Running django server` section).
2. Download taxi locations forever.
   ```
   python3 manage.py process_tasks
   ```
3. Check `logs/debug.log` for debug output. For example:
   ```
   INFO 2018-05-17 12:26:54,905 tasks 8245 140658619733760 Running daemons.download.start_download
   DEBUG 2018-05-17 12:26:54,906 download 8245 140658619733760 start_download
   DEBUG 2018-05-17 12:26:55,219 download 8245 140658619733760 2018-05-17T12:26:46+08:00 4950 healthy
   INFO 2018-05-17 12:26:56,828 tasks 8245 140658619733760 Ran task and deleting daemons.download.start_download

   DEBUG 2018-05-17 12:26:58,045 process_tasks 8245 140658619733760 waiting for tasks
   ...
   DEBUG 2018-05-17 12:27:48,140 process_tasks 8245 140658619733760 waiting for tasks

   DEBUG 2018-05-17 12:27:53,932 download 8681 139710976792320 daemons.download
   INFO 2018-05-17 12:27:53,948 tasks 8681 139710976792320 Running daemons.download.start_download
   DEBUG 2018-05-17 12:27:53,948 download 8681 139710976792320 start_download
   DEBUG 2018-05-17 12:27:54,256 download 8681 139710976792320 2018-05-17T12:26:46+08:00 4950 healthy
   INFO 2018-05-17 12:27:55,522 tasks 8681 139710976792320 Ran task and deleting daemons.download.start_download
   ```
