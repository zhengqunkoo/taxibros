"""
Features lacking in `django-dotenv`.
Copy functions from `python-dotenv` into this file.
Could have installed `python-dotenv`, but then `dotenv` namespace will clash.
"""

import codecs
import fileinput
import io
import os

__escape_decoder = codecs.getdecoder("unicode_escape")


def decode_escaped(escaped):
    return __escape_decoder(escaped)[0]


def parse_line(line):
    line = line.strip()

    # Ignore lines with `#` or which doesn't have `=` in it.
    if not line or line.startswith("#") or "=" not in line:
        return None, None

    k, v = line.split("=", 1)

    if k.startswith("export "):
        k = k.lstrip("export ")

    # Remove any leading and trailing spaces in key, value
    k, v = k.strip(), v.strip()

    if v:
        v = v.encode("unicode-escape").decode("ascii")
        quoted = v[0] == v[-1] in ['"', "'"]
        if quoted:
            v = decode_escaped(v[1:-1])

    return k, v


def set_key(dotenv_path, key_to_set, value_to_set, quote_mode="always"):
    """
    Adds or Updates a key/value to the given .env

    If the .env path given doesn't exist, fails instead of risking creating
    an orphan .env somewhere in the filesystem
    """
    value_to_set = value_to_set.strip("'").strip('"')
    if not os.path.exists(dotenv_path):
        warnings.warn("can't write to %s - it doesn't exist." % dotenv_path)
        return None, key_to_set, value_to_set

    if " " in value_to_set:
        quote_mode = "always"

    line_template = '{}="{}"' if quote_mode == "always" else "{}={}"
    line_out = line_template.format(key_to_set, value_to_set)

    replaced = False
    for line in fileinput.input(dotenv_path, inplace=True):
        k, v = parse_line(line)
        if k == key_to_set:
            replaced = True
            line = line_out
        print(line, end="")

    if not replaced:
        with io.open(dotenv_path, "a") as f:
            f.write("{}\n".format(line_out))

    return True, key_to_set, value_to_set
