"""Erreurs et exceptions du pipeline landing-generator.

Ce module centralise toutes les exceptions métier avec des messages explicites
pour faciliter le debug et l'intégration CI/CD.
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Codes d'erreur standardisés pour le pipeline."""

    # Validation errors (1xx)
    SCHEMA_VALIDATION = "E101"
    INVALID_TONE = "E102"
    INVALID_VARIANT_ID = "E103"
    INVALID_TEMPLATE_TYPE = "E104"
    INVALID_HEX_COLOR = "E105"
    MISSING_REQUIRED_FIELD = "E106"

    # Agent errors (2xx)
    ONBOARDING_FAILED = "E201"
    BRAND_FAILED = "E202"
    LANDING_FAILED = "E203"
    LLM_GENERATION_FAILED = "E204"

    # Render errors (3xx)
    TEMPLATE_NOT_FOUND = "E301"
    RENDER_FAILED = "E302"
    MISSING_CONTENT = "E303"

    # IO errors (4xx)
    FILE_NOT_FOUND = "E401"
    FILE_WRITE_FAILED = "E402"
    JSON_PARSE_FAILED = "E403"


class PipelineError(Exception):
    """Exception de base pour toutes les erreurs du pipeline.

    Attributes:
        code: Code d'erreur standardisé (ErrorCode enum)
        message: Message d'erreur lisible
        details: Informations supplémentaires pour le debug
        step: Étape du pipeline où l'erreur s'est produite
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        step: str | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.step = step
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Formate le message d'erreur complet."""
        parts = [f"[{self.code.value}]"]
        if self.step:
            parts.append(f"[{self.step}]")
        parts.append(self.message)
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'erreur pour logging/API."""
        return {
            "code": self.code.value,
            "message": self.message,
            "step": self.step,
            "details": self.details,
        }


class ValidationError(PipelineError):
    """Erreur de validation des données d'entrée."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        code: ErrorCode = ErrorCode.SCHEMA_VALIDATION,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]  # Tronque pour les logs
        super().__init__(code=code, message=message, details=details, step="validation")


class AgentError(PipelineError):
    """Erreur lors de l'exécution d'un agent."""

    def __init__(
        self,
        agent_name: str,
        message: str,
        code: ErrorCode,
        cause: Exception | None = None,
    ):
        details = {"agent": agent_name}
        if cause:
            details["cause"] = str(cause)
        super().__init__(code=code, message=message, details=details, step=agent_name)


class RenderError(PipelineError):
    """Erreur lors du rendu HTML."""

    def __init__(
        self,
        message: str,
        template: str | None = None,
        code: ErrorCode = ErrorCode.RENDER_FAILED,
    ):
        details = {}
        if template:
            details["template"] = template
        super().__init__(code=code, message=message, details=details, step="render")
