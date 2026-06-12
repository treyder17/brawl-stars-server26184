"""
utils/logger.py — Colorized logging setup.
"""
import logging
from colorama import Fore, Back, Style


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG   : Fore.WHITE  + Style.DIM,
        logging.INFO    : Fore.WHITE,
        logging.WARNING : Fore.YELLOW,
        logging.ERROR   : Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    LEVEL_LABELS = {
        logging.DEBUG   : "DBG",
        logging.INFO    : "INF",
        logging.WARNING : "WRN",
        logging.ERROR   : "ERR",
        logging.CRITICAL: "CRT",
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        label = self.LEVEL_LABELS.get(record.levelno, "???")
        msg   = super().format(record)
        return f"{color}[{label}] {msg}{Style.RESET_ALL}"


def setup_logger(level_str: str = "INFO") -> logging.Logger:
    level = getattr(logging, level_str.upper(), logging.INFO)
    log   = logging.getLogger("brawl")
    log.setLevel(level)

    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter("%(message)s"))
        log.addHandler(handler)

    return log


def banner():
    b = Fore.YELLOW
    r = Style.RESET_ALL
    print(f"{b}")
    print(r"  ╔══════════════════════════════════════════════════════╗")
    print(r"  ║                                                      ║")
    print(r"  ║    ██████╗ ███████╗                                  ║")
    print(r"  ║    ██╔══██╗██╔════╝                                  ║")
    print(r"  ║    ██████╔╝███████╗   Brawl Stars                    ║")
    print(r"  ║    ██╔══██╗╚════██║   v26.184 Server Emulator        ║")
    print(r"  ║    ██████╔╝███████║   Personal / Local use           ║")
    print(r"  ║    ╚═════╝ ╚══════╝                                  ║")
    print(r"  ║                                                      ║")
    print(r"  ╚══════════════════════════════════════════════════════╝")
    print(f"{r}")
