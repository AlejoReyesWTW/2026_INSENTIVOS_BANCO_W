"""Tests para src/infrastructure/config_loader.py."""

import json
from pathlib import Path

import pytest

from src.domain.errores import ConfiguracionInvalidaError
from src.infrastructure.config_loader import ConfigLoader


@pytest.fixture
def config_valida_temporal(tmp_path: Path) -> Path:
    """Crea un Config.json temporal válido en tmp_path."""
    cfg = {
        "_meta": {"version": "1.1"},
        "estructuras_requeridas": {
            "Soy Prevenido": {
                "hojas": {
                    "Ventas": ["CODIGO_AGENCIA", "NOMBRE_AGENCIA", "VALOR_PRIMA"],
                },
            },
            "Base Banco Completa SS": {
                "hojas": {
                    "Hoja1": ["CEDULA", "COLABORADOR", "CARGO"],
                },
            },
        },
        "tabla_primas": [
            {"prima": 2414, "cajero": 137, "subgerente": 34},
            {"prima": 5072, "cajero": 290, "subgerente": 72},
            {"prima": 6644, "cajero": 378, "subgerente": 95},
            {"prima": 11597, "cajero": 658, "subgerente": 164},
        ],
        "filtros_cargo": {
            "subgerente_oficina": "SUBGERENTE DE OFICINA",
            "red_agencias": [
                "CAJERO(A) AUXILIAR",
                "CAJERO(A) PRINCIPAL",
                "SUBGERENTE DE OFICINA",
                "AUXILIAR OPERATIVO",
                "AUXILIAR OPERATIVO DE PLANTA",
                "CAJERO(A) PRINCIPAL  DE PLANTA",
            ],
        },
    }
    ruta = tmp_path / "Configuracion.json"
    ruta.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


@pytest.fixture
def config_sin_estructuras(tmp_path: Path) -> Path:
    """Crea un Config.json sin la clave estructuras_requeridas."""
    cfg = {"_meta": {}, "tabla_primas": []}
    ruta = tmp_path / "Configuracion.json"
    ruta.write_text(json.dumps(cfg), encoding="utf-8")
    return ruta


@pytest.fixture
def config_json_invalido(tmp_path: Path) -> Path:
    """Crea un archivo JSON inválido."""
    ruta = tmp_path / "Configuracion.json"
    ruta.write_text("{ esto no es json valido", encoding="utf-8")
    return ruta


class TestConfigLoaderInit:
    """Tests del constructor y carga del JSON."""

    def test_carga_archivo_valido(self, config_valida_temporal: Path):
        """Carga correctamente un Config.json válido."""
        loader = ConfigLoader(config_valida_temporal)
        assert loader.ruta == config_valida_temporal

    def test_archivo_inexistente_lanza_error(self, tmp_path: Path):
        """Si el archivo no existe, lanza ConfiguracionInvalidaError."""
        with pytest.raises(ConfiguracionInvalidaError) as exc:
            ConfigLoader(tmp_path / "no_existe.json")
        assert "no existe" in str(exc.value).lower() or "no se encontr" in str(exc.value).lower()

    def test_json_invalido_lanza_error(self, config_json_invalido: Path):
        """Si el JSON es inválido, lanza ConfiguracionInvalidaError."""
        with pytest.raises(ConfiguracionInvalidaError) as exc:
            ConfigLoader(config_json_invalido)
        assert "json" in str(exc.value).lower() or "formato" in str(exc.value).lower()

    def test_sin_estructuras_lanza_error(self, config_sin_estructuras: Path):
        """Si no tiene 'estructuras_requeridas', lanza error."""
        with pytest.raises(ConfiguracionInvalidaError) as exc:
            ConfigLoader(config_sin_estructuras)
        assert "estructuras_requeridas" in str(exc.value)


class TestConfigLoaderEstructuras:
    """Tests del método cargar_estructuras."""

    def test_devuelve_dict_con_tipos_de_insumo(self, config_valida_temporal: Path):
        """cargar_estructuras devuelve dict con todos los tipos."""
        loader = ConfigLoader(config_valida_temporal)
        estructuras = loader.cargar_estructuras()
        assert "Soy Prevenido" in estructuras
        assert "Base Banco Completa SS" in estructuras
        assert "Ventas" in estructuras["Soy Prevenido"]["hojas"]

    def test_estructura_incluye_hojas_y_columnas(self, config_valida_temporal: Path):
        """La estructura tiene 'hojas' con sus columnas."""
        loader = ConfigLoader(config_valida_temporal)
        estructuras = loader.cargar_estructuras()
        cols_ventas = estructuras["Soy Prevenido"]["hojas"]["Ventas"]
        assert "CODIGO_AGENCIA" in cols_ventas
        assert "VALOR_PRIMA" in cols_ventas

    def test_estructura_incluye_fila_encabezado(self, config_valida_temporal: Path):
        """Si el tipo tiene fila_encabezado, se preserva."""
        cfg = json.loads(config_valida_temporal.read_text(encoding="utf-8"))
        cfg["estructuras_requeridas"]["Formato"] = {
            "fila_encabezado": 3,
            "hojas": {"Hoja1": ["CEDULA"]},
        }
        config_valida_temporal.write_text(json.dumps(cfg), encoding="utf-8")
        loader = ConfigLoader(config_valida_temporal)
        estructuras = loader.cargar_estructuras()
        assert estructuras["Formato"]["fila_encabezado"] == 3


class TestConfigLoaderTablaPrimas:
    """Tests del método cargar_tabla_primas."""

    def test_carga_tabla_con_4_primas(self, config_valida_temporal: Path):
        """Carga la tabla de primas con 4 entradas."""
        loader = ConfigLoader(config_valida_temporal)
        tabla = loader.cargar_tabla_primas()
        assert len(tabla.primas) == 4
        assert tabla.primas[0].valor == 2414
        assert tabla.primas[0].cajero == 137
        assert tabla.primas[3].valor == 11597

    def test_orden_de_primas_se_preserva(self, config_valida_temporal: Path):
        """Las primas se cargan en el orden del JSON."""
        loader = ConfigLoader(config_valida_temporal)
        tabla = loader.cargar_tabla_primas()
        valores = [p.valor for p in tabla.primas]
        assert valores == [2414, 5072, 6644, 11597]

    def test_tabla_vacia_si_no_hay_seccion(self, tmp_path: Path):
        """Si no hay tabla_primas en el JSON, retorna tabla vacía."""
        cfg = {"_meta": {}, "estructuras_requeridas": {}}
        ruta = tmp_path / "Configuracion.json"
        ruta.write_text(json.dumps(cfg), encoding="utf-8")
        loader = ConfigLoader(ruta)
        tabla = loader.cargar_tabla_primas()
        assert len(tabla.primas) == 0


class TestConfigLoaderFiltrosCargo:
    """Tests del método cargar_filtros_cargo."""

    def test_carga_filtro_subgerente_oficina(self, config_valida_temporal: Path):
        """Carga el filtro de subgerente de oficina."""
        loader = ConfigLoader(config_valida_temporal)
        filtros = loader.cargar_filtros_cargo()
        assert filtros.subgerente_oficina == "SUBGERENTE DE OFICINA"

    def test_carga_lista_red_agencias(self, config_valida_temporal: Path):
        """Carga la lista de cargos para red de agencias."""
        loader = ConfigLoader(config_valida_temporal)
        filtros = loader.cargar_filtros_cargo()
        assert len(filtros.red_agencias) == 6
        assert "CAJERO(A) AUXILIAR" in filtros.red_agencias
        assert "SUBGERENTE DE OFICINA" in filtros.red_agencias