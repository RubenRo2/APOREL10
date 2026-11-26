# Plan de pruebas funcionales

Pruebas manuales de APOREL10 antes de la release final, hechas desde la interfaz.

## 1. Cómo ejecutar el plan

1. Se ejecuta sobre `dev` con todas las historias integradas y `uv run pytest` en verde.
2. Cada caso lo ejecuta alguien que no haya implementado su historia (apartado 5).
3. Cada caso empieza con la aplicación cerrada y termina cerrándola. Si necesita un archivo de otro caso, lo indica en **Precondiciones**.
4. Un caso es **Correcto** si se cumple todo el resultado esperado y **Fallido** si falla algo. En los números se admite una unidad de diferencia en el último decimal.
5. Los resultados se anotan en `informe_pruebas.md`. Cada fallo genera una tarea de corrección en Taiga, dentro de esta historia, y se corrige en una rama `fix/<numero>-<descripcion>`.

**Preparación (una vez):** instala `uv` (README), ejecuta `uv sync` en la carpeta del proyecto, copia `housing.csv`, `housing.xlsx` y `housing.db` en `data/` y crea la carpeta `C:\pruebas_aporel10` para los archivos que generen los casos. Ningún archivo de datos se sube al repositorio.

**Precondiciones generales:** aplicación cerrada, datasets en `data/` y carpeta `C:\pruebas_aporel10` creada. Si un caso dice «No existe `x`», borra antes ese archivo de la carpeta.

