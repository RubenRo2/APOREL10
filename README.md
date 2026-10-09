# APOREL10

Aplicación de escritorio con interfaz gráfica orientada al análisis y modelado de datos mediante regresión lineal (simple y múltiple). 

El sistema permite importar conjuntos de datos desde diversas fuentes (archivos CSV, Excel y bases de datos SQLite), entrenar y visualizar los modelos resultantes, exportarlos e importarlos para su posterior reutilización, y generar predicciones a partir de nuevas entradas.

## Requisitos previos

Es necesario tener instalado el gestor de paquetes y proyectos **uv**:

- **Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
```

- **Linux / macOS (curl):**
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

- **Linux (sin curl):**
```bash
wget -qO- [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

## Como empezar

Para clonar y ejecutar el proyecto en local:

```bash
git clone [https://github.com/RubenRo2/APOREL10.git](https://github.com/RubenRo2/APOREL10.git)
cd APOREL10
git switch dev
uv sync
uv run aporel10
```

## Gestión de datos

Los datasets de prueba (CSV, Excel, bases de datos SQLite), modelos guardados y archivos generados no se suben al repositorio. 
Deben almacenarse localmente dentro de la carpeta `data/` (excluida mediante `.gitignore`). Consulta `CONTRIBUTING.md` para más información sobre el flujo de trabajo y las normas del equipo.