"""Configuration du logging pour le pipeline landing-generator.

Usage:
    from core.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")
"""

import logging
import sys
from pathlib import Path
from typing import Literal

# Niveau de log par défaut
DEFAULT_LEVEL = logging.INFO

# Format des messages
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger racine du projet
ROOT_LOGGER_NAME = "landing_generator"

_configured = False


def configure_logging(
    level: int = DEFAULT_LEVEL,
    log_file: Path | None = None,
    format_style: Literal["simple", "detailed"] = "simple",
) -> None:
    """Configure le logging pour tout le projet.

    Args:
        level: Niveau de log (logging.DEBUG, INFO, WARNING, ERROR)
        log_file: Fichier de log optionnel
        format_style: "simple" pour dev, "detailed" pour prod
    """
    global _configured
    if _configured:
        return

    # Format selon le style
    if format_style == "simple":
        fmt = "%(levelname)-8s | %(message)s"
    else:
        fmt = LOG_FORMAT

    # Configuration du handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(fmt, LOG_DATE_FORMAT))

    # Configuration du logger racine du projet
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Handler fichier optionnel
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré pour le module donné.

    Args:
        name: Nom du module (typiquement __name__)

    Returns:
        Logger configuré sous le namespace landing_generator
    """
    # Configure si pas encore fait
    if not _configured:
        configure_logging()

    # Crée un sous-logger du logger racine
    if name.startswith(ROOT_LOGGER_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


class StepTimer:
    """Context manager pour mesurer et logger la durée d'une étape.

    Usage:
        with StepTimer(logger, "OnboardingAgent"):
            # ... code ...
    """

    def __init__(self, logger: logging.Logger, step_name: str):
        self.logger = logger
        self.step_name = step_name
        self._start_time: float = 0

    def __enter__(self) -> "StepTimer":
        import time
        self._start_time = time.perf_counter()
        self.logger.info(f"[START] {self.step_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import time
        duration_ms = (time.perf_counter() - self._start_time) * 1000
        if exc_type is None:
            self.logger.info(f"[DONE]  {self.step_name} ({duration_ms:.0f}ms)")
        else:
            self.logger.error(f"[FAIL]  {self.step_name} ({duration_ms:.0f}ms) - {exc_val}")
        return None  # Ne pas supprimer l'exception
