"""Tests para src/domain/mapeo.py."""

from dataclasses import FrozenInstanceError

import pytest

from src.domain.mapeo import MapeoColumnas, normalizar_header


class TestNormalizarHeader:
    """Tests de la función normalizar_header."""

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("CEDULA", "cedula"),
            ("Cédula", "cedula"),
            ("  CEDULA  ", "cedula"),
            ("CEDULA     ", "cedula"),
            ("cédula", "cedula"),
            ("Código_Agencia", "codigo agencia"),
            ("CODIGO AGENCIA", "codigo agencia"),
            ("Código de Agencia", "codigo de agencia"),
            ("USUARIO (Iniciales de 3 letras)", "usuario (iniciales de 3 letras)"),
            ("", ""),
            ("A", "a"),
        ],
    )
    def test_normaliza_headers(self, entrada, esperado):
        """Normaliza lowercase + sin acentos + strip + colapsa separadores."""
        assert normalizar_header(entrada) == esperado

    def test_acentos_diferentes_mismo_resultado(self):
        """Distintas formas de un acento producen el mismo resultado."""
        assert normalizar_header("NOMBRE_ASEGURADO") == normalizar_header("nombre asegurado")
        assert normalizar_header("VICEPRESIDENCIA") == normalizar_header("vicepresidencia")
        assert normalizar_header("PÉREZ") == normalizar_header("perez")


class TestMapeoColumnas:
    """Tests del dataclass MapeoColumnas."""

    def test_crear_mapeo(self):
        """MapeoColumnas tiene origen y destino."""
        m = MapeoColumnas(origen="CODIGO_AGENCIA", destino="CODIGO_AGENCIA")
        assert m.origen == "CODIGO_AGENCIA"
        assert m.destino == "CODIGO_AGENCIA"

    def test_mapeo_es_inmutable(self):
        """MapeoColumnas es frozen."""
        m = MapeoColumnas(origen="X", destino="Y")
        with pytest.raises(FrozenInstanceError):
            m.origen = "Z"  # type: ignore

    def test_match_por_header_normalizado(self):
        """match_normalizado compara por versión normalizada de ambos headers."""
        m = MapeoColumnas(origen="CODIGO_AGENCIA", destino="A")
        assert m.match_normalizado("codigo_agencia")
        assert m.match_normalizado("Código Agencia")
        assert m.match_normalizado("CODIGO AGENCIA")
        assert not m.match_normalizado("NOMBRE_AGENCIA")
        assert not m.match_normalizado("")
