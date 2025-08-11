# foodops/ui/console_style.py
def bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def cyan(text: str) -> str:
    return f"\033[96m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"
