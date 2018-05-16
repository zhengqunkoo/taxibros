# TaxiBros
Instantly query taxi arrival times.

## Running django server
All the following instructions executed from same folder as this `README.md`.
Each instruction is a command, and a description of the command.
1. Follow `.env.template` to store all secret keys in a file named `.env`.
   Get your `DJANGO_SECRET_KEY` by running this command:
   ```
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. `python3 manage.py runserver`

## Installing package
1. Install the `taxibros` module.
   ```
   python3 -m pip install --upgrade .
   ```

## Dowloading data
1. Make a data folder.
   ```
   mkdir -p data
   ```
2. Download taxi locations forever.
   ```
   python3 -m taxibros.download_json data
   ```
