import json
from typing import List


def shorten(name, to=18):
    return name if len(name) < to else name[:(to-1)] + "..."


def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Perceived brightness formula
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 128 else "white"


def blend_colors(color1, color2, t):
    c1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    c2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


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


def detect_string(search_line: str, search_strings: List[str], replace: str = "_") -> int:
    """Search a line for a string and return the offset at the end of the string."""
    # Extend search strings with modified versions (replacing 'replace' character)
    modified_strings = search_strings + [
        string.replace(replace, "") for string in search_strings
    ]
    # Find the first matching string and return its offset
    for string in modified_strings:
        if string in search_line:
            return search_line.find(string) + len(string)
    return None