Según el sistema, algunos mensajes muestran los botones en inglés (**Yes**/**No**).

## 2. Pasos comunes

Los pasos de los casos usan estas acciones:

| Acción | Qué hacer |
| --- | --- |
| **Abrir** | En PowerShell, desde la carpeta del proyecto, ejecuta `uv run aporel10`. |
| **Cargar `f`** | Pulsa **Cargar datos...**, entra en `data` (o en `C:\pruebas_aporel10` si el archivo se creó en el caso), elige `f` y pulsa **Abrir**. |
| **Seleccionar `e` → `s`** | En el desplegable **Entradas (Features):** marca las columnas `e` y pulsa **Esc**. En **Salida (Target):** marca `s`. Pulsa **Validar variables** y luego **OK**. |
| **Separar `p`/`s`** | Escribe `p` en **Test (%):** y `s` en **Semilla:**, pulsa **Separar datos** y luego **OK**. |
| **Crear** | Pulsa **Crear modelo** y luego **OK**. |
| **Modelo simple** | Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value` → Separar `20`/`42` → Crear. |
| **Modelo múltiple** | Igual que el modelo simple, con las entradas `housing_median_age` y `median_income`. |
| **Guardar `n`** | Pulsa **Guardar modelo**, entra en `C:\pruebas_aporel10`, escribe `n` en **Nombre**, pulsa **Guardar** y luego **OK**. |
| **Cargar modelo `n`** | Pulsa **Cargar modelo...**, entra en `C:\pruebas_aporel10`, elige `n`, pulsa **Abrir** y luego **OK**. |
| **Predecir `c`=`v`** | En **Predicción** escribe `v` en el campo `c` (si `v` está vacío, deja el campo en blanco) y pulsa **Realizar predicción**. |
| **Crear archivo `n`: líneas** | En el Bloc de notas escribe las líneas indicadas, una por renglón. Pulsa **Guardar como**, elige **Todos los archivos** y guárdalo como `C:\pruebas_aporel10\n`. |

## 3. Datos de prueba

| Archivo | Formato | Filas × columnas | Detalle |
| --- | --- | --- | --- |
| `housing.csv` | CSV separado por comas | 20640 × 10 | 1 423 529 bytes |
| `housing.xlsx` | Excel | 20640 × 10 | Hoja `housing` |
| `housing.db` | SQLite | 20640 × 10 | Tabla `california_housing_dataset` |

Los tres archivos tienen los mismos datos; según el formato, los enteros se ven con `.0` o sin él. Columnas: `longitude`, `latitude`, `housing_median_age`, `total_rooms`, `total_bedrooms`, `population`, `households`, `median_income`, `median_house_value` y `ocean_proximity`.

- `total_bedrooms` tiene **207 valores inexistentes**. Con test `20` y semilla `42`, todos caen en test. Por eso los casos de preprocesado usan la semilla `7`, que deja 156 en entrenamiento y 51 en test.
- `ocean_proximity` es de **texto**; se usa en los casos de error.
- Los archivos pequeños de los casos de error (`vacio.csv`, `cinco.csv`…) se crean en los propios pasos.
- Valores de referencia (test `20`, semilla `42`):
  - **Modelo simple:** `median_house_value = 41933.8494 * median_income + 44459.7292`; R² `0.4770`/`0.4589` y ECM `6,991,447,170.1828`/`7,091,157,771.7655` (entrenamiento/test).
  - **Modelo múltiple:** `median_house_value = 1748.5735 * housing_median_age + 43342.2840 * median_income - 11029.7493`; R² `0.5128`/`0.4941` y ECM `6,513,066,873.6164`/`6,629,874,283.0482`.

## 4. Índice de casos

| Caso | Título | Tipo |
| --- | --- | --- |
| CP-01 | Cargar CSV, Excel y SQLite | Válido |
| CP-02 | Cancelar la carga y cambiar de archivo | Válido |
| CP-03 | Archivo vacío o sin filas | Error |
| CP-04 | Archivo dañado o mal formado | Error |
| CP-05 | Extensión no admitida | Error |
| CP-06 | Selección válida con una y con dos entradas | Válido |
| CP-07 | Ninguna entrada seleccionada | Error |
| CP-08 | Entrada no numérica | Error |
| CP-09 | Salida no numérica | Error |
| CP-10 | Columna de entrada bloqueada en la salida | Error |
| CP-11 | Elegir la salida antes que las entradas | Válido |
| CP-12 | Validar sin datos cargados | Error |
| CP-13 | Cambiar la selección tras crear un modelo | Válido |
| CP-14 | Separar con un 20 % y un 25,5 % de test | Válido |
| CP-15 | Porcentajes límite admitidos: 1 y 99 | Límite |
| CP-16 | Porcentajes límite rechazados: 0 y 100 | Límite (error) |
| CP-17 | Porcentajes no válidos | Error |
| CP-18 | Semillas límite | Límite |
| CP-19 | Semillas no válidas | Error |
| CP-20 | La semilla hace reproducible la separación | Válido |
| CP-21 | Dataset con menos de 5 filas | Límite (error) |
| CP-22 | Porcentajes que dejan un conjunto vacío | Límite (error) |
| CP-23 | Detectar valores inexistentes | Válido |
| CP-24 | Tratamientos de valores inexistentes | Válido |
| CP-25 | Campo de constante según el tratamiento | Válido |
| CP-26 | Constante no válida | Error |
| CP-27 | Eliminar filas deja un conjunto vacío | Error |
| CP-28 | Media de una columna sin valores | Error |
| CP-29 | Modelo simple con los tres formatos | Válido |
| CP-30 | Modelo múltiple y vistas del gráfico | Válido |
| CP-31 | Zoom, movimiento y vista inicial | Válido |
| CP-32 | Mínimo de filas de test | Límite |
| CP-33 | Guardar y cargar un modelo | Válido |
| CP-34 | Guardar sin descripción | Válido |
| CP-35 | Cancelar el guardado y la carga | Válido |
| CP-36 | No sobrescribir un modelo existente | Válido |
| CP-37 | Guardar en una carpeta inexistente | Error |
| CP-38 | Editar la descripción de un modelo cargado | Válido |
| CP-39 | Volver a los datos desde un modelo cargado | Válido |
| CP-40 | Archivo de modelo no válido | Error |
| CP-41 | Cambios sin guardar al cargar datos | Válido |
| CP-42 | Predicciones válidas | Válido / Límite |
| CP-43 | Predicción con un modelo múltiple | Válido / Error |
| CP-44 | Predicciones no válidas | Error |
| CP-45 | Flujo completo | Válido |

## 5. Trazabilidad

Los autores salen del historial de Git y sirven para elegir quién ejecuta cada caso; el equipo debe confirmarlos.

| Historia | Funcionalidad | Casos | Implementada por |
| --- | --- | --- | --- |
| [#10](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/10) | Importación de datos | CP-01 a CP-05, CP-45 | RubenRo2 y jotabepe7 |
| [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14) | Lectura de datos en la interfaz | CP-01 a CP-05, CP-39, CP-41, CP-45 | jotabepe7 |
| [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11) | Selección de columnas | CP-06 a CP-13, CP-45 | RubenRo2 |
| [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41) | Separación train/test | CP-14 a CP-22, CP-45 | SergioVazquez0 |
| [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26) | Preprocesado | CP-14, CP-23 a CP-28, CP-45 | IagoUDC |
| [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16) | Creación y evaluación del modelo | CP-13, CP-20, CP-24, CP-29 a CP-32, CP-45 | IagoUDC y SergioVazquez0 |
| Descripción del modelo (tareas [#137](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/137) y [#138](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/138)) | Descripción | CP-33, CP-34, CP-36, CP-38, CP-41, CP-45 | SergioVazquez0 |
| [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21) | Guardado del modelo | CP-33 a CP-38, CP-41, CP-45 | RubenRo2 e IagoUDC |
| [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24) | Carga del modelo | CP-33 a CP-36, CP-38 a CP-40, CP-45 | IagoUDC y jotabepe7 |
| Predicciones (pendiente de numerar) | Predicción | CP-24, CP-42 a CP-45 | jotabepe7 e IagoUDC |
| [#37](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/37) | Mejora de la interfaz (lupa) | CP-31 | RubenRo2 |

## 6. Casos de prueba

### Carga de datos

#### CP-01. Cargar CSV, Excel y SQLite

- **Historia:** [#10](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/10), [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar que se cargan los tres formatos y que la tabla muestra todos los datos.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`, `housing.xlsx`, `housing.db`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv`.
  2. Mira los encabezados y las filas 1, 291 y 20640.
  3. Repite los pasos 1 y 2 con `housing.xlsx` y `housing.db`.
- **Resultado esperado:**
  - No sale ningún error y junto al botón aparece la ruta del archivo.
  - La tabla tiene las 10 columnas del apartado 3 y 20640 filas.
  - Fila 1: `-122.23 · 37.88 · 41 · 880 · 129.0 · 322 · 126 · 8.3252 · 452600 · NEAR BAY`. Según el formato, los enteros se ven con `.0` o sin él.
  - Fila 291: celda vacía en `total_bedrooms`. Fila 20640: `INLAND` en `ocean_proximity`.

#### CP-02. Cancelar la carga y cambiar de archivo

- **Historia:** [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar que cancelar no cambia nada y que cargar otro archivo reinicia la selección.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`, `housing.xlsx`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value` → Separar `20`/`42`.
  2. Pulsa **Cargar datos...** y luego **Cancelar**.
  3. Cargar `housing.xlsx`.
- **Resultado esperado:**
  - Tras el paso 2 no sale ningún mensaje y se mantienen la tabla y la separación.
  - Tras el paso 3, la ruta termina en `housing.xlsx`, las entradas muestran **Seleccionar...**, aparece «Datos sin separar» y **Crear modelo** está desactivado.

#### CP-03. Archivo vacío o sin filas

- **Historia:** [#10](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/10), [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar el aviso al cargar un archivo sin datos.
- **Precondiciones:** Generales.
- **Datos de prueba:** `vacio.csv` (sin contenido) y `cabecera.csv` (solo `x,y`).
- **Pasos:**
  1. Crear archivo `vacio.csv`: sin ninguna línea. Crear archivo `cabecera.csv`: `x,y`.
  2. Abrir → Cargar `vacio.csv` → **OK**.
  3. Cargar `cabecera.csv` → **OK**.
- **Resultado esperado:**
  - Paso 2: sale «Error al cargar los datos» con el texto "El archivo 'vacio.csv' está vacío y no contiene datos."
  - Paso 3: sale «Error al cargar los datos» con el texto "El archivo 'cabecera.csv' no contiene datos."
  - En los dos casos aparece «Ningún archivo cargado», la tabla está vacía y las entradas están desactivadas.

#### CP-04. Archivo dañado o mal formado

- **Historia:** [#10](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/10), [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar el aviso cuando el contenido de un archivo no corresponde a su extensión o está mal formado.
- **Precondiciones:** Generales.
- **Datos de prueba:** `falso.xlsx` (`hola`), `falso.db` (`hola mundo, esto no es una base`), `desigual.csv` (`a,b` / `1,2` / `1,2,3,4`).
- **Pasos:**
  1. Crea los tres archivos.
  2. Abrir. Carga cada archivo y pulsa **OK** en el aviso.
- **Resultado esperado:**
  - Cada vez sale «Error al cargar los datos» con un texto que empieza por "El archivo está dañado o su contenido no corresponde a su extensión. Detalle:", seguido de:
    - `falso.xlsx`: "Excel file format cannot be determined, you must specify an engine manually."
    - `falso.db`: "file is not a database".
    - `desigual.csv`: "Error tokenizing data. C error: Expected 2 fields in line 3, saw 4".
  - La aplicación sigue abierta y aparece «Ningún archivo cargado».

#### CP-05. Extensión no admitida

- **Historia:** [#10](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/10), [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar que se rechaza un archivo que no es CSV, Excel ni SQLite.
- **Precondiciones:** Generales.
- **Datos de prueba:** `datos.txt` (`x,y` / `1,2`).
- **Pasos:**
  1. Crea el archivo `datos.txt`.
  2. Abrir. Pulsa **Cargar datos...**, escribe en **Nombre** `C:\pruebas_aporel10\datos.txt`, pulsa **Abrir** y luego **OK**.
- **Resultado esperado:**
  - Sale «Error al cargar los datos» con el texto "Extensión '.txt' no soportada. Formas validas: .csv, .db, .sqlite, .xls, .xlsx".
  - Aparece «Ningún archivo cargado».

### Selección de columnas

#### CP-06. Selección válida con una y con dos entradas

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que se aceptan entradas y salida numéricas.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; primero `median_income` → `median_house_value`; después `housing_median_age` y `median_income` → `median_house_value`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Marca también `housing_median_age` en las entradas, comprueba que la salida sigue siendo `median_house_value`, pulsa **Validar variables** y luego **OK**.
- **Resultado esperado:**
  - Las dos veces sale «Éxito» con el texto "Las variables seleccionadas son válidas y están listas para entrenar." y **Separar datos** se activa.
  - Con dos entradas, el desplegable muestra `2 de 10 columnas`.

#### CP-07. Ninguna entrada seleccionada

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que se exige al menos una entrada.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; sin entradas; salida `median_house_value`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv`.
  2. En **Salida (Target):** marca `median_house_value`, pulsa **Validar variables** y luego **OK**.
- **Resultado esperado:**
  - Sale «Error de Selección» con el texto "Debe seleccionar al menos una columna de entrada (feature)".
  - **Separar datos** sigue desactivado.

#### CP-08. Entrada no numérica

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que se rechaza una entrada de texto.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; `ocean_proximity` → `median_house_value`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `ocean_proximity` → `median_house_value`.
- **Resultado esperado:**
  - Sale «Error de Selección» con el texto "Solo se admiten columnas numéricas para regresión lineal/multiple. Columnas inválidas: ocean_proximity".
  - **Separar datos** sigue desactivado.

#### CP-09. Salida no numérica

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que se rechaza una salida de texto.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; `median_income` → `ocean_proximity`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `ocean_proximity`.
- **Resultado esperado:**
  - Sale «Error de Selección» con el mismo texto que en CP-08.
  - **Separar datos** sigue desactivado.

#### CP-10. Columna de entrada bloqueada en la salida

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que una columna marcada como entrada no se puede usar como salida y que vuelve a estar disponible al desmarcarla.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; `median_income` como entrada y como salida.
- **Pasos:**
  1. Abrir → Cargar `housing.csv`. Marca `median_income` en las entradas y pulsa **Esc**.
  2. En **Salida (Target):** intenta marcar `median_income` y pulsa **Esc**.
  3. Desmarca `median_income` en las entradas, pulsa **Esc** y vuelve a intentar marcarla en la salida.
- **Resultado esperado:**
  - En el paso 2, `median_income` sale en gris en la salida y no se puede marcar.
  - En el paso 3 vuelve a verse normal y se puede marcar.

#### CP-11. Elegir la salida antes que las entradas

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar que marcar una entrada no anula una salida distinta que ya estaba elegida.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; primero la salida `median_house_value`, después la entrada `median_income`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv`. En **Salida (Target):** marca `median_house_value` y pulsa **Esc**.
  2. Marca `median_income` en las entradas y pulsa **Esc**.
  3. Abre la salida, mira qué columna está marcada y pulsa **Esc**. Pulsa **Validar variables**.
- **Resultado esperado:**
  - `median_house_value` sigue marcada en la salida.
  - Sale «Éxito».

#### CP-12. Validar sin datos cargados

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11)
- **Objetivo:** Comprobar el aviso si se valida sin haber cargado datos.
- **Precondiciones:** Generales.
- **Datos de prueba:** Ninguno.
- **Pasos:**
  1. Abrir. Pulsa **Validar variables** y luego **OK**.
- **Resultado esperado:**
  - Sale «Atención» con el texto "Primero debes cargar un archivo de datos."
  - **Separar datos** sigue desactivado.

#### CP-13. Cambiar la selección tras crear un modelo

- **Historia:** [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11), [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar que cambiar las variables invalida la separación y el modelo.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple; nueva salida `longitude`.
- **Pasos:**
  1. Modelo simple.
  2. En **Salida (Target):** marca `longitude`.
- **Resultado esperado:**
  - Aparece «Datos sin separar», y **Separar datos**, **Crear modelo** y **Guardar modelo** se desactivan.
  - Aparece «No se ha creado ningún modelo.» y las métricas muestran «—».

### Separación en entrenamiento y test

#### CP-14. Separar con un 20 % y un 25,5 % de test

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41), [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar la separación con un porcentaje entero y con uno decimal.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; `median_income` → `median_house_value`; test `20` y `25,5`; semilla `42`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Escribe `20` en **Test (%):** y mira el texto que aparece al lado. Separar `20`/`42`.
  3. Separar `25,5`/`42`.
- **Resultado esperado:**
  - Antes de separar se lee «Entrenamiento: 80 %».
  - Con 20: 16512 filas de entrenamiento y 4128 de test, en el mensaje y en la etiqueta.
  - Con 25,5: 15377 filas de entrenamiento y 5263 de test.
  - Aparece «No hay valores inexistentes en las columnas seleccionadas. Puedes continuar sin preprocesar.» y **Crear modelo** está activado.

#### CP-15. Porcentajes límite admitidos: 1 y 99

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que se aceptan el porcentaje mínimo y el máximo.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; test `1` y `99`; semilla `42`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Separar `1`/`42`.
  3. Separar `99`/`42`.
- **Resultado esperado:**
  - Con 1: 20434 filas de entrenamiento y 206 de test.
  - Con 99: 206 filas de entrenamiento y 20434 de test.
  - En los dos casos **Crear modelo** queda activado.

#### CP-16. Porcentajes límite rechazados: 0 y 100

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que se rechazan los porcentajes que dejarían un conjunto vacío.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; test `0` y `100`; semilla `42`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Separar `0`/`42`.
  3. Separar `100`/`42`.
- **Resultado esperado:**
  - Las dos veces sale «Error al separar los datos» con el texto "El porcentaje de test debe ser un número entre 1 y 99."
  - Aparecen «Entrenamiento: -- %» y «Datos sin separar», y **Crear modelo** sigue desactivado.

#### CP-17. Porcentajes no válidos

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que se rechazan los porcentajes fuera de rango y los que no son números.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; test `0,99`, `-5`, `abc` y vacío; semilla `42`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Separar con cada valor y semilla `42`. Para el vacío, borra el campo **Test (%):**.
- **Resultado esperado:**
  - Con `0,99` y `-5` sale «Error al separar los datos», y con `abc` y vacío, «Error en el porcentaje». El texto es siempre "El porcentaje de test debe ser un número entre 1 y 99."
  - Aparece «Datos sin separar» y **Crear modelo** sigue desactivado.

#### CP-18. Semillas límite

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que se aceptan la semilla mínima y la máxima.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; test `20`; semillas `0` y `4294967295`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Separar `20`/`0`.
  3. Separar `20`/`4294967295`.
- **Resultado esperado:**
  - Las dos veces sale «Separación realizada», con 16512 filas de entrenamiento y 4128 de test.

#### CP-19. Semillas no válidas

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que se rechazan las semillas fuera de rango y las que no son enteras.
- **Precondiciones:** Generales.
- **Datos de prueba:** `housing.csv`; test `20`; semillas `-1`, `4294967296`, `3.5` y `abc`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `median_income` → `median_house_value`.
  2. Separar con test `20` y cada una de las semillas.
- **Resultado esperado:**
  - `-1` y `4294967296`: «Error al separar los datos», "La semilla debe ser un entero entre 0 y 4294967295."
  - `3.5` y `abc`: «Error en la semilla», "La semilla debe ser un número entero."
  - Aparece «Datos sin separar» y **Crear modelo** sigue desactivado.

#### CP-20. La semilla hace reproducible la separación

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41), [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar que la misma semilla da el mismo modelo y que otra semilla da uno distinto.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple; semillas `42`, `7` y `42`.
- **Pasos:**
  1. Modelo simple y anota la fórmula.
  2. Separar `20`/`7` → Crear, y anota la fórmula.
  3. Separar `20`/`42` → Crear.
- **Resultado esperado:**
  - Con 42 (pasos 1 y 3) se obtiene la fórmula del modelo simple (apartado 3).
  - Con 7: `median_house_value = 41792.4980 * median_income + 44757.2253`, con R² `0.4761`/`0.4620`.

#### CP-21. Dataset con menos de 5 filas

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar el mínimo de filas necesario para separar.
- **Precondiciones:** Generales.
- **Datos de prueba:** `cuatro.csv`: `x,y` / `1,2` / `2,4` / `3,6` / `4,8`.
- **Pasos:**
  1. Crea el archivo `cuatro.csv`.
  2. Abrir → Cargar `cuatro.csv` → Seleccionar `x` → `y` → Separar `20`/`42`.
- **Resultado esperado:**
  - Sale «Error al separar los datos» con el texto "El dataset tiene 4 filas y se necesitan al menos 5 para separarlo."
  - Aparece «Datos sin separar».

#### CP-22. Porcentajes que dejan un conjunto vacío

- **Historia:** [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41)
- **Objetivo:** Comprobar que, con solo 5 filas, no se crea ningún conjunto vacío.
- **Precondiciones:** Generales.
- **Datos de prueba:** `cinco.csv`: `x,y` / `1,2` / `2,4` / `3,6` / `4,8` / `5,10`; test `1` y `99`.
- **Pasos:**
  1. Crea el archivo `cinco.csv`.
  2. Abrir → Cargar `cinco.csv` → Seleccionar `x` → `y` → Separar `1`/`42` → Separar `99`/`42`.
- **Resultado esperado:**
  - Con 1 sale «Error al separar los datos» con el texto "Con un 1.0 % el conjunto de test quedaría vacío. Aumenta el porcentaje de test."
  - Con 99 sale «Error al separar los datos» con el texto "Con un 99.0 % el conjunto de entrenamiento quedaría vacío. Reduce el porcentaje de test."
  - Aparece «Datos sin separar».

### Valores inexistentes y preprocesado

Los casos CP-23 a CP-27 parten de: Abrir → Cargar `housing.csv` → Seleccionar `total_rooms`, `total_bedrooms` → `median_house_value` → Separar `20`/`7` (lo llamamos **Base nulos**).

#### CP-23. Detectar valores inexistentes

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar el recuento de valores inexistentes por columna y por conjunto.
- **Precondiciones:** Generales.
- **Datos de prueba:** Base nulos.
- **Pasos:**
  1. Base nulos.
  2. Mira el recuadro **Valores inexistentes y preprocesado**.
- **Resultado esperado:**
  - Se lee «Valores inexistentes: 156 en entrenamiento y 51 en test.».
  - En la tabla, `total_bedrooms` tiene 156 y 51, y las otras dos columnas, 0 y 0.
  - **Aplicar preprocesado** está activado, **Crear modelo** desactivado y se lee «Creación del modelo: no disponible hasta tratar los nulos».

#### CP-24. Tratamientos de valores inexistentes

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26), [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16), Predicciones
- **Objetivo:** Comprobar cada tratamiento y el modelo que se obtiene con él.
- **Precondiciones:** Generales.
- **Datos de prueba:** Base nulos; los tratamientos de la tabla; predicción con `total_rooms` = `2000` y `total_bedrooms` = `400`.
- **Pasos:**
  1. Base nulos.
  2. En **Tratamiento:** elige el de la fila. Si es una constante, escribe su valor en el campo de al lado.
  3. Pulsa **Aplicar preprocesado** y luego **OK** → Crear → Predecir `total_rooms`=`2000` y `total_bedrooms`=`400`.
  4. Cierra la aplicación y repite los pasos con cada fila.
- **Resultado esperado:**
  - El mensaje «Preprocesado aplicado» indica 156 filas eliminadas o valores rellenados en entrenamiento y 51 en test. Después, los recuentos de la tabla pasan a 0.
  - La fórmula empieza por `median_house_value =` y los resultados coinciden con la tabla:

  | Tratamiento | Filas (entrenamiento/test) | Fórmula (tras `=`) | R² (entrenamiento/test) | Predicción |
  | --- | --- | --- | --- | --- |
  | Eliminar filas | 16356 / 4077 | `34.3890 * total_rooms - 150.6062 * total_bedrooms + 196526.3550` | `0.0592` / `0.0558` | `205061.7826` |
  | Rellenar con media | 16512 / 4128 | `33.5325 * total_rooms - 146.5061 * total_bedrooms + 196571.7742` | `0.0585` / `0.0547` | `205034.3885` |
  | Rellenar con mediana | 16512 / 4128 | `33.4401 * total_rooms - 145.9823 * total_bedrooms + 196391.6828` | `0.0583` / `0.0547` | `204878.8523` |
  | Rellenar con constante `500` | 16512 / 4128 | `33.5222 * total_rooms - 146.4452 * total_bedrooms + 196512.9041` | `0.0585` / `0.0547` | `204979.2352` |
  | Rellenar con constante `0` (límite) | 16512 / 4128 | `30.9779 * total_rooms - 132.2477 * total_bedrooms + 194941.5889` | `0.0545` / `0.0505` | `203998.3059` |

#### CP-25. Campo de constante según el tratamiento

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar que el valor constante solo se puede escribir con su tratamiento.
- **Precondiciones:** Generales.
- **Datos de prueba:** Base nulos.
- **Pasos:**
  1. Base nulos. Elige **Rellenar con media** e intenta escribir en el campo **Valor numérico**.
  2. Elige **Rellenar con constante** y escribe `5`.
- **Resultado esperado:**
  - Con la media, el campo está desactivado; con la constante, admite texto.

#### CP-26. Constante no válida

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar que se rechazan las constantes no numéricas y las infinitas.
- **Precondiciones:** Generales.
- **Datos de prueba:** Base nulos; constantes `abc`, vacía e `inf`.
- **Pasos:**
  1. Base nulos y elige **Rellenar con constante**.
  2. Con cada valor, escríbelo en el campo, pulsa **Aplicar preprocesado** y luego **OK**.
- **Resultado esperado:**
  - Sale «Error de preprocesado» con el texto "El valor constante debe ser numérico." para `abc` y para el vacío, y "El valor constante debe ser un número finito." para `inf`.
  - Los recuentos siguen en 156 y 51, y **Crear modelo** sigue desactivado.

#### CP-27. Eliminar filas deja un conjunto vacío

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar que no se pueden eliminar todas las filas de un conjunto.
- **Precondiciones:** Generales.
- **Datos de prueba:** Igual que Base nulos, pero con test `1` y semilla `42`.
- **Pasos:**
  1. Abrir → Cargar `housing.csv` → Seleccionar `total_rooms`, `total_bedrooms` → `median_house_value` → Separar `1`/`42`.
  2. Elige **Eliminar filas**, pulsa **Aplicar preprocesado** y luego **OK**.
- **Resultado esperado:**
  - Antes de aplicar se lee «Valores inexistentes: 1 en entrenamiento y 206 en test.».
  - Sale «Error de preprocesado» con el texto "Eliminar las filas con valores inexistentes dejaría vacío el conjunto de entrenamiento o el de test."
  - Se mantienen 20434/206 filas y **Crear modelo** sigue desactivado.

#### CP-28. Media de una columna sin valores

- **Historia:** [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26)
- **Objetivo:** Comprobar el aviso cuando no se puede calcular la media.
- **Precondiciones:** Generales.
- **Datos de prueba:** `sin_valores.csv`: `x,y` seguido de 10 líneas `,1` … `,10` (`x` vacía).
- **Pasos:**
  1. Crea el archivo `sin_valores.csv`.
  2. Abrir → Cargar `sin_valores.csv` → Seleccionar `x` → `y` → Separar `20`/`42`.
  3. Elige **Rellenar con media**, pulsa **Aplicar preprocesado** y luego **OK**.
- **Resultado esperado:**
  - Antes de aplicar se lee «Valores inexistentes: 8 en entrenamiento y 2 en test.».
  - Sale «Error de preprocesado» con el texto "No es posible calcular la media de 'x' con los valores del conjunto de entrenamiento."

### Creación, evaluación y gráfico del modelo

#### CP-29. Modelo simple con los tres formatos

- **Historia:** [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar la fórmula, las métricas y el gráfico de un modelo con una entrada.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple con `housing.csv`, `housing.xlsx` y `housing.db`.
- **Pasos:**
  1. Modelo simple. Mira el mensaje, la fórmula, las métricas y el gráfico.
  2. En **Visualización:** elige **Regresión por variable**.
  3. Repite el paso 1 cargando `housing.xlsx` y después `housing.db`.
- **Resultado esperado:**
  - Sale «Modelo creado» con el texto "El modelo de regresión lineal se ha creado correctamente."
  - Con los tres archivos, la fórmula y las métricas son las del modelo simple (apartado 3) y debajo se lee «Entradas: median_income  ·  Salida: median_house_value».
  - El gráfico inicial se titula «Valores reales vs. predichos», con los ejes «Valor real» y «Valor predicho», y su leyenda es: Entrenamiento, Test, Predicción perfecta y Tendencia de predicciones (test). **Variable de entrada:** está desactivado.
  - En el paso 2, el título pasa a «Efecto de median_income sobre median_house_value», la leyenda incluye «Recta condicional del modelo» y **Variable de entrada:** sigue desactivado.

#### CP-30. Modelo múltiple y vistas del gráfico

- **Historia:** [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar el modelo con dos entradas y el cambio de vista y de variable.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo múltiple.
- **Pasos:**
  1. Modelo múltiple.
  2. En **Visualización:** elige **Regresión por variable**. En **Variable de entrada:** elige `median_income`.
  3. En **Visualización:** elige **Reales vs. predichos**.
- **Resultado esperado:**
  - La fórmula y las métricas son las del modelo múltiple (apartado 3) y no cambian en todo el caso.
  - En el paso 2, **Variable de entrada:** se activa. El título es «Efecto de housing_median_age sobre median_house_value» y después «Efecto de median_income sobre median_house_value».
  - En el paso 3 vuelve el título «Valores reales vs. predichos» y **Variable de entrada:** se desactiva.

#### CP-31. Zoom, movimiento y vista inicial

- **Historia:** [#37](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/37), [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar la lupa, el arrastre y el botón de vista inicial.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple.
- **Pasos:**
  1. Modelo simple. Gira la rueda del ratón sobre el gráfico.
  2. Pulsa 🔍 y gira la rueda hacia delante tres veces. Arrastra el gráfico con el botón izquierdo.
  3. Pulsa **Vista inicial**. Vuelve a pulsar 🔍 y gira la rueda.
- **Resultado esperado:**
  - Con la lupa desactivada, la rueda no cambia la escala. Con la lupa activada, amplía el gráfico.
  - Al arrastrar, el gráfico se mueve, y **Vista inicial** devuelve la escala y la posición originales.
  - La ayuda de 🔍 dice «Zoom activado (pulsa para desactivar)» o «Zoom desactivado (pulsa para activar)», según el estado.

#### CP-32. Mínimo de filas de test

- **Historia:** [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16)
- **Objetivo:** Comprobar que con 1 fila de test no se crea el modelo y que con 2 sí.
- **Precondiciones:** Generales.
- **Datos de prueba:** `cinco.csv` de CP-22; test `20` y `40`.
- **Pasos:**
  1. Crea el archivo `cinco.csv` si no existe.
  2. Abrir → Cargar `cinco.csv` → Seleccionar `x` → `y` → Separar `20`/`42` → Crear.
  3. Separar `40`/`42` → Crear.
- **Resultado esperado:**
  - Con 20 % (4/1 filas) sale «Error al crear el modelo» con el texto "El conjunto de test necesita al menos 2 filas para calcular R²." y **Guardar modelo** sigue desactivado.
  - Con 40 % (3/2 filas) sale «Modelo creado» y R² vale `1.0000` en los dos conjuntos.

### Descripción, guardado y carga del modelo

#### CP-33. Guardar y cargar un modelo

- **Historia:** Descripción, [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24)
- **Objetivo:** Comprobar que el modelo se guarda (y se añade `.pkl` si falta) y que se recupera completo tras reiniciar.
- **Precondiciones:** Generales. No existe `cargar.pkl`.
- **Datos de prueba:** Modelo simple; descripción `Modelo de prueba ñ`; nombre `cargar` (sin extensión).
- **Pasos:**
  1. Modelo simple. En **Descripción (opcional):** escribe `Modelo de prueba ñ`.
  2. Guardar `cargar` (lee el mensaje antes de pulsar **OK**).
  3. Cierra la aplicación → Abrir → Cargar modelo `cargar.pkl` (lee el mensaje antes de pulsar **OK**).
- **Resultado esperado:**
  - Sale «Modelo guardado» con el texto «El modelo se ha guardado correctamente en:» y una ruta que termina en `cargar.pkl`. El archivo está en la carpeta.
  - Sale «Modelo cargado» con esa ruta. Se ven la fórmula y las métricas del modelo simple y la descripción `Modelo de prueba ñ`.
  - No se ven la tabla, la selección, la separación, el preprocesado, **Crear modelo** ni el gráfico.

#### CP-34. Guardar sin descripción

- **Historia:** Descripción, [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24)
- **Objetivo:** Comprobar el aviso de descripción vacía y sus dos respuestas.
- **Precondiciones:** Generales. No existe `sin_descripcion.pkl`.
- **Datos de prueba:** Modelo simple sin descripción.
- **Pasos:**
  1. Modelo simple. Pulsa **Guardar modelo** y en **Descripción vacía** pulsa **No**.
  2. Pulsa **Guardar modelo**, responde **Yes** y guarda como `sin_descripcion.pkl` en `C:\pruebas_aporel10`. Pulsa **OK**.
  3. Cargar modelo `sin_descripcion.pkl`.
- **Resultado esperado:**
  - El aviso dice "El modelo no tiene descripción. ¿Quieres guardarlo igualmente sin descripción?"
  - Con **No** no se abre el explorador y la descripción se puede seguir escribiendo.
  - Con **Yes** el modelo se guarda y se carga sin errores, con la descripción vacía.

#### CP-35. Cancelar el guardado y la carga

- **Historia:** [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24)
- **Objetivo:** Comprobar que cancelar cualquiera de los dos exploradores no cambia el modelo.
- **Precondiciones:** Generales. No existe `actual.pkl`.
- **Datos de prueba:** Modelo simple; descripción `Modelo de prueba ñ`; `actual.pkl`.
- **Pasos:**
  1. Modelo simple y escribe la descripción. Pulsa **Guardar modelo** y luego **Cancelar**.
  2. Guardar `actual.pkl`. Pulsa **Cargar modelo...** y luego **Cancelar**.
- **Resultado esperado:**
  - Al cancelar no sale ningún mensaje y siguen la fórmula del modelo simple y la descripción.

#### CP-36. No sobrescribir un modelo existente

- **Historia:** [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24), Descripción
- **Objetivo:** Comprobar que se pide confirmación antes de sobrescribir y que rechazarla conserva el archivo.
- **Precondiciones:** Generales. No existe `repetido.pkl`.
- **Datos de prueba:** Modelo simple; descripciones `Original` y `Cambiada`; `repetido.pkl`.
- **Pasos:**
  1. Modelo simple con la descripción `Original` → Guardar `repetido.pkl`.
  2. Cambia la descripción a `Cambiada`, pulsa **Guardar modelo**, elige `repetido.pkl` y pulsa **Guardar**. Cuando pida confirmación, pulsa **No** y después cancela el explorador.
  3. Pulsa **Cargar modelo...**, responde **Yes** en **Cambios sin guardar** y abre `repetido.pkl`.
- **Resultado esperado:**
  - En el paso 2 se pide confirmación para sobrescribir.
  - El modelo cargado tiene la descripción `Original`.

#### CP-37. Guardar en una carpeta inexistente

- **Historia:** [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21)
- **Objetivo:** Comprobar que una ruta no válida no hace perder el modelo.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple; ruta `C:\pruebas_aporel10\noexiste\m.pkl`.
- **Pasos:**
  1. Modelo simple. Pulsa **Guardar modelo**, escribe la ruta en **Nombre** y pulsa **Guardar**.
  2. Cierra el aviso y, si sigue abierto, cancela el explorador.
- **Resultado esperado:**
  - Windows o la aplicación avisan de que no se puede guardar.
  - No se crea ningún archivo y el modelo sigue en pantalla.

#### CP-38. Editar la descripción de un modelo cargado

- **Historia:** Descripción, [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24)
- **Objetivo:** Comprobar el aviso de cambios sin guardar y que la descripción editada se conserva.
- **Precondiciones:** Generales. Existe `cargar.pkl` (CP-33) y no existe `editado.pkl`.
- **Datos de prueba:** `cargar.pkl`; descripción `Otra`; `editado.pkl`.
- **Pasos:**
  1. Abrir → Cargar modelo `cargar.pkl`. Cambia la descripción a `Otra`.
  2. Pulsa **Cargar modelo...** y en **Cambios sin guardar** pulsa **No**.
  3. Guardar `editado.pkl` → cierra la aplicación → Abrir → Cargar modelo `editado.pkl`.
- **Resultado esperado:**
  - El aviso dice "El modelo actual tiene cambios sin guardar. Si cargas otro modelo, se perderán esos cambios. ¿Quieres continuar sin guardarlo?" y con **No** se mantiene `Otra`.
  - `editado.pkl` se carga con la descripción `Otra` y la fórmula del modelo simple.

#### CP-39. Volver a los datos desde un modelo cargado

- **Historia:** [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24), [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14)
- **Objetivo:** Comprobar que al cargar datos vuelven a verse las secciones ocultas.
- **Precondiciones:** Generales. Existe `cargar.pkl` (CP-33).
- **Datos de prueba:** `cargar.pkl`, `housing.csv`.
- **Pasos:**
  1. Abrir → Cargar modelo `cargar.pkl` → Cargar `housing.csv`.
- **Resultado esperado:**
  - Vuelven a verse la tabla (20640 filas), la selección, la separación, el preprocesado y **Crear modelo**.
  - Se lee «No se ha creado ningún modelo.».

#### CP-40. Archivo de modelo no válido

- **Historia:** [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24)
- **Objetivo:** Comprobar que un archivo dañado o que no es `.pkl` no se carga y que el modelo actual se conserva.
- **Precondiciones:** Generales. No existe `actual.pkl`.
- **Datos de prueba:** `vacio.pkl` (sin contenido), `falso.pkl` (`hola esto no es un modelo`), `housing.csv`.
- **Pasos:**
  1. Crea los archivos `vacio.pkl` y `falso.pkl`.
  2. Modelo simple con la descripción `Modelo de prueba ñ` → Guardar `actual.pkl`.
  3. Cargar modelo `vacio.pkl` → Cargar modelo `falso.pkl`.
  4. Pulsa **Cargar modelo...**, escribe en **Nombre** la ruta completa de `data\housing.csv`, pulsa **Abrir** y luego **OK**.
- **Resultado esperado:**
  - Con los `.pkl` sale «Error al cargar el modelo» con un texto que empieza por "No se pudo leer el archivo de modelo" y termina en "Ran out of input" (`vacio.pkl`) o en "Memo value not found at index 111" (`falso.pkl`).
  - Con el CSV sale "El archivo debe tener extensión .pkl."
  - Siguen en pantalla la fórmula del modelo simple y la descripción.

#### CP-41. Cambios sin guardar al cargar datos

- **Historia:** Descripción, [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14), [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21)
- **Objetivo:** Comprobar que se puede conservar o descartar un modelo sin guardar.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple con la descripción `Modelo de prueba ñ`; `housing.xlsx`.
- **Pasos:**
  1. Modelo simple con la descripción. Pulsa **Cargar datos...** y responde **No**.
  2. Pulsa **Cargar datos...**, responde **Yes** y abre `housing.xlsx` desde `data`.
- **Resultado esperado:**
  - El aviso dice "El modelo actual tiene cambios sin guardar. Si cargas un dataset, se descartará el modelo actual. ¿Quieres continuar sin guardarlo?"
  - Con **No** no se abre el explorador y se mantienen la fórmula y la descripción.
  - Con **Yes** la ruta termina en `housing.xlsx`, se lee «No se ha creado ningún modelo.» y la descripción queda vacía y desactivada.

### Predicciones

#### CP-42. Predicciones válidas

- **Historia:** Predicciones
- **Objetivo:** Comprobar la predicción con punto decimal, coma decimal, cero y un valor negativo.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple; `median_income` = `3.5`, `3,5`, `0` y `-1`.
- **Pasos:**
  1. Modelo simple.
  2. Predecir `median_income` con cada valor.
- **Resultado esperado:**
  - `3.5` y `3,5` dan `median_house_value = 191228.2020`; `0` da `44459.7292` y `-1`, `2525.8798`.

#### CP-43. Predicción con un modelo múltiple

- **Historia:** Predicciones
- **Objetivo:** Comprobar que hay un campo por entrada y que el mensaje de error señala cada campo con problemas.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo múltiple; primero `30` y `3.5`; después `x` y vacío.
- **Pasos:**
  1. Modelo múltiple. Predecir `housing_median_age`=`30` y `median_income`=`3.5`.
  2. Predecir `housing_median_age`=`x` y `median_income` vacío, y pulsa **OK**.
- **Resultado esperado:**
  - Hay dos campos, `housing_median_age` y `median_income`. En el paso 1 sale `median_house_value = 193125.4508`.
  - En el paso 2 sale «Predicción no válida» con el texto "Faltan valores para: median_income. Estos valores no son números válidos: housing_median_age." y no se muestra ningún resultado.

#### CP-44. Predicciones no válidas

- **Historia:** Predicciones
- **Objetivo:** Comprobar que no se predice con un valor vacío, no numérico o desbordado.
- **Precondiciones:** Generales.
- **Datos de prueba:** Modelo simple; `median_income` vacío, `abc` y `1e400`.
- **Pasos:**
  1. Modelo simple.
  2. Predecir `median_income` con cada valor y pulsa **OK**.
- **Resultado esperado:**
  - Vacío: «Predicción no válida», "Faltan valores para: median_income."
  - `abc` y `1e400`: «Predicción no válida», "Estos valores no son números válidos: median_income."
  - No se muestra ningún resultado.

### Flujo completo

#### CP-45. Flujo completo: cargar, crear, guardar, recuperar y predecir

- **Historia:** [#14](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/14), [#11](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/11), [#41](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/41), [#26](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/26), [#16](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/16), Descripción, [#21](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/21), [#24](https://taiga.daico.es/project/gia-is-proyecto-base-13/t/24), Predicciones
- **Objetivo:** Comprobar el recorrido completo de la aplicación.
- **Precondiciones:** Generales. No existe `flujo.pkl`.
- **Datos de prueba:** `housing.db`; `housing_median_age`, `median_income` → `median_house_value`; test `20`, semilla `42`; descripción `Flujo completo`; `flujo.pkl`; predicción con `30` y `3.5`.
- **Pasos:**
  1. Abrir → Cargar `housing.db` → Seleccionar `housing_median_age`, `median_income` → `median_house_value` → Separar `20`/`42` → Crear.
  2. Escribe la descripción `Flujo completo` → Predecir `housing_median_age`=`30` y `median_income`=`3.5`.
  3. Guardar `flujo.pkl` → cierra la aplicación → Abrir → Cargar modelo `flujo.pkl`.
  4. Predecir otra vez con los mismos valores.
- **Resultado esperado:**
  - La tabla tiene 20640 filas, la separación da 16512/4128 y no hay valores inexistentes.
  - Antes de guardar y después de cargar se ven la fórmula y las métricas del modelo múltiple (apartado 3).
  - La descripción recuperada es `Flujo completo`.
  - Las dos predicciones dan `median_house_value = 193125.4508`.
