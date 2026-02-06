from . import globalvars


def info(message: str) -> None:
    print("==> " + message)


def info_weak(message: str) -> None:
    print("  -> " + message)


def warning(message: str) -> None:
    print("==> WARNING: " + message)


def error(message: str) -> None:
    print("==> ERROR: " + message)


def command(command: str) -> None:
    print("--> " + command)


def debug(message: str) -> None:
    if globalvars.DEBUG:
        print("==> DEBUG: " + message)
