import os


def get_width() -> int:
    _, columns = os.popen("stty size", "r").read().split()
    return int(columns)
