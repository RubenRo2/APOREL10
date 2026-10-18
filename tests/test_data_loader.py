"""Pruebas unitarias para el módulo data_loader"""

from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from aporel10.data_loader import ErrorImportacionDatos, cargar_datos

# --- 1. Pruebas de formatos soportados y lectura válida ---

def test_importa_csv_valido(tmp_path: Path):
    """Comprueba lectura de CSV, cabeceras en primera fila y tipos numéricos."""
    path = tmp_path / "datos.csv"
    pd.DataFrame({"x": [1.5, 2.5], "y": [10.0, 20.0], "cat": ["A", "B"]}).to_csv(
        path, index=False
    )
    
    datos = cargar_datos(path)
    
    assert len(datos) == 2
    assert list(datos.columns) == ["x", "y", "cat"]
    assert pd.api.types.is_numeric_dtype(datos["x"])
    assert pd.api.types.is_numeric_dtype(datos["y"])
    
    
def test_importa_excel_xlsx_valido(tmp_path: Path):
    """Comprueba lectura de Excel (.xlsx) y tipos numéricos."""
    path = tmp_path / "datos.xlsx"
    pd.DataFrame({"altura": [170, 185], "peso": [65.0, 82.5]}).to_excel(
        path, index=False
    )
    
    datos = cargar_datos(path)
    
    assert len(datos) == 2
    assert list(datos.columns) == ["altura", "peso"]
    assert pd.api.types.is_numeric_dtype(datos["altura"])
    assert pd.api.types.is_numeric_dtype(datos["peso"])
    
    
def test_importa_sqlite_valido(tmp_path: Path):
    """Comprueba detección automática de tabla única y tipos en SQLite."""
    path = tmp_path / "datos.db"
    with sqlite3.connect(path) as conexion:
        conexion.execute("CREATE TABLE prueba (id INTEGER, valor REAL);")
        conexion.execute("INSERT INTO prueba VALUES (1, 121), (2, 122);")
        conexion.commit
    
    datos = cargar_datos(path)
    
    assert len(datos) == 2
    assert list(datos.columns) == ["id", "valor"]
    assert pd.api.types.is_numeric_dtype(datos["id"])
    assert pd.api.types.is_numeric_dtype(datos["valor"])
    
    
def test_importa_ruta_con_espacios_tildes_y_enye(tmp_path: Path):
    """Comprueba soporte para rutas complejas y caracteres especiales."""
    carpeta = tmp_path / "carpeta con espacios y letra ñ"
    carpeta.mkdir()
    path = carpeta / "regresión_diseño.csv"
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_csv(path, index=False)

    datos = cargar_datos(path)
    assert len(datos) == 2
    
    
# --- 2. Pruebas de cada caso de error requerido ---

def test_error_archivo_no_existe(tmp_path: Path):
    """Error: El archivo no existe."""
    ruta_fantasma = tmp_path / "no_existo.csv"

    with pytest.raises(ErrorImportacionDatos, match="no existe o no es válido"):
        cargar_datos(ruta_fantasma)


def test_error_extension_no_soportada(tmp_path: Path):
    """Error: La extensión del archivo no está soportada."""
    path = tmp_path / "datos.json"
    path.write_text('{"a": 1}', encoding="utf-8")

    with pytest.raises(ErrorImportacionDatos, match="no soportada"):
        cargar_datos(path)


def test_error_archivo_vacio_en_disco(tmp_path: Path):
    """Error: El archivo no contiene datos (0 bytes)."""
    path = tmp_path / "vacio.csv"
    path.touch()

    with pytest.raises(ErrorImportacionDatos, match="está vacío y no contiene datos"):
        cargar_datos(path)
        
        
def test_error_archivo_sin_filas_de_datos(tmp_path: Path):
    """Error: El archivo contiene solo cabeceras pero ningún registro de datos."""
    path = tmp_path / "solo_cabeceras.csv"
    path.write_text("columna1,columna2\n", encoding="utf-8")

    with pytest.raises(ErrorImportacionDatos, match="no contiene datos"):
        cargar_datos(path)


def test_error_archivo_danado_o_contenido_incompatible(tmp_path: Path):
    """Error: El archivo está dañado o su contenido no corresponde a su extensión."""
    path = tmp_path / "corrupto.xlsx"
    path.write_bytes(b"texto plano que no es un binario valido de excel")

    with pytest.raises(ErrorImportacionDatos, match="dañado o su contenido no corresponde"):
        cargar_datos(path)
        
        
def test_error_sqlite_sin_ninguna_tabla(tmp_path: Path):
    """Error: La base de datos SQLite no contiene ninguna tabla."""
    ruta = tmp_path / "sin_tablas.sqlite"
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("VACUUM;")

    with pytest.raises(ErrorImportacionDatos, match="no contiene ninguna tabla"):
        cargar_datos(ruta)


def test_error_sqlite_multiples_tablas(tmp_path: Path):
    """Error: La base de datos SQLite contiene más de una tabla."""
    path = tmp_path / "dos_tablas.db"
    with sqlite3.connect(path) as conexion:
        conexion.execute("CREATE TABLE t1 (x INTEGER);")
        conexion.execute("CREATE TABLE t2 (y INTEGER);")
        conexion.commit()

    with pytest.raises(ErrorImportacionDatos, match="Solo se admite una única tabla"):
        cargar_datos(path)