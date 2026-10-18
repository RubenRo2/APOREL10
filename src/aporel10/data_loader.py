"""Módulo de importación de datos desde archivos CSV, Excel y SQLite."""

from pathlib import Path
import sqlite3

import pandas as pd

class ErrorImportacionDatos(Exception):
    """Excepción para errores ocurridos durante la importación de datasets."""
    
    pass


def cargar_datos(file_path: str | Path) -> pd.DataFrame:
    """Importa datos desde un archivo CSV, Excel o base de datos SQLite.

    Determina el formato según la extensión del archivo, infiere los tipos
    numéricos de las columnas y detecta automáticamente la tabla existente
    en bases de datos SQLite.

    Args:
        ruta_archivo (str | Path): Ruta relativa o absoluta hacia el archivo
            de datos. Soporta rutas con espacios, tildes y caracteres como la ñ.

    Returns:
        pd.DataFrame: Conjunto de datos cargado en memoria con encabezados
            en la primera fila.

    Raises:
        ErrorImportacionDatos: Si el archivo no existe o no es válido,
            si la extensión no está soportada, si el archivo está vacío (0 bytes
            o sin registros), si está dañado o no coincide con su formato, o si
            la base de datos SQLite no contiene exactamente una tabla.
    """
    path = Path(file_path)
    
    # 1. El archivo no existe o no es un archivo regular
    if not path.exists() or not path.is_file():
        raise ErrorImportacionDatos(
            f"El archivo '{file_path}' no existe o no es válido."
        )
    
    # 2. El archivo está vacío en disco (0 bytes)
    if path.stat().st_size == 0:
        raise ErrorImportacionDatos(
            f"El archivo '{path.name}' está vacío y no contiene datos."
        )
    
    extension = path.suffix.lower()
    extensiones_permitidas = {".csv", ".xlsx", ".xls", ".sqlite", ".db"}
    
    # 3. Extensión no soportada
    if extension not in extensiones_permitidas:
        formatos = ", ".join(sorted(extensiones_permitidas))
        raise ErrorImportacionDatos(
            f"Extensión '{extension}' no soportada. Formas validas: {formatos}"
        )
    
    # 4. Lectura de datos según la extensión
    try:
        if extension == ".csv":
            datos = pd.read_csv(path)
            
        elif extension in {".xlsx", ".xls"}:
            datos = pd.read_excel(path)
            
        elif extension in {".sqlite", ".db"}:
            with sqlite3.connect(path) as conexion:
                cursor = conexion.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                )
                tablas = cursor.fetchall()
            
            if len(tablas) == 0:
                raise ErrorImportacionDatos(
                    f"La base de datos SQLite no contiene ninguna tabla."
                )
            
            elif len(tablas) > 1:
                raise ErrorImportacionDatos(
                    f"La base de datos SQLite contiene {len(tablas)} tablas. Solo se admite una única tabla."
                )
                
            nombre_tabla = tablas[0][0]
            
            with sqlite3.connect(path) as conexion:
                datos = pd.read_sql_query(
                    f'SELECT * FROM "{nombre_tabla}"',
                    conexion,
                )
                
    except ErrorImportacionDatos:
        raise
    
    except Exception as error:
        raise ErrorImportacionDatos(
            f"El archivo está dañado o su contenido no corresponde a su extensión. "
            f"Detalle: {error}"
        ) from error
    
    # 5. Archivo sin datos tras la lectura (ej. solo cabeceras sin filas)
    if datos.empty or len(datos.columns) == 0:
        raise ErrorImportacionDatos(
            f"El archivo '{path.name}' no contiene datos."
        )
    
    return datos