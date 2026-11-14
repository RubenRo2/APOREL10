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

### 7.4. Reglas de fusión y GitHub Actions

- Antes de abrir la Pull Request de una rama de trabajo (`feature`, `fix` o `docs`) hacia `dev`, se actualiza con los últimos cambios de `dev`(sección 3, paso 2) y se comprueba en local con `uv run pytest`.
- **Validación obligatoria:** Las ramas de trabajo solo se fusionarán en `dev` si pasan las pruebas locales **Y** la última ejecución automática en la pestaña Actions de GitHub finaliza con éxito (✅).
- **Protección de `dev`:** Si tras un merge el flujo de GitHub Actions falla en `dev`, se bloquean nuevas fusiones. Se debe abrir inmediatamente una tarea en Taiga y una rama `fix/` para solucionarlo.
- El paso a producción (`dev` a `main`) solo se realizará si la última ejecución de GitHub Actions sobre `dev` ha terminado correctamente y sin errores.

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

### 11.1. Versionado

Seguimos el versionado semántico (SemVer), `MAJOR.MINOR.PATCH`:

| Tipo de commit | Versión que sube |
|----------------|------------------|
| `fix` | PATCH (`0.1.0` → `0.1.1`) |
| `feat` | MINOR (`0.1.0` → `0.2.0`) |
| `BREAKING CHANGE` | MAJOR (`1.0.0` → `2.0.0`) |

Las versiones `0.x.y` indican que la aplicación está en desarrollo; `1.0.0` es la primera versión completa y estable. Antes de `v1.0.0` se revisa todo el código y se refactoriza en ramas desde `dev` con commits `refactor`.

### 11.2. Procedimiento de release

Sustituye `X.Y.Z` por el número de la versión (por ejemplo, `0.1.0`).

**1. Requisitos previos**

- Todas las historias previstas para la versión están terminadas y fusionadas en `dev`.
- Las pruebas pasan sobre `dev`:

  ```bash
  git switch dev
  git pull origin dev
  uv sync
  uv run pytest
  ```

- Un miembro del equipo que no haya implementado esas historias prueba a mano la aplicación sobre `dev` con un dataset de ejemplo de su carpeta `data/`. Los errores encontrados se corrigen en ramas `fix/` antes de continuar.
- El `README.md` describe las funcionalidades de la versión.

**2. Actualizar el número de versión**

Si el campo `version` de `pyproject.toml` no es ya `X.Y.Z`, se cambia en una rama de trabajo desde `dev` (`uv version` actualiza también `uv.lock`):

```bash
git switch -c feature/<id>-version-X.Y.Z
uv version X.Y.Z
uv run pytest
git add pyproject.toml uv.lock
git commit -m "chore: actualiza la versión a X.Y.Z"
```

y se integra en `dev` siguiendo la sección 3.

**3. Fusionar `dev` en `main`**

```bash
git switch main
git pull origin main
git merge --no-ff dev -m "Merge branch 'dev' into main: versión X.Y.Z"
uv run pytest
git push origin main
```

Después de la fusión, `main` y `dev` tienen el mismo código y el desarrollo continúa en ramas creadas desde `dev`.

**4. Crear y subir la etiqueta**

```bash
git tag -a vX.Y.Z -m "Versión X.Y.Z"
git push origin vX.Y.Z
```

La etiqueta es *anotada* (`-a`): guarda quién la creó, cuándo y un mensaje.

**5. Crear la release en GitHub**

1. En la página del repositorio, en la columna derecha, entra en **Releases** y pulsa **Draft a new release**.
2. En **Choose a tag**, elige `vX.Y.Z`.
3. Título: `vX.Y.Z`.
4. Escribe las notas de la release (paso 6).
5. Si la versión es `0.x.y`, marca **Set as a pre-release**. A partir de `1.0.0`, no la marques y deja **Set as the latest release**.
6. Pulsa **Publish release**.

**6. Notas de la release**

Para ver los commits desde la versión anterior (en la primera release, quita `vANTERIOR..`):

```bash
git log vANTERIOR..vX.Y.Z --oneline --no-merges
```

Plantilla de las notas:

```markdown
## APOREL10 vX.Y.Z

Breve descripción de la aplicación y del estado del proyecto.

### Funcionalidades
- (a partir de los commits `feat`)

### Correcciones
- (a partir de los commits `fix`)

### Pendiente para próximas versiones
- ...

Instrucciones de instalación y uso: [README.md](https://github.com/RubenRo2/APOREL10/blob/vX.Y.Z/README.md)
```

**7. Comprobar la descarga**

1. En la página de la release, descarga **Source code (zip)**.
2. Descomprímelo en una carpeta nueva, fuera del repositorio.
3. Dentro de esa carpeta:

   ```bash
   uv sync
   uv run aporel10
   ```

4. Comprueba que la aplicación se abre siguiendo el `README.md` y que el `version` de `pyproject.toml` coincide con el de la release.