"""Tests para src/domain/insumo.py."""

import pytest

from src.domain.errores import TipoInsumoDesconocidoError
from src.domain.insumo import TipoInsumo, validar_tipo


class TestTipoInsumo:
    """Tests del enum TipoInsumo."""

    def test_enum_tiene_los_6_tipos(self):
        """El enum define los 6 tipos de insumos esperados."""
        tipos = [t.value for t in TipoInsumo]
        assert "Directorio Nacional" in tipos
        assert "Formato novedades subgerente oficina para seguros" in tipos
        assert "Base Temporal Completa SS" in tipos
        assert "Base Banco Completa SS" in tipos
        # Acepta tanto guion normal como en-dash.
        assert any("Base Seguros" in t for t in tipos)
        assert "Soy Prevenido" in tipos
        assert len(tipos) == 6


class TestValidarTipo:
    """Tests de la función validar_tipo."""

    @pytest.mark.parametrize(
        "nombre_esperado",
        [
            "Directorio Nacional",
            "Formato novedades subgerente oficina para seguros",
            "Base Temporal Completa SS",
            "Base Banco Completa SS",
            "Base Seguros – Actualizada",
            "Base Seguros - Actualizada",
            "Soy Prevenido",
        ],
    )
    def test_nombres_validos_se_mapean(self, nombre_esperado):
        """Cada nombre del Config.json se mapea a un TipoInsumo."""
        resultado = validar_tipo(nombre_esperado)
        assert isinstance(resultado, TipoInsumo)

    def test_nombre_desconocido_lanza_error(self):
        """Un nombre que no está en el enum lanza TipoInsumoDesconocidoError."""
        with pytest.raises(TipoInsumoDesconocidoError) as exc:
            validar_tipo("Archivo Inventado")
        assert "Archivo Inventado" in str(exc.value)

    def test_nombre_vacio_lanza_error(self):
        """Un nombre vacío lanza error."""
        with pytest.raises(TipoInsumoDesconocidoError):
            validar_tipo("")

    def test_round_trip(self):
        """El value de cada enum se puede usar como nombre válido."""
        for tipo in TipoInsumo:
            assert validar_tipo(tipo.value) == tipo