# Informe de pruebas funcionales

Resultado de ejecutar el [plan de pruebas](plan_pruebas.md) sobre `dev` antes de la release final.

## 1. Datos de la ejecución

| Dato | Valor |
| --- | --- |
| Fecha | 26/11/2026 |
| Versión probada | `dev`, commit `0fc3c19` |
| Entorno | Windows 11 Pro, Python 3.12.14, PySide6 6.12.0, scikit-learn 1.9.1, pandas 3.0.6 |
| Pruebas unitarias | `uv run pytest`: 189 superadas |
| Datos | `housing.csv`, `housing.xlsx` y `housing.db` de `data/`; los archivos pequeños se crearon como indica cada caso |
| Ejecución | Automatizada sobre la interfaz real, sin pantalla (`QT_QPA_PLATFORM=offscreen`), siguiendo los pasos de cada caso |

**Limitaciones de la ejecución automatizada:**

- **Exploradores de Windows:** los exploradores de archivos y los mensajes se sustituyeron por la respuesta que indica cada paso (archivo elegido, **Cancelar**, **Yes** o **No**). El contenido de cada mensaje se comparó con el texto esperado.
- **Comprobaciones visuales:** que una opción se vea en gris o que el gráfico se mueva al arrastrar se comprobaron por el estado de los controles y por los límites de los ejes, no mirando la pantalla.
- **CP-36:** con el nombre `repetido.pkl` la confirmación la muestra el propio explorador de Windows, que no se puede automatizar. Se probó con `repetido`, sin extensión, y en ese caso la pide la aplicación.
- **CP-37:** se comprobó el aviso de la aplicación, no el del explorador de Windows.
- **Archivos generados:** se crearon en una carpeta temporal en lugar de `C:\pruebas_aporel10`.

El CONTRIBUTING pide que pruebe a mano la aplicación alguien que no haya implementado la historia. Por eso, antes de cerrar la release, una persona del equipo debe repetir a mano al menos CP-31, CP-36, CP-37 y CP-45 (apartado 5 del plan) y firmar la tabla del apartado 5.

## 2. Resumen

| Total | Correctos | Fallidos | No ejecutados |
| --- | --- | --- | --- |
| 45 | 43 | 2 | 0 |

Se hicieron 292 comprobaciones y fallaron 5, todas en CP-06 y CP-11. Los dos fallos tienen la misma causa (F-01).

## 3. Resultados por caso

