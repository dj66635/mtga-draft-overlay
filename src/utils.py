import json
from typing import List


def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Perceived brightness formula
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 128 else "white"


def process_json(obj):
    """
    Convert JSON string with escape characters to a nested dictionary
    """
    if isinstance(obj, dict):
        return {key: process_json(value) for key, value in obj.items()}
    elif isinstance(obj, str):
        try:
            parsed_json = json.loads(obj)
            return process_json(parsed_json)
        except json.JSONDecodeError:
            return obj
    else:
        return obj


def json_find(key, obj):
    """
    Retrieve a value from a nested dictionary using a specified key.
    """
    result = None
    if isinstance(obj, dict):
        if key in obj:
            result = obj[key]
        else:
            for value in obj.values():
                result = json_find(key, value)
                if result is not None:
                    break
    return result



def detect_string(
    search_line: str, search_strings: List[str], replace: str = "_"
) -> int:
    """Search a line for a string and return the offset at the end of the string."""
    # Extend search strings with modified versions (replacing 'replace' character)
    modified_strings = search_strings + [
        string.replace(replace, "") for string in search_strings
    ]
    # Find the first matching string and return its offset
    for string in modified_strings:
        if string in search_line:
            return search_line.find(string) + len(string)
    # Return -1 if no match is found
    return -1



def clean_string(input_string: str, uppercase: bool = True) -> str:
    """Cleans a string by removing unwanted characters"""
    unwanted_chars = [" ", ".", "/", "_"]
    for char in unwanted_chars:
        input_string = input_string.replace(char, "")
    return input_string.upper() if uppercase else input_string
