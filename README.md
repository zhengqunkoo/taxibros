# TaxiBros
Instantly query taxi arrival times.

## Instructions
All the following instructions executed from same folder as this `README.md`.
Each instruction is a command, and a description of the command.

1. Install the `taxibros` module.
   ```
   python3 -m pip install --upgrade .
   ```
2. Make a data folder.
   ```
   mkdir -p data
   ```
3. Start downloading taxi locations forever.
   ```
   python3 -m geoinfo.download_json data
   ```
