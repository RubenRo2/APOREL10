# Guía de contribución

Normas de desarrollo, estilo y flujo de trabajo del proyecto **APOREL10**

## 1. Normas básicas del repositorio

- Prohibido subir archivos de datos (CSV, SQLite, Excel...).
- Los datos se guardan solo en local, en la carpeta `data/`, excluida con `.gitignore`.
- Ejecuta `git status` antes de cada commit.

## 2. Modelo de ramas

- **`main`**: versiones estables. Solo recibe cambios desde `dev` al publicar una release.
- **`dev`**: integración del desarrollo, creada desde `main` al inicio del proyecto.
- **Prohibido commitear directamente en `main` o `dev`.**

Una rama por tarea, creada desde `dev`, en minúsculas y con guiones. El nombre incluye el número de la tarea en Taiga (`<numero>`). Las ramas no se eliminan una vez fusionadas.

| Funcionalidad | `feature/<numero>-<descripcion>` | 
| Corrección | `fix/<numero>-<descripcion>` | 
| Documentación | `docs/<numero>-<descripcion>` | 

## 3. Flujo de trabajo

Los cambios se integran en `dev`.

```bash
# 1. Crear la rama desde dev actualizado
git switch dev
git pull origin dev
git switch -c feature/10-importacion-datos

# 2. Actualizar la rama con dev (con frecuencia y antes de fusionar)
git fetch origin
git merge origin/dev

# 3. 
git add .
git commit -m "mensaje commit"

# 4. Integrar los cambios localmente
git switch dev
git merge feature/10-importacion-datos

# 5. Subir dev actualizado al repositorio remoto
git push origin dev
```

6. La rama se conserva tras el merge.


## 4. Mensajes de commit (Conventional Commits)

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

- **description**: en imperativo, sin punto final.
- **scope** *(opcional)*: parte del código afectada, entre paréntesis (`gui`, `modelo`, `datasets`).
- **body** *(opcional)*: explica el motivo del cambio; va separado por una línea en blanco.
- **footer** *(opcional)*: referencias a incidencias o `BREAKING CHANGE`.
- **`!`** tras el tipo o scope indica un `BREAKING CHANGE`.

| `feat` | Añade una nueva funcionalidad al proyecto |
| `fix` | Corrige un error |
| `docs` | Cambia solo la documentación o los comentarios |
| `refactor` | Mejora la estructura interna del código sin cambiar su comportamiento |
| `test` | Añade o modifica pruebas |
| `chore` | Tareas de mantenimiento, como dependencias o configuración |

## 5. Dependencias con `uv`

| Añadir librería | `uv add <paquete>` |
| Añadir dependencia de desarrollo | `uv add --dev <paquete>` |
| Sincronizar el entorno | `uv sync` |
| Ejecutar tests | `uv run pytest` |

- No usar `pip install`.
- `pyproject.toml` y `uv.lock` se commitean siempre juntos.

## 6. Documentación

| Al crear una función, clase o módulo | Docstring |
| Al cambiar la instalación o el uso | `README.md` |
| Al cambiar estas normas | `CONTRIBUTING.md` |

Los cambios de documentación se hacen en una rama `docs/` y se commitean con `docs:`.

## 7. Pruebas automatizadas

El proyecto usa **pytest**, añadido como dependencia de desarrollo (`uv add --dev pytest`). Las pruebas comprueban los módulos de lógica, así que no necesitan abrir la interfaz gráfica.

### 7.1. Ejecutar las pruebas

Desde la raíz del repositorio:

```bash
uv run pytest                          # todas las pruebas
uv run pytest -v                       # mostrando el nombre de cada prueba
uv run pytest tests/test_paquete.py    # solo un archivo
```

Cada prueba que pasa aparece como `.` (`PASSED` con `-v`) y cada una que falla como `F` (`FAILED`). Si alguna falla, el resumen final indica el archivo y la función (`FAILED tests/<archivo>.py::<prueba>`) y, más arriba, el `assert` que no se ha cumplido junto con los valores obtenidos.

### 7.2. Añadir pruebas nuevas

- Las pruebas van en la carpeta `tests/`, separada del código fuente, con **un archivo por cada módulo** de la aplicación: el módulo `src/aporel10/importacion.py` se prueba en `tests/test_importacion.py`.
- Cada prueba es una función cuyo nombre empieza por `test_` y comprueba el resultado con `assert`. Para comprobar que se lanza una excepción se usa `pytest.raises`.
- El código se importa **por el nombre del paquete**, nunca modificando `sys.path` ni con rutas relativas:

```python
  from aporel10.importacion import importar_datos
```

### 7.3. Datos de las pruebas

- Las pruebas **no** usan archivos de datos del repositorio ni de la carpeta local `data/` (en GitHub y en los ordenadores de los demás no existen).
- Los datos se escriben en el propio código de la prueba: unas pocas filas con valores conocidos, incluidos los casos especiales que se quieran comprobar (valores inexistentes, columnas no numéricas...).
- Si una prueba necesita un archivo, lo crea al ejecutarse en una carpeta temporal con el parámetro `tmp_path` de pytest, que se borra automáticamente:

```python
  import pandas as pd

  from aporel10.importacion import importar_datos


  def test_importa_csv(tmp_path):
      ruta = tmp_path / "datos.csv"
      pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]}).to_csv(ruta, index=False)

      datos = importar_datos(ruta)

      assert list(datos.columns) == ["x", "y"]
```

  (Es un ejemplo: el módulo `importacion` y pandas llegarán con la historia #10.)

### 7.4. Reglas de fusión según el resultado de las pruebas

- Antes de abrir la Pull Request de una rama de trabajo (`feature`, `fix` o `docs`) hacia `dev`, se actualiza con los últimos cambios de `dev` (sección 3, paso 2) y se ejecuta `uv run pytest`. **Solo se fusiona si todas las pruebas pasan.**
- `dev` solo se fusiona en `main` si todas las pruebas pasan sobre `dev`.

## 8. Estilo de código (PEP 8)

- Indentación de 4 espacios, sin tabuladores.
- 2 líneas en blanco entre funciones y clases; 1 entre métodos.
- Espacios alrededor de operadores: `total = precio * unidades`.
- Nombres significativos y comparaciones con `is None` / `is not None`.
- Comentarios solo si aportan algo que el código no dice, en inglés.

| Variables y funciones | `snake_case` | `calcular_media()` |
| Clases | `CapWords` | `LinearModel` |
| Constantes | `UPPER_CASE` | `MAX_SIZE` |

**Herramienta**: extensión **autopep8** de VSCode.

## 9. Refactorización

Mejorar el código **sin cambiar su comportamiento**, con los tests en verde.

- **Cuándo**: al encontrar código duplicado o confuso.

## 10. Revisión de cambios

Antes de aprobar y fusionar una Pull Request en `dev`, quien la revisa comprueba:

- [ ] Estilo PEP 8 aplicado con autopep8.
- [ ] Nombres claros.
- [ ] Sin código duplicado.
- [ ] Mensajes de commit correctos.
- [ ] Todas las pruebas pasan (`uv run pytest`).

## 11. Releases

Versionado `MAJOR.MINOR.PATCH` (SemVer):

| `fix` | PATCH |
| `feat` | MINOR |
| `BREAKING CHANGE` | MAJOR |

Antes de `v1.0.0` se revisa todo el código y se refactoriza en ramas desde `dev` con commits `refactor`. Después:

```bash
git switch main
git merge --no-ff dev
git tag v1.0.0
git push origin main --tags
```