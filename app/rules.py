"""Sistema basado en reglas para recomendaciones deterministas de riego."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class IrrigationFacts:
    """Hechos extraidos de una consulta en lenguaje natural."""

    crop: str | None = None
    soil: str | None = None
    moisture: float | None = None
    temperature: float | None = None
    rain_expected: bool | None = None
    actuator_request: bool = False


@dataclass
class RuleEvaluation:
    """Resultado explicable del motor de inferencia."""

    facts: IrrigationFacts
    fired_rules: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)

    @property
    def has_evidence(self) -> bool:
        return bool(self.fired_rules or self.recommendations)


class IrrigationRuleEngine:
    """Motor de reglas academico con encadenamiento hacia adelante."""

    CROP_ALIASES = {
        "tomate": "tomate",
        "jitomate": "tomate",
        "fresa": "fresa",
        "maiz": "maiz",
        "maíz": "maiz",
        "lechuga": "lechuga",
        "pepino": "pepino",
    }
    SOIL_ALIASES = {
        "arenoso": "arenoso",
        "arena": "arenoso",
        "franco": "franco",
        "arcilloso": "arcilloso",
        "arcilla": "arcilloso",
        "sustrato": "sustrato",
        "coco": "fibra de coco",
    }

    def extract_facts(self, message: str) -> IrrigationFacts:
        text = message.lower()
        crop = next((v for k, v in self.CROP_ALIASES.items() if k in text), None)
        soil = next((v for k, v in self.SOIL_ALIASES.items() if k in text), None)

        moisture_match = re.search(
            r"(?:humedad(?:\s+del\s+(?:suelo|sustrato))?[^\d]{0,20})"
            r"(\d{1,3}(?:[.,]\d+)?)\s*%?",
            text,
        )
        temperature_match = re.search(
            r"(?:temperatura|temp(?:eratura)?)[^\d-]{0,15}(-?\d{1,2}(?:[.,]\d+)?)",
            text,
        )

        moisture = self._number(moisture_match.group(1)) if moisture_match else None
        temperature = self._number(temperature_match.group(1)) if temperature_match else None

        rain_expected: bool | None = None
        if any(term in text for term in ("no va a llover", "sin lluvia", "no se espera lluvia")):
            rain_expected = False
        elif any(term in text for term in ("va a llover", "lluvia esperada", "pronostico de lluvia", "pronóstico de lluvia")):
            rain_expected = True

        actuator_request = any(
            term in text
            for term in (
                "abre la valvula",
                "abre la válvula",
                "enciende la bomba",
                "activa el riego",
                "riega por mi",
                "riega por mí",
            )
        )
        return IrrigationFacts(
            crop=crop,
            soil=soil,
            moisture=moisture,
            temperature=temperature,
            rain_expected=rain_expected,
            actuator_request=actuator_request,
        )

    def evaluate(self, message: str) -> RuleEvaluation:
        facts = self.extract_facts(message)
        result = RuleEvaluation(facts=facts)

        if facts.actuator_request:
            result.fired_rules.append("R-SEG-01")
            result.recommendations.append(
                "El prototipo no acciona bombas ni valvulas; se requiere verificacion humana."
            )

        if facts.moisture is not None:
            if not 0 <= facts.moisture <= 100:
                result.fired_rules.append("R-DAT-01")
                result.recommendations.append(
                    "La humedad indicada esta fuera del rango de 0 a 100 % y debe verificarse."
                )
            elif facts.moisture < 25:
                result.fired_rules.append("R-HUM-01")
                result.recommendations.append(
                    "La humedad reportada es baja; conviene revisar el cultivo y considerar riego."
                )
            elif facts.moisture > 70:
                result.fired_rules.append("R-HUM-03")
                result.recommendations.append(
                    "La humedad reportada es alta; conviene posponer el riego y revisar drenaje."
                )
            else:
                result.fired_rules.append("R-HUM-02")
                result.recommendations.append(
                    "La humedad reportada esta en el intervalo demostrativo intermedio; confirme el umbral del cultivo antes de regar."
                )

        if facts.temperature is not None and facts.temperature >= 32:
            result.fired_rules.append("R-TEMP-01")
            result.recommendations.append(
                "La temperatura es alta; priorice una inspeccion y evite regar en las horas de mayor radiacion."
            )

        if facts.rain_expected is True:
            result.fired_rules.append("R-CLIMA-01")
            result.recommendations.append(
                "Hay lluvia esperada; posponga la decision hasta verificar el pronostico y la humedad real."
            )
        elif facts.rain_expected is False and facts.moisture is not None and facts.moisture < 25:
            result.fired_rules.append("R-CLIMA-02")
            result.recommendations.append(
                "La ausencia de lluvia aumenta la prioridad de revisar la necesidad de riego."
            )

        if facts.soil == "arenoso" and facts.moisture is not None and facts.moisture < 35:
            result.fired_rules.append("R-SUELO-01")
            result.recommendations.append(
                "El suelo arenoso retiene menos agua; use riegos controlados y compruebe la humedad con mayor frecuencia."
            )

        if facts.crop is None:
            result.missing_data.append("cultivo")
        if facts.moisture is None:
            result.missing_data.append("humedad del suelo o sustrato")
        if facts.soil is None:
            result.missing_data.append("tipo de suelo o sustrato")

        return result

    @staticmethod
    def _number(value: str) -> float:
        return float(value.replace(",", "."))


rule_engine = IrrigationRuleEngine()
