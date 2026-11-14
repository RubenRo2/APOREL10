# APOREL10

Aplicación de escritorio con interfaz gráfica orientada al análisis y modelado de datos mediante regresión lineal (simple y múltiple).

El sistema permite importar conjuntos de datos desde diversas fuentes (archivos CSV, Excel y bases de datos SQLite), entrenar y visualizar los modelos resultantes, exportarlos e importarlos para su posterior reutilización, y generar predicciones a partir de nuevas entradas.

## Funcionalidades (versión 0.2.0)

Versión en desarrollo: permite cargar y preparar los datos, y crear y evaluar un modelo de regresión lineal.

1. **Cargar datos** desde archivos CSV (`.csv`), Excel (`.xlsx`, `.xls`) o SQLite (`.sqlite`, `.db`) y verlos en una tabla.
2. **Seleccionar columnas**: una o varias columnas de entrada y una de salida (numéricas).
3. **Separar los datos** en entrenamiento y test, eligiendo el porcentaje de test y la semilla.
4. **Preprocesar** los valores inexistentes: eliminar filas o rellenar con la media, la mediana o un valor constante.
5. **Crear y evaluar el modelo** de regresión lineal (simple o múltiple) con los datos de entrenamiento:
   - **Fórmula** del modelo con sus coeficientes.
   - **Métricas** R² y ECM (error cuadrático medio) sobre los conjuntos de entrenamiento y test.
   - **Gráfico** del modelo, con dos visualizaciones: *Regresión por variable* (eligiendo la variable de entrada que se representa) y *Reales vs. predichos*. Se puede mover arrastrando, hacer zoom con la rueda del ratón y volver a la *Vista inicial*.

Próximas versiones: guardado y carga de modelos y predicciones.

## Requisitos previos

Es necesario tener instalado el gestor de paquetes y proyectos **uv**:

- **Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- **Linux / macOS (curl):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- **Linux (sin curl):**

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

## Cómo empezar

Para clonar y ejecutar el proyecto en local:

```bash
git clone https://github.com/RubenRo2/APOREL10.git
cd APOREL10
git switch dev
uv sync
uv run aporel10
```

### Desde una release

Descarga el **Source code (zip)** de la release en la página [Releases](https://github.com/RubenRo2/APOREL10/releases), descomprímelo y, dentro de la carpeta:

```bash
uv sync
uv run aporel10
```

## Gestión de datos

Los datasets de prueba (CSV, Excel, bases de datos SQLite), modelos guardados y archivos generados no se suben al repositorio.
Deben almacenarse localmente dentro de la carpeta `data/` (excluida mediante `.gitignore`). Consulta `CONTRIBUTING.md` para más información sobre el flujo de trabajo y las normas del equipo.