| Caso | Título | Resultado | Observaciones |
| --- | --- | --- | --- |
| CP-01 | Cargar CSV, Excel y SQLite | Correcto | 20640 × 10 en los tres formatos; filas 1, 291 y 20640 correctas |
| CP-02 | Cancelar la carga y cambiar de archivo | Correcto | |
| CP-03 | Archivo vacío o sin filas | Correcto | |
| CP-04 | Archivo dañado o mal formado | Correcto | Los tres detalles coinciden |
| CP-05 | Extensión no admitida | Correcto | |
| CP-06 | Selección válida con una y con dos entradas | **Fallido** | F-01: al marcar la segunda entrada se desmarca la salida |
| CP-07 | Ninguna entrada seleccionada | Correcto | |
| CP-08 | Entrada no numérica | Correcto | |
| CP-09 | Salida no numérica | Correcto | |
| CP-10 | Columna de entrada bloqueada en la salida | Correcto | |
| CP-11 | Elegir la salida antes que las entradas | **Fallido** | F-01 |
| CP-12 | Validar sin datos cargados | Correcto | |
| CP-13 | Cambiar la selección tras crear un modelo | Correcto | |
| CP-14 | Separar con un 20 % y un 25,5 % de test | Correcto | 16512/4128 y 15377/5263 |
| CP-15 | Porcentajes límite admitidos: 1 y 99 | Correcto | 20434/206 y 206/20434 |
| CP-16 | Porcentajes límite rechazados: 0 y 100 | Correcto | |
| CP-17 | Porcentajes no válidos | Correcto | |
| CP-18 | Semillas límite | Correcto | |
| CP-19 | Semillas no válidas | Correcto | |
| CP-20 | La semilla hace reproducible la separación | Correcto | |
| CP-21 | Dataset con menos de 5 filas | Correcto | |
| CP-22 | Porcentajes que dejan un conjunto vacío | Correcto | |
| CP-23 | Detectar valores inexistentes | Correcto | 156 y 51 |
| CP-24 | Tratamientos de valores inexistentes | Correcto | Los cinco tratamientos coinciden en filas, fórmula, R² y predicción |
| CP-25 | Campo de constante según el tratamiento | Correcto | |
| CP-26 | Constante no válida | Correcto | |
| CP-27 | Eliminar filas deja un conjunto vacío | Correcto | |
| CP-28 | Media de una columna sin valores | Correcto | |
| CP-29 | Modelo simple con los tres formatos | Correcto | Misma fórmula y métricas con CSV, Excel y SQLite |
| CP-30 | Modelo múltiple y vistas del gráfico | Correcto | |
| CP-31 | Zoom, movimiento y vista inicial | Correcto | Pendiente de confirmar a mano |
| CP-32 | Mínimo de filas de test | Correcto | |
| CP-33 | Guardar y cargar un modelo | Correcto | Se añade `.pkl` al nombre |
| CP-34 | Guardar sin descripción | Correcto | |
| CP-35 | Cancelar el guardado y la carga | Correcto | |
| CP-36 | No sobrescribir un modelo existente | Correcto | Probado sin extensión (apartado 1); pendiente de confirmar a mano |
| CP-37 | Guardar en una carpeta inexistente | Correcto | Sale «Error al guardar el modelo» con «[Errno 2] No such file or directory» |
| CP-38 | Editar la descripción de un modelo cargado | Correcto | |
| CP-39 | Volver a los datos desde un modelo cargado | Correcto | |
| CP-40 | Archivo de modelo no válido | Correcto | |
| CP-41 | Cambios sin guardar al cargar datos | Correcto | |
| CP-42 | Predicciones válidas | Correcto | |
| CP-43 | Predicción con un modelo múltiple | Correcto | 193125.4508 |
| CP-44 | Predicciones no válidas | Correcto | |
| CP-45 | Flujo completo | Correcto | Fórmula, descripción y predicción iguales antes de guardar y después de cargar |

## 4. Fallos encontrados

### F-01. Marcar una entrada desmarca la salida elegida

- **Casos:** CP-06 (paso 2) y CP-11.
- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11).
- **Gravedad:** Media. Impide validar si la salida se elige antes que alguna entrada, aunque se puede evitar volviendo a marcar la salida.
- **Pasos para reproducirlo:** Abrir → Cargar `housing.csv`. Marca la salida `median_house_value`, marca la entrada `median_income` y pulsa **Validar variables**.
- **Resultado esperado:** `median_house_value` sigue marcada y sale «Éxito».
- **Resultado obtenido:**
  - La salida queda sin marcar, aunque el botón sigue mostrando `median…`.
  - Sale «Error de Selección» con el texto "Debe seleccionar al menos una columna de salida (target)" y **Separar datos** sigue desactivado.
  - Pasa lo mismo al añadir una segunda entrada después de haber elegido la salida.
- **Causa probable:** `SelectorColumnas.deshabilitar_opciones` (`src/aporel10/gui.py`) desmarca todas las casillas de la salida, no solo las bloqueadas. Además, solo actualiza el texto del botón si la casilla desmarcada estaba bloqueada.
- **Acción:**
  1. Crear en Taiga, dentro de esta historia, una tarea de corrección.
  2. Corregirla en una rama `fix/<numero>-salida-desmarcada`, creada desde `dev`, con una prueba unitaria que reproduzca el fallo.
  3. Repetir CP-06, CP-10 y CP-11 en la subtarea #151.

## 5. Revisión manual y cierre

Ejecución automatizada completa. Queda pendiente que una persona del equipo que no haya implementado las historias revise los casos indicados en el apartado 1.

| Caso | Ejecutado por | Fecha | Resultado |
| --- | --- | --- | --- |
| CP-31 | | | |
| CP-36 | | | |
| CP-37 | | | |
| CP-45 | | | |

Los casos fallidos se repiten tras la corrección en la subtarea #151, que cierra este informe.
