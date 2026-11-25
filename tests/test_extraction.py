"""Casos de lenguaje natural que antes se interpretaban mal."""

import pytest

from app.rules import IrrigationFacts, IrrigationRuleEngine


engine = IrrigationRuleEngine()


def test_rain_negation_is_detected() -> None:
    facts = engine.extract_facts("No hay lluvia esperada, tomate con humedad 30 % y temperatura 31")
    assert facts.rain_expected is False
    assert "R-CLIMA-01" not in engine.evaluate_facts(facts).fired_rules


@pytest.mark.parametrize(
    "message",
    ["Va a llover mañana", "Hay pronóstico de lluvia", "probabilidad de lluvia 80 %"],
)
def test_rain_expected(message: str) -> None:
    assert engine.extract_facts(message).rain_expected is True


@pytest.mark.parametrize(
    "message",
    ["Sin lluvia esta semana", "no va a llover", "No se espera que llueva", "probabilidad de lluvia 10 %"],
)
def test_no_rain_expected(message: str) -> None:
    assert engine.extract_facts(message).rain_expected is False


def test_relative_humidity_is_not_soil_moisture() -> None:
    facts = engine.extract_facts("La humedad relativa es 60 % y la temperatura 28 en mi fresa")
    assert facts.moisture is None
    assert facts.air_humidity == 60


def test_soil_and_air_humidity_in_same_message() -> None:
    facts = engine.extract_facts("Humedad ambiental 45 % y humedad del suelo 18,5 %")
    assert facts.air_humidity == 45
    assert facts.moisture == 18.5


def test_season_year_is_not_a_temperature() -> None:
    facts = engine.extract_facts("Esta temporada 2026 tengo maíz con humedad 40 %")
    assert facts.temperature is None
    assert facts.crop == "maiz"


def test_temperature_with_degrees() -> None:
    assert engine.extract_facts("Estamos a 34 °C").temperature == 34
    assert engine.extract_facts("hace 30 grados").temperature == 30


def test_plural_and_accented_names() -> None:
    facts = engine.extract_facts("Mis fresas están en sustrato de fibra de coco")
    assert facts.crop == "fresa"
    assert facts.soil == "fibra de coco"


@pytest.mark.parametrize(
    "message",
    [
        "Abre las válvulas del sector 2",
        "enciende las bombas",
        "Activa el riego por goteo",
        "riega por mí",
    ],
)
def test_actuator_requests_fire_safety_rule(message: str) -> None:
    assert "R-SEG-01" in engine.evaluate(message).fired_rules


def test_safety_rule_cannot_be_disabled() -> None:
    restricted = IrrigationRuleEngine(disabled_rules={"R-SEG-01", "R-HUM-01"})
    result = restricted.evaluate("Abre la válvula, la humedad es 10 %")
    assert "R-SEG-01" in result.fired_rules
    assert "R-HUM-01" not in result.fired_rules


def test_unknown_crop_is_reported() -> None:
    result = engine.evaluate("Tengo chile en suelo franco, humedad 22 %, temperatura 33")
    assert result.facts.crop is None
    assert result.facts.unknown_crop == "chile"
    assert "R-DAT-02" in result.fired_rules
    assert "cultivo" not in result.missing_data


def test_common_phrases_are_not_crops() -> None:
    assert engine.extract_facts("Tengo dudas con el riego").unknown_crop is None


def test_facts_accumulate_across_messages() -> None:
    first = engine.evaluate("Tengo jitomate en suelo arenoso")
    second = engine.evaluate("La humedad del suelo es 20 %", previous=first.facts)
    assert second.facts.crop == "tomate"
    assert second.facts.soil == "arenoso"
    assert second.facts.moisture == 20
    assert "R-SUELO-01" in second.fired_rules
    assert second.missing_data == []


def test_new_values_replace_previous_ones() -> None:
    previous = IrrigationFacts(crop="tomate", moisture=20, actuator_request=True)
    merged = previous.merged_with(engine.extract_facts("ahora la humedad es 65 %"))
    assert merged.moisture == 65
    assert merged.crop == "tomate"
    assert merged.actuator_request is False
