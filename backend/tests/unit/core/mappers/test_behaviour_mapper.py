"""M9-C43.6 — Coverage + mutation-strengthening for core/mappers/behaviour_mapper.py.

This module was at 0% line coverage. These tests exercise every branch of the
BehaviourMapper (full dict, empty sub-dicts, list comprehensions).
"""

from __future__ import annotations

import pytest

from src.core.mappers.behaviour_mapper import BehaviourMapper


def test_to_dto_full() -> None:
    data = {
        "wellness_score": {"score": 72, "label": "Good", "factors": ["a", "b"]},
        "spending_patterns": [
            {"category": "Food", "amount_paise": 1000, "percentage": 0.3,
             "trend": "up", "month_over_month_change": 0.1},
        ],
        "savings_rate": {
            "savings_rate_bps": 2500, "income_paise": 100000,
            "savings_paise": 25000, "period": "1M",
        },
        "debt_health": {
            "debt_to_income_bps": 4000, "total_debt_paise": 40000,
            "total_income_paise": 100000, "health_score": 60,
        },
        "wellness_radar": [
            {"dimension": "Calm", "score": 800, "max_score": 1000},
        ],
        "insights": [
            {"type": "warning", "severity": "high", "message": "x", "action_url": "http://y"},
        ],
        "evidence_chain": {
            "summary": "ok", "confidence_score": 80.0,
            "evidence": [], "calculation_steps": [], "source_references": [],
        },
    }
    dto = BehaviourMapper.to_dto(data)
    assert dto.wellness_score.score == 72
    assert dto.wellness_score.label == "Good"
    assert dto.wellness_score.factors == ["a", "b"]
    assert dto.spending_patterns[0].category == "Food"
    assert dto.spending_patterns[0].amount_paise == 1000
    assert dto.spending_patterns[0].percentage == 0.3
    assert dto.spending_patterns[0].trend == "up"
    assert dto.spending_patterns[0].month_over_month_change == 0.1
    assert dto.savings_rate.savings_rate_bps == 2500
    assert dto.savings_rate.income_paise == 100000
    assert dto.savings_rate.savings_paise == 25000
    assert dto.savings_rate.period == "1M"
    assert dto.debt_health.debt_to_income_bps == 4000
    assert dto.debt_health.total_debt_paise == 40000
    assert dto.debt_health.total_income_paise == 100000
    assert dto.debt_health.health_score == 60
    assert dto.wellness_radar[0].dimension == "Calm"
    assert dto.wellness_radar[0].score == 800
    assert dto.wellness_radar[0].max_score == 1000
    assert dto.insights[0].type == "warning"
    assert dto.insights[0].severity == "high"
    assert dto.insights[0].message == "x"
    assert dto.insights[0].action_url == "http://y"
    assert dto.evidence_chain is not None
    assert dto.evidence_chain.summary == "ok"
    assert dto.evidence_chain.confidence_score == 80.0


def test_to_dto_missing_subdicts() -> None:
    """Empty score dict and None savings/debt fall back to defaults."""
    data = {
        "wellness_score": {},
        "spending_patterns": [],
        "savings_rate": None,
        "debt_health": None,
        "wellness_radar": [],
        "insights": [],
    }
    dto = BehaviourMapper.to_dto(data)
    assert dto.wellness_score.score == 0
    assert dto.wellness_score.label == "Unknown"
    assert dto.wellness_score.factors == []
    assert dto.savings_rate is None
    assert dto.debt_health is None
    assert dto.spending_patterns == []
    assert dto.wellness_radar == []
    assert dto.insights == []
    assert dto.evidence_chain is None


def test_to_dto_defaults_in_lists() -> None:
    """Comprehensions apply defaults when keys absent."""
    data = {
        "spending_patterns": [{}],
        "wellness_radar": [{}],
        "insights": [{}],
    }
    dto = BehaviourMapper.to_dto(data)
    assert dto.spending_patterns[0].category == "Unknown"
    assert dto.spending_patterns[0].amount_paise == 0
    assert dto.spending_patterns[0].percentage == 0.0
    assert dto.spending_patterns[0].trend == "stable"
    assert dto.spending_patterns[0].month_over_month_change == 0.0
    assert dto.wellness_radar[0].dimension == "Unknown"
    assert dto.wellness_radar[0].score == 0
    assert dto.wellness_radar[0].max_score == 10000
    assert dto.insights[0].type == "info"
    assert dto.insights[0].severity == "medium"
    assert dto.insights[0].message == ""
    assert dto.insights[0].action_url is None


def test_to_dto_empty_dict() -> None:
    """Fully empty behaviour data still produces a DTO with defaults."""
    dto = BehaviourMapper.to_dto({})
    assert dto.wellness_score.score == 0
    assert dto.wellness_score.label == "Unknown"
    assert dto.savings_rate is None
    assert dto.debt_health is None
