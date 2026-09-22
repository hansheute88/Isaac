from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional

log = logging.getLogger("Isaac.DIVAProtocol")

# Standard-Halbwertszeiten in Sekunden für exponentielles Decay
DEFAULT_HALF_LIVES: Dict[str, float] = {
    "uncertainty_arousal": 1800.0,   # 30 Minuten
    "urgency_modifier": 1200.0,      # 20 Minuten
    "memory_bias_strength": 2400.0,  # 40 Minuten
}

# Standard-Base-Rates pro Turn für Turn-basiertes Decay
DEFAULT_BASE_RATES: Dict[str, float] = {
    "uncertainty_arousal": 0.08,
    "urgency_modifier": 0.10,
    "memory_bias_strength": 0.07,
}

# Standard-Parameter für logarithmisches Decay
DEFAULT_LOG_PARAMS: Dict[str, Dict[str, float]] = {
    "uncertainty_arousal": {"k": 0.35, "offset": 1.0},
    "urgency_modifier": {"k": 0.45, "offset": 1.0},
    "memory_bias_strength": {"k": 0.30, "offset": 1.0},
}

# Standard-Zeiten in Sekunden für lineares Decay
DEFAULT_LINEAR_TIMES: Dict[str, float] = {
    "uncertainty_arousal": 2400.0,   # 40 Minuten
    "urgency_modifier": 1800.0,      # 30 Minuten
    "memory_bias_strength": 3000.0,  # 50 Minuten
}

# Standard-Anhebefaktoren bei DIVA-Event-Trigger
DEFAULT_RAISE_FACTORS: Dict[str, float] = {
    "uncertainty_arousal": 0.40,
    "urgency_modifier": 0.30,
    "memory_bias_strength": 0.35,
}

RESOLVED_HALF_LIFE_FACTOR: float = 0.25   # Halbwertszeit auf 25% reduzieren
RESOLVED_K_MULTIPLIER: float = 3.5        # k-Faktor für logarithmisches Decay
RESOLVED_BOOST_MULTIPLIER: float = 3.0    # Beschleunigung für Turn/Lineardecay


def create_initial_diva_modulators() -> Dict[str, Any]:
    """Erstellt den initialen Zustand der DIVA-Modulatoren."""
    return {
        "uncertainty_arousal": 0.0,
        "urgency_modifier": 0.0,
        "memory_bias_strength": 0.0,
        "last_update_ts": time.time(),
        "active_diva_events": [],
    }


def clamp_modulator(value: float) -> float:
    """Stellt sicher, dass ein Modulator-Wert im Bereich [0.0, 1.0] bleibt."""
    return max(0.0, min(1.0, float(value)))


def exponential_decay(
    current_value: float,
    elapsed_seconds: float,
    half_life_seconds: float,
) -> float:
    """
    Exponentielles Decay.
    Formel: current_value * (0.5 ** (elapsed_seconds / half_life_seconds))
    """
    if current_value <= 0.0 or half_life_seconds <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    decayed = current_value * (0.5 ** (elapsed_seconds / half_life_seconds))
    return decayed if decayed > 1e-6 else 0.0


def logarithmic_decay(
    current_value: float,
    elapsed_seconds: float,
    k: float = 0.35,
    offset: float = 1.0,
) -> float:
    """
    Logarithmisches Decay.
    Formel: current_value * (1 / (offset + k * log1p(elapsed_seconds)))
    """
    if current_value <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    log_term = math.log1p(elapsed_seconds)
    factor = 1.0 / (offset + k * log_term)
    decayed = current_value * factor
    return decayed if decayed > 1e-6 else 0.0


def linear_decay(
    current_value: float,
    elapsed_seconds: float,
    total_decay_seconds: float,
) -> float:
    """
    Lineares Decay.
    Formel: current_value * (1.0 - elapsed_seconds / total_decay_seconds)
    """
    if current_value <= 0.0 or total_decay_seconds <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    progress = min(1.0, elapsed_seconds / total_decay_seconds)
    decayed = current_value * (1.0 - progress)
    return decayed if decayed > 1e-6 else 0.0


def turn_decay(
    current_value: float,
    rate: float,
    dt_turns: float = 1.0,
    factor: float = 1.0,
) -> float:
    """
    Turn-basiertes Decay.
    Formel: current_value - (rate * factor * dt_turns)
    """
    if current_value <= 0.0:
        return 0.0

    decay_amount = rate * factor * dt_turns
    return max(0.0, current_value - decay_amount)


