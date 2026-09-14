"""
validation.py
==============

Centralised, reusable validation helpers for the thermal engine.

Pydantic was deliberately NOT used for the core data models in this phase.
The engine is meant to be a small, dependency-light, standalone module that
can later be embedded inside a larger backend (which may already bring its
own Pydantic/DB models). Plain Python dataclasses + explicit validation
functions give the same "fail fast with a clear message" behaviour with
zero external dependencies for the core physics, while pytest remains an
external (test-time only) dependency as required by the brief.

Every validator raises ``ThermalEngineValidationError`` (a subclass of
``ValueError``) with a human-readable message describing exactly what was
wrong and, where useful, what a valid value looks like.
"""

from __future__ import annotations

from typing import Iterable, Sequence


class ThermalEngineValidationError(ValueError):
    """Raised when user-supplied input to the thermal engine is invalid."""


def validate_positive(value: float, name: str) -> float:
    """Validate that ``value`` is a strictly positive, finite number."""
    _validate_is_number(value, name)
    if value <= 0:
        raise ThermalEngineValidationError(
            f"'{name}' must be strictly positive, got {value!r}."
        )
    return float(value)


def validate_non_negative(value: float, name: str) -> float:
    """Validate that ``value`` is a non-negative, finite number (>= 0)."""
    _validate_is_number(value, name)
    if value < 0:
        raise ThermalEngineValidationError(
            f"'{name}' must be zero or positive, got {value!r}."
        )
    return float(value)


def validate_fraction(value: float, name: str) -> float:
    """Validate that ``value`` lies in the physically valid range [0, 1]."""
    _validate_is_number(value, name)
    if not (0.0 <= value <= 1.0):
        raise ThermalEngineValidationError(
            f"'{name}' must be between 0 and 1 (inclusive), got {value!r}."
        )
    return float(value)


def validate_temperature_celsius(value: float, name: str) -> float:
    """
    Validate a temperature expressed in degrees Celsius.

    Rejects values below absolute zero (-273.15 C) and implausibly high
    values, which almost always indicate a unit mistake (e.g. Kelvin
    passed in by accident).
    """
    _validate_is_number(value, name)
    if value < -273.15:
        raise ThermalEngineValidationError(
            f"'{name}' of {value!r} C is below absolute zero. "
            "Check that the value is in degrees Celsius, not Kelvin."
        )
    if value > 100.0:
        raise ThermalEngineValidationError(
            f"'{name}' of {value!r} C looks implausible for this model "
            "(expected a typical ambient/indoor air temperature)."
        )
    return float(value)


def validate_non_negative_sequence(values: Sequence[float], name: str) -> None:
    """Validate that every element of a sequence is a non-negative number."""
    for i, v in enumerate(values):
        _validate_is_number(v, f"{name}[{i}]")
        if v < 0:
            raise ThermalEngineValidationError(
                f"'{name}[{i}]' must be zero or positive, got {v!r}."
            )


def validate_non_empty_string(value: str, name: str) -> str:
    """Validate that ``value`` is a non-empty, non-whitespace string."""
    if not isinstance(value, str) or not value.strip():
        raise ThermalEngineValidationError(
            f"'{name}' must be a non-empty string, got {value!r}."
        )
    return value.strip()


def validate_positive_int(value: int, name: str) -> int:
    """Validate that ``value`` is a positive integer (or integral float)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ThermalEngineValidationError(
            f"'{name}' must be an integer, got {value!r}."
        )
    if float(value) != int(value):
        raise ThermalEngineValidationError(
            f"'{name}' must be a whole number, got {value!r}."
        )
    if int(value) <= 0:
        raise ThermalEngineValidationError(
            f"'{name}' must be a positive integer, got {value!r}."
        )
    return int(value)


def validate_comfort_range(comfort_range: tuple[float, float] | None) -> None:
    """Validate an optional (min, max) thermal comfort range in Celsius."""
    if comfort_range is None:
        return
    if not isinstance(comfort_range, (tuple, list)) or len(comfort_range) != 2:
        raise ThermalEngineValidationError(
            "'comfort_range' must be a (min, max) tuple of two temperatures "
            f"in Celsius, got {comfort_range!r}."
        )
    low, high = comfort_range
    validate_temperature_celsius(low, "comfort_range.min")
    validate_temperature_celsius(high, "comfort_range.max")
    if low >= high:
        raise ThermalEngineValidationError(
            f"'comfort_range' minimum ({low}) must be less than maximum ({high})."
        )


def validate_time_series_length(
    values: Iterable, expected_length: int, name: str
) -> None:
    """Validate that a time-series input has a usable, positive length."""
    values = list(values)
    if len(values) == 0:
        raise ThermalEngineValidationError(f"'{name}' must not be empty.")
    if expected_length <= 0:
        raise ThermalEngineValidationError(
            "Simulation must have at least one timestep."
        )


def _validate_is_number(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ThermalEngineValidationError(
            f"'{name}' must be a number, got {type(value).__name__}: {value!r}."
        )
    if value != value:  # NaN check without importing math
        raise ThermalEngineValidationError(f"'{name}' must not be NaN.")
    if value in (float("inf"), float("-inf")):
        raise ThermalEngineValidationError(f"'{name}' must be finite.")
