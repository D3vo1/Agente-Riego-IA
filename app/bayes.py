"""Modulo probabilistico simple basado en odds bayesianas."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rules import IrrigationFacts


@dataclass
class BayesResult:
    probability: float | None
    evidence: list[str] = field(default_factory=list)
    explanation: str = ""


class BayesianIrrigationEstimator:
    """Estima la necesidad de riego con un Naive Bayes explicable.

    Los parametros son demostrativos y deben calibrarse con datos locales antes
    de emplearse en decisiones agronomicas reales.
    """

    prior_probability = 0.35

    def estimate(self, facts: IrrigationFacts) -> BayesResult:
        likelihood_ratios: list[tuple[str, float]] = []

        if facts.moisture is not None and 0 <= facts.moisture <= 100:
            if facts.moisture < 25:
                likelihood_ratios.append(("humedad baja", 5.0))
            elif facts.moisture > 70:
                likelihood_ratios.append(("humedad alta", 0.12))
            else:
                likelihood_ratios.append(("humedad intermedia", 0.8))
        if facts.temperature is not None:
            if facts.temperature >= 32:
                likelihood_ratios.append(("temperatura alta", 1.8))
            elif facts.temperature <= 12:
                likelihood_ratios.append(("temperatura baja", 0.65))
        if facts.rain_expected is True:
            likelihood_ratios.append(("lluvia esperada", 0.25))
        elif facts.rain_expected is False:
            likelihood_ratios.append(("sin lluvia esperada", 1.5))
        if facts.soil == "arenoso":
            likelihood_ratios.append(("suelo arenoso", 1.4))
        elif facts.soil == "arcilloso":
            likelihood_ratios.append(("suelo arcilloso", 0.8))

        if not likelihood_ratios:
            return BayesResult(
                probability=None,
                explanation="No hay evidencias suficientes para realizar la estimacion bayesiana.",
            )

        odds = self.prior_probability / (1 - self.prior_probability)
        for _, ratio in likelihood_ratios:
            odds *= ratio
        probability = odds / (1 + odds)
        probability = round(max(0.01, min(0.99, probability)), 4)
        evidence = [name for name, _ in likelihood_ratios]
        explanation = (
            "Estimacion academica calculada desde una probabilidad previa de 35 % "
            f"y las evidencias: {', '.join(evidence)}. Los valores requieren calibracion local."
        )
        return BayesResult(probability=probability, evidence=evidence, explanation=explanation)


bayes_estimator = BayesianIrrigationEstimator()
