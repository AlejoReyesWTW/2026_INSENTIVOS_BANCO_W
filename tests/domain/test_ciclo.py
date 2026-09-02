"""Tests para src/domain/ciclo.py."""

from dataclasses import FrozenInstanceError

import pytest

from src.domain.ciclo import Periodo, detectar_periodo_de_filename


class TestPeriodo:
    """Tests del dataclass Periodo."""

    def test_crear_periodo_valido(self):
        """Un Periodo se crea con mes y año."""
        p = Periodo(mes="junio", anio=2026)
        assert p.mes == "junio"
        assert p.anio == 2026

    def test_periodo_es_inmutable(self):
        """Periodo es inmutable (dataclass frozen)."""
        p = Periodo(mes="junio", anio=2026)
        with pytest.raises(FrozenInstanceError):
            p.mes = "julio"  # type: ignore

    def test_periodo_igualdad(self):
        """Dos Periodos con mismos valores son iguales."""
        p1 = Periodo(mes="junio", anio=2026)
        p2 = Periodo(mes="junio", anio=2026)
        assert p1 == p2

    def test_periodo_str(self):
        """Periodo se serializa como 'MES AÑO'."""
        p = Periodo(mes="junio", anio=2026)
        assert str(p) == "junio 2026"


class TestDetectarPeriodoDeFilename:
    """Tests de la función detectar_periodo_de_filename."""

    @pytest.mark.parametrize(
        "filename,esperado_mes,esperado_anio",
        [
            ("Base incentivos junio 2026 - Soy Prevenido.xlsx", "junio", 2026),
            ("Base incentivos JUNIO 2026.xlsx", "junio", 2026),
            ("Base incentivos Jun 2026.xlsx", "junio", 2026),
            ("Base incentivos Junio.xlsx", "junio", None),
            ("Soy Prevenido enero 2025.xlsx", "enero", 2025),
            ("SOY PREVENIDO DICIEMBRE 2024.xlsx", "diciembre", 2024),
            ("archivo FEBRERO 2027.xlsx", "febrero", 2027),
            ("Base incentivos marzo.xlsx", "marzo", None),
        ],
    )
    def test_detecta_mes_y_anio(self, filename, esperado_mes, esperado_anio):
        """Detecta mes y año en distintos formatos."""
        resultado = detectar_periodo_de_filename(filename)
        assert resultado is not None
        assert resultado.mes == esperado_mes
        assert resultado.anio == esperado_anio

    def test_detecta_sin_extension(self):
        """Funciona con o sin extensión .xlsx."""
        resultado = detectar_periodo_de_filename("Base junio 2026")
        assert resultado is not None
        assert resultado.mes == "junio"
        assert resultado.anio == 2026

    def test_retorna_none_sin_mes(self):
        """Si no detecta mes, retorna None."""
        resultado = detectar_periodo_de_filename("archivo.xlsx")
        assert resultado is None

    def test_retorna_none_sin_anio(self):
        """Si no detecta año (pero sí mes), retorna Periodo con anio=None."""
        resultado = detectar_periodo_de_filename("archivo junio.xlsx")
        assert resultado is not None
        assert resultado.mes == "junio"
        assert resultado.anio is None
