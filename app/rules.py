"""Sistema basado en reglas para recomendaciones deterministas de riego."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
import re
import unicodedata


@dataclass
class IrrigationFacts:
    """Hechos extraidos de una consulta en lenguaje natural."""

    crop: str | None = None
    unknown_crop: str | None = None
    soil: str | None = None
    moisture: float | None = None
    air_humidity: float | None = None
    temperature: float | None = None
    rain_expected: bool | None = None
    actuator_request: bool = False

    def merged_with(self, newer: "IrrigationFacts") -> "IrrigationFacts":
        """Combina hechos previos de la sesion con los del mensaje nuevo.

        Los valores nuevos sustituyen a los anteriores. La peticion de accionar
        equipos solo cuenta para el mensaje actual.
        """

        values = {}
        for item in fields(self):
            new_value = getattr(newer, item.name)
            old_value = getattr(self, item.name)
            values[item.name] = new_value if new_value is not None else old_value
        if newer.crop is not None:
            values["unknown_crop"] = None
        elif newer.unknown_crop is not None:
            values["crop"] = None
        values["actuator_request"] = newer.actuator_request
        return replace(self, **values)


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


NUMBER = r"(\d{1,3}(?:[.,]\d+)?)(?![\d.,]*\d)"

CROP_PATTERNS = {
    "tomate": r"\b(?:jitomate|tomate)s?\b",
    "fresa": r"\bfresas?\b",
    "maiz": r"\bmaiz(?:al|es)?\b",
    "lechuga": r"\blechugas?\b",
    "pepino": r"\bpepinos?\b",
}
SOIL_PATTERNS = {
    "arenoso": r"\b(?:arenos[oa]s?|arena)\b",
    "franco": r"\bfranc[oa]s?\b",
    "arcilloso": r"\b(?:arcillos[oa]s?|arcilla)\b",
    "fibra de coco": r"\b(?:fibra de )?coco\b",
    "sustrato": r"\bsustratos?\b",
}
# Palabras que no son cultivos aunque aparezcan tras "tengo" o "cultivo de".
NOT_A_CROP = {
    "un", "una", "unos", "unas", "el", "la", "los", "las", "mi", "mis", "que",
    "humedad", "suelo", "sustrato", "riego", "agua", "temperatura", "duda",
    "problema", "pregunta", "sistema", "bomba", "valvula", "sensor", "lluvia",
    "hoja", "planta", "huerto", "parcela", "invernadero", "fuga", "dato",
}
AIR_HUMIDITY = r"humedad\s+(?:ambiental|relativa|del\s+aire|atmosferica)"
NEGATION = r"\b(?:no|sin|ni|nunca)\b"


def normalize(text: str) -> str:
    """Minusculas y sin acentos para que las reglas no dependan de la ortografia."""

    decomposed = unicodedata.normalize("NFKD", text.lower())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks.replace("º", "°")


class IrrigationRuleEngine:
    """Motor de reglas academico con encadenamiento hacia adelante."""

    KNOWN_CROPS = tuple(CROP_PATTERNS)

    def __init__(self, disabled_rules: set[str] | None = None) -> None:
        self.disabled_rules: set[str] = set(disabled_rules or ())

    # ------------------------------------------------------------------ hechos
    def extract_facts(self, message: str) -> IrrigationFacts:
        text = normalize(message)
        crop = next(
            (name for name, pattern in CROP_PATTERNS.items() if re.search(pattern, text)),
            None,
        )
        return IrrigationFacts(
            crop=crop,
            unknown_crop=None if crop else self._unknown_crop(text),
            soil=next(
                (name for name, pattern in SOIL_PATTERNS.items() if re.search(pattern, text)),
                None,
            ),
            moisture=self._soil_moisture(text),
            air_humidity=self._search_number(AIR_HUMIDITY + r"[^\d]{0,20}" + NUMBER, text),
            temperature=self._temperature(text),
            rain_expected=self._rain_expected(text),
            actuator_request=self._actuator_request(text),
        )

    def _soil_moisture(self, text: str) -> float | None:
        # Se descartan las menciones de humedad ambiental o relativa.
        pattern = (
            r"humedad(?!\s+(?:ambiental|relativa|del\s+aire|atmosferica))"
            r"(?:\s+del\s+(?:suelo|sustrato))?[^\d%]{0,20}" + NUMBER
        )
        return self._search_number(pattern, text)

    def _temperature(self, text: str) -> float | None:
        # "temp" debe ser palabra completa: "temporada 2026" no es temperatura.
        explicit = re.search(
            r"\b(?:temperatura|temp)\b[^\d-]{0,15}(-?\d{1,2}(?:[.,]\d+)?)(?![\d.,]*\d)",
            text,
        )
        if explicit:
            return self._number(explicit.group(1))
        degrees = re.search(r"(-?\d{1,2}(?:[.,]\d+)?)\s*(?:°\s*c?|grados)", text)
        return self._number(degrees.group(1)) if degrees else None

    @staticmethod
    def _rain_expected(text: str) -> bool | None:
        probability = re.search(
            r"probabilidad\s+de\s+lluvia[^\d]{0,12}(\d{1,3})\s*%", text
        )
        if probability:
            value = int(probability.group(1))
            if value >= 60:
                return True
            if value <= 20:
                return False
        rain_word = r"(?:llov\w*|lluvias?)"
        # Una negacion hasta tres palabras antes: "no hay lluvia esperada",
        # "sin lluvia", "no se espera que llueva".
        filler = r"(?:hay|habra|se|espera|esperan|esperamos|va|a|que|pronostico|de|nada|mas|mucha|tanta)"
        if re.search(
            NEGATION + r"(?:\s+" + filler + r"){0,3}\s+(?:" + rain_word + r"|llueva)", text
        ):
            return False
        if re.search(
            r"va\s+a\s+llover|llovera|se\s+espera(?:n)?\s+lluvias?|lluvias?\s+esperadas?"
            r"|pronostico\s+de\s+lluvias?|esta\s+lloviendo",
            text,
        ):
            return True
        return None

    @staticmethod
    def _actuator_request(text: str) -> bool:
        verbs = (
            r"\b(?:abre|abra|abrir|abran|enciende|encienda|encender|prende|prenda|"
            r"activa|active|activar|acciona|accione|accionar|arranca|arranque)\b"
        )
        equipment = r"\b(?:valvulas?|bombas?|riego|aspersor(?:es)?|goteo|electrovalvulas?)\b"
        if re.search(verbs + r"[^.?!]{0,30}" + equipment, text):
            return True
        return bool(re.search(r"\briega(?:lo|la|los|las)?\s+(?:por\s+mi|tu|ya|ahora)\b", text))

    @staticmethod
    def _unknown_crop(text: str) -> str | None:
        match = re.search(
            r"\b(?:cultivo|siembra|plantacion|plantio|sembradio)\s+de\s+([a-zn]+)"
            r"|\btengo\s+(?:un\s+|una\s+|unos\s+|unas\s+|mis?\s+)?([a-zn]+)\s+"
            r"(?:en|con|sembrad|plantad)",
            text,
        )
        if not match:
            return None
        word = match.group(1) or match.group(2)
        if word in NOT_A_CROP or word.rstrip("s") in NOT_A_CROP:
            return None
        return word

    def _search_number(self, pattern: str, text: str) -> float | None:
        match = re.search(pattern, text)
        return self._number(match.group(1)) if match else None

    # ------------------------------------------------------------------ reglas
    def evaluate(
        self, message: str, previous: IrrigationFacts | None = None
    ) -> RuleEvaluation:
        facts = self.extract_facts(message)
        if previous is not None:
            facts = previous.merged_with(facts)
        return self.evaluate_facts(facts)

    def evaluate_facts(self, facts: IrrigationFacts) -> RuleEvaluation:
        result = RuleEvaluation(facts=facts)

        def fire(code: str, recommendation: str) -> None:
            if code not in self.disabled_rules:
                result.fired_rules.append(code)
                result.recommendations.append(recommendation)

        if facts.actuator_request:
            # La regla de seguridad no se puede desactivar desde la gestion.
            result.fired_rules.append("R-SEG-01")
            result.recommendations.append(
                "El prototipo no acciona bombas ni valvulas; se requiere verificacion humana."
            )

        if facts.unknown_crop:
            fire(
                "R-DAT-02",
                f"El cultivo '{facts.unknown_crop}' no esta en la base de conocimiento; "
                "los umbrales son genericos y deben confirmarse para ese cultivo.",
            )

        if facts.moisture is not None:
            if not 0 <= facts.moisture <= 100:
                fire(
                    "R-DAT-01",
                    "La humedad indicada esta fuera del rango de 0 a 100 % y debe verificarse.",
                )
            elif facts.moisture < 25:
                fire(
                    "R-HUM-01",
                    "La humedad reportada es baja; conviene revisar el cultivo y considerar riego.",
                )
            elif facts.moisture > 70:
                fire(
                    "R-HUM-03",
                    "La humedad reportada es alta; conviene posponer el riego y revisar drenaje.",
                )
            else:
                fire(
                    "R-HUM-02",
                    "La humedad reportada esta en el intervalo demostrativo intermedio; "
                    "confirme el umbral del cultivo antes de regar.",
                )

        if facts.temperature is not None and facts.temperature >= 32:
            fire(
                "R-TEMP-01",
                "La temperatura es alta; priorice una inspeccion y evite regar en las horas "
                "de mayor radiacion.",
            )

        if facts.rain_expected is True:
            fire(
                "R-CLIMA-01",
                "Hay lluvia esperada; posponga la decision hasta verificar el pronostico y "
                "la humedad real.",
            )
        elif facts.rain_expected is False and facts.moisture is not None and facts.moisture < 25:
            fire(
                "R-CLIMA-02",
                "La ausencia de lluvia aumenta la prioridad de revisar la necesidad de riego.",
            )

        if facts.soil == "arenoso" and facts.moisture is not None and facts.moisture < 35:
            fire(
                "R-SUELO-01",
                "El suelo arenoso retiene menos agua; use riegos controlados y compruebe la "
                "humedad con mayor frecuencia.",
            )

        if facts.crop is None and facts.unknown_crop is None:
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