def raise_modulators(
    modulators: Dict[str, Any],
    uncertainty: float,
    relevance: float,
    event_id: Optional[str] = None,
    raise_factors: Optional[Dict[str, float]] = None,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Hebt die DIVA-Modulatoren proportional zu Unsicherheit und Relevanz an.
    """
    now_ts = now if now is not None else time.time()
    factors = raise_factors or DEFAULT_RAISE_FACTORS

    unc = clamp_modulator(uncertainty)
    rel = clamp_modulator(relevance)
    strength = min(1.0, unc * rel)

    for key, base_factor in factors.items():
        current = float(modulators.get(key, 0.0))
        delta = base_factor * strength
        modulators[key] = clamp_modulator(current + delta)

    modulators["last_update_ts"] = now_ts

    if event_id:
        active_events: List[str] = list(modulators.get("active_diva_events") or [])
        if event_id not in active_events:
            active_events.append(event_id)
        modulators["active_diva_events"] = active_events

    log.debug("DIVA modulators raised: strength=%.4f -> %s", strength, modulators)
    return modulators


def decay_modulators(
    modulators: Dict[str, Any],
    decay_type: str = "exponential",
    half_lives: Optional[Dict[str, float]] = None,
    base_rates: Optional[Dict[str, float]] = None,
    log_params: Optional[Dict[str, Dict[str, float]]] = None,
    linear_times: Optional[Dict[str, float]] = None,
    resolved: bool = False,
    dt_turns: float = 1.0,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Wendet das gewählte Decay (exponential, logarithmic, linear, turn) auf die Modulatoren an.
    """
    now_ts = now if now is not None else time.time()
    last_ts = float(modulators.get("last_update_ts") or now_ts)
    elapsed = max(0.0, now_ts - last_ts)

    keys = ("uncertainty_arousal", "urgency_modifier", "memory_bias_strength")
    decay_mode = (decay_type or "exponential").lower().strip()

    if decay_mode == "turn":
        rates = base_rates or DEFAULT_BASE_RATES
        boost_factor = RESOLVED_BOOST_MULTIPLIER if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            rate = float(rates.get(key, 0.08))
            modulators[key] = clamp_modulator(turn_decay(curr, rate, dt_turns=dt_turns, factor=boost_factor))
    elif decay_mode == "logarithmic":
        params_map = log_params or DEFAULT_LOG_PARAMS
        k_mult = RESOLVED_K_MULTIPLIER if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            p = params_map.get(key, {"k": 0.35, "offset": 1.0})
            k_val = float(p.get("k", 0.35)) * k_mult
            offset_val = float(p.get("offset", 1.0))
            modulators[key] = clamp_modulator(logarithmic_decay(curr, elapsed, k=k_val, offset=offset_val))
    elif decay_mode == "linear":
        times_map = linear_times or DEFAULT_LINEAR_TIMES
        factor = RESOLVED_HALF_LIFE_FACTOR if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            total_time = float(times_map.get(key, 2400.0)) * factor
            modulators[key] = clamp_modulator(linear_decay(curr, elapsed, total_time))
    else:  # exponential (default)
        hl_map = half_lives or DEFAULT_HALF_LIVES
        factor = RESOLVED_HALF_LIFE_FACTOR if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            hl = float(hl_map.get(key, 1800.0)) * factor
            modulators[key] = clamp_modulator(exponential_decay(curr, elapsed, hl))

    modulators["last_update_ts"] = now_ts
    return modulators


def on_diva_resolved(
    modulators: Dict[str, Any],
    event_id: Optional[str] = None,
    immediate_reduction_factor: float = 0.4,
    decay_type: str = "exponential",
    now: Optional[float] = None,
    **decay_kwargs: Any,
) -> Dict[str, Any]:
    """
    Wird aufgerufen, wenn ein DIVA-Event gelöst ist.
    Entfernt event_id, reduziert Modulatoren sofort und wendet beschleunigtes Decay an.
    """
    now_ts = now if now is not None else time.time()

    if event_id:
        active_events: List[str] = list(modulators.get("active_diva_events") or [])
        if event_id in active_events:
            active_events.remove(event_id)
        modulators["active_diva_events"] = active_events

    # Sofortige Absenkung
    for key in ("uncertainty_arousal", "urgency_modifier", "memory_bias_strength"):
        curr = float(modulators.get(key, 0.0))
        modulators[key] = clamp_modulator(curr * immediate_reduction_factor)

    # Anschließendes beschleunigtes Decay
    return decay_modulators(
        modulators=modulators,
        decay_type=decay_type,
        resolved=True,
        now=now_ts,
        **decay_kwargs,
    )


def check_cognitive_loss_trigger(loss_delta_i: float, threshold: float = 2.0) -> bool:
    """
    Prüft, ob ein kognitiver Loss Delta I den Schwellenwert überschreitet,
    um automatisch ein DIVA-Event auszulösen.
    """
    return loss_delta_i > threshold
