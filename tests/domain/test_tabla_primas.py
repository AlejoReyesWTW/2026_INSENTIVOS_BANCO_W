"""Tests para src/domain/tabla_primas.py."""

from dataclasses import FrozenInstanceError

import pytest

from src.domain.tabla_primas import Prima, TablaPrimas


@pytest.fixture
def tabla_ejemplo() -> TablaPrimas:
    """Tabla de 4 primas (la del Config.json v1.1)."""
    return TablaPrimas(
        [
            Prima(valor=2414, cajero=137, subgerente=34),
            Prima(valor=5072, cajero=290, subgerente=72),
            Prima(valor=6644, cajero=378, subgerente=95),
            Prima(valor=11597, cajero=658, subgerente=164),
        ]
    )


@pytest.fixture
def tabla_vacia() -> TablaPrimas:
    """Tabla sin primas (caso borde)."""
    return TablaPrimas([])


class TestPrima:
    """Tests del dataclass Prima."""

    def test_crear_prima(self):
        """Prima se crea con valor, cajero y subgerente."""
        p = Prima(valor=2414, cajero=137, subgerente=34)
        assert p.valor == 2414
        assert p.cajero == 137
        assert p.subgerente == 34

    def test_prima_es_inmutable(self):
        """Prima es frozen."""
        p = Prima(valor=2414, cajero=137, subgerente=34)
        with pytest.raises(FrozenInstanceError):
            p.valor = 9999  # type: ignore


class TestTablaPrimasFormulaCajero:
    """Tests del método formula_cajero."""

    def test_genera_si_anidada_con_4_niveles(self, tabla_ejemplo: TablaPrimas):
        """Con 4 primas, genera SI anidado de 4 niveles."""
        formula = tabla_ejemplo.formula_cajero(col_prima="G", fila=2)
        # Debe contener los 4 valores y los 4 premios de cajero.
        assert "2414" in formula
        assert "137" in formula
        assert "5072" in formula
        assert "290" in formula
        assert "6644" in formula
        assert "378" in formula
        assert "11597" in formula
        assert "658" in formula
        # Contiene referencia a fila.
        assert "$G2" in formula
        # Empieza con = y usa separador ; (Excel en español).
        assert formula.startswith("=")
        assert ";" in formula

    def test_genera_si_simple_con_1_prima(self):
        """Con 1 sola prima, genera SI simple (sin anidación)."""
        tabla = TablaPrimas([Prima(valor=1000, cajero=50, subgerente=10)])
        formula = tabla.formula_cajero(col_prima="G", fila=2)
        assert "1000" in formula
        assert "50" in formula
        # Solo 1 nivel de SI.
        assert formula.count("SI(") == 1

    def test_tabla_vacia_genera_cero(self, tabla_vacia: TablaPrimas):
        """Con tabla vacía, la fórmula es 0 (siempre)."""
        assert tabla_vacia.formula_cajero(col_prima="G", fila=2) == "0"
        assert tabla_vacia.formula_subgerente(col_prima="G", fila=2) == "0"

    def test_numero_fila_se_refleja(self, tabla_ejemplo: TablaPrimas):
        """La fila del parámetro aparece en la fórmula."""
        f2 = tabla_ejemplo.formula_cajero(col_prima="G", fila=2)
        f100 = tabla_ejemplo.formula_cajero(col_prima="G", fila=100)
        assert "$G2" in f2
        assert "$G100" in f100
        assert "$G100" not in f2
        assert "$G2" not in f100

    def test_columna_personalizada(self, tabla_ejemplo: TablaPrimas):
        """El nombre de la columna se puede parametrizar."""
        formula = tabla_ejemplo.formula_cajero(col_prima="Z", fila=5)
        assert "$Z5" in formula
        assert "$G5" not in formula


class TestTablaPrimasFormulaSubgerente:
    """Tests del método formula_subgerente."""

    def test_valores_subgerente(self, tabla_ejemplo: TablaPrimas):
        """Usa los valores de subgerente (34, 72, 95, 164), no de cajero."""
        formula = tabla_ejemplo.formula_subgerente(col_prima="G", fila=2)
        assert "34" in formula
        assert "72" in formula
        assert "95" in formula
        assert "164" in formula
        # No debe tener los valores de cajero (137, 290, 378, 658).
        assert "137" not in formula
        assert "290" not in formula

    def test_misma_estructura_que_cajero(self, tabla_ejemplo: TablaPrimas):
        """La estructura (anidamiento) es idéntica a la del cajero."""
        cajero = tabla_ejemplo.formula_cajero(col_prima="G", fila=2)
        subgerente = tabla_ejemplo.formula_subgerente(col_prima="G", fila=2)
        # Misma cantidad de SI(.
        assert cajero.count("SI(") == subgerente.count("SI(")
