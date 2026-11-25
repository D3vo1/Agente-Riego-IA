from app.bayes import BayesianIrrigationEstimator
from app.rules import IrrigationRuleEngine


def test_low_moisture_activates_rule_and_bayes() -> None:
    engine = IrrigationRuleEngine()
    evaluation = engine.evaluate(
        "Tengo jitomate en suelo arenoso, humedad del suelo 18 %, temperatura 34 y sin lluvia"
    )
    assert evaluation.facts.crop == "tomate"
    assert evaluation.facts.moisture == 18
    assert "R-HUM-01" in evaluation.fired_rules
    assert "R-TEMP-01" in evaluation.fired_rules
    assert "R-SUELO-01" in evaluation.fired_rules

    result = BayesianIrrigationEstimator().estimate(evaluation.facts)
    assert result.probability is not None
    assert result.probability > 0.8


def test_high_moisture_reduces_probability() -> None:
    facts = IrrigationRuleEngine().extract_facts(
        "Fresa en suelo arcilloso con humedad 82 % y lluvia esperada"
    )
    result = BayesianIrrigationEstimator().estimate(facts)
    assert result.probability is not None
    assert result.probability < 0.1


def test_actuator_request_is_blocked() -> None:
    result = IrrigationRuleEngine().evaluate("Abre la válvula y activa el riego")
    assert "R-SEG-01" in result.fired_rules
    assert any("no acciona" in item for item in result.recommendations)
