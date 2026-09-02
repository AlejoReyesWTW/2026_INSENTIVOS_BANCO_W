"""Tests para src/domain/formulas.py."""

from src.domain.formulas import formula_buscarx, formula_replica


class TestFormulaBuscarx:
    """Tests de la función formula_buscarx."""

    def test_formula_basica(self):
        """Genera fórmula BUSCARX con la sintaxis correcta."""
        f = formula_buscarx(
            valor_ref="I2",
            hoja_destino="Base red agencias",
            col_busqueda="A",
            col_retorno="C",
        )
        # Empieza con =.
        assert f.startswith("=")
        # Contiene BUSCARX.
        assert "BUSCARX(" in f
        # Contiene la referencia al valor buscado.
        assert "I2" in f
        # Contiene la hoja destino entre comillas simples.
        assert "'Base red agencias'!" in f
        # Contiene las columnas A:A y C:C.
        assert "A:A" in f
        assert "C:C" in f
        # Termina con ;1;0 (sin match → 1, modo exacto).
        assert f.endswith(";1;0)")
        # Usa separador ; (Excel español).
        assert ";" in f

    def test_formula_con_hoja_con_espacios(self):
        """Hojas con espacios se encierran en comillas simples."""
        f = formula_buscarx(
            valor_ref="N5",
            hoja_destino="Base subgerentes",
            col_busqueda="H",
            col_retorno="A",
        )
        assert "'Base subgerentes'!" in f

    def test_formula_sin_espacios_no_necesita_comillas(self):
        """Hojas sin espacios igual se encierran en comillas simples (sintaxis segura)."""
        f = formula_buscarx(
            valor_ref="X2",
            hoja_destino="Ventas",
            col_busqueda="A",
            col_retorno="B",
        )
        assert "'Ventas'!" in f

    def test_valor_ref_puede_ser_structured_reference(self):
        """valor_ref acepta referencias tipo @I:I (tablas Excel)."""
        f = formula_buscarx(
            valor_ref="@I:I",
            hoja_destino="Base red agencias",
            col_busqueda="A",
            col_retorno="C",
        )
        assert "@I:I" in f

    def test_distintas_columnas(self):
        """Distintas combinaciones de columnas producen fórmulas distintas."""
        f1 = formula_buscarx("I2", "Hoja", "A", "C")
        f2 = formula_buscarx("I2", "Hoja", "B", "D")
        assert f1 != f2
        assert "A:A" in f1
        assert "B:B" in f2
        assert "C:C" in f1
        assert "D:D" in f2


class TestFormulaReplica:
    """Tests de la función formula_replica."""

    def test_replica_simple(self):
        """Genera =<ref> (réplica de otra celda)."""
        f = formula_replica("P2")
        assert f == "=P2"

    def test_replica_con_otro_nombre(self):
        """Acepta cualquier referencia de celda."""
        assert formula_replica("Q5") == "=Q5"
        assert formula_replica("A1") == "=A1"
        assert formula_replica("Z99") == "=Z99"


class TestEstructuraFormula:
    """Tests adicionales de la estructura de las fórmulas generadas."""

    def test_buscarx_tiene_5_argumentos(self):
        """BUSCARX tiene 5 argumentos: valor, matriz_buscar, matriz_retornar, si_no_encontrado, modo."""
        f = formula_buscarx("I2", "Hoja", "A", "C")
        # Cuenta las comas + 1 = argumentos. Usamos ; porque es Excel español.
        argumentos = f.split(";")
        # =BUSCARX(I2 ; 'Hoja'!A:A ; 'Hoja'!C:C ; 1 ; 0)
        # 5 argumentos después de quitar el "=" y "BUSCARX(".
        assert len(argumentos) == 5

    def test_buscarx_no_encontrado_es_1(self):
        """El 4° argumento (si_no_encontrado) es 1 (identifica fallos)."""
        f = formula_buscarx("I2", "Hoja", "A", "C")
        argumentos = f.split(";")
        assert argumentos[3] == "1"

    def test_buscarx_modo_es_0(self):
        """El 5° argumento (modo) es 0 (coincidencia exacta)."""
        f = formula_buscarx("I2", "Hoja", "A", "C")
        argumentos = f.split(";")
        assert argumentos[4].rstrip(")") == "0"
