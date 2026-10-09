# Guia de contribución

Normas de desarrollo, estilo y flujo de trabajo del proyecto **APOREL10**

## 1. Normas basicas de uso del repositorio

- **Prohibición de subida de datos** : Queda prohibido commitear o subir archivos de datos(CSV, SQlite, Excel...)
- **Uso exclusivo de la carpeta data/** : Todo dato necesario para desarrollo, pruebas o modelado debe ubicarse localmente en la carpeta `data/`, la cual está excluida del control de versiones mediante `.gitignore`.
- Comprueba siempre `git status` antes de confirmar cualquier cambio para evitar el seguimiento accidental de datos.

## 2. Modelo de ramas

- **`main`**: Rama de producción y versiones finales estables. Solo recibe fusiones desde `dev` al momento de realizar entregas.
- **`dev`**: Rama principal de integración activa del equipo.
- **Regla estricta**: Prohibido hacer commits directamente en `main` o en `dev`.

### Formato de nombres de ramas
Todas las ramas de trabajo nacen de `dev` y deben seguir la nomenclatura `<prefijo>/<numero>-<descripcion-corta>`:
- `feature/<id>-<descripcion>`: Para nuevas funcionalidades (ej. `feature/10-importacion-datos`).
- `fix/<id>-<descripcion>`: Para resolución de errores o bugs (ej. `fix/04-error-parser`).
- `docs/<id>-<descripcion>`: Para creación o actualización de documentación (ej. `docs/02-documentacion-inicial`).

## 3. Flujo de trabajo con ramas

1. **Crear la rama de trabajo** (siempre partiendo de `dev` actualizado):
   ```bash
   git switch dev
   git pull origin dev
   git switch -c feature/03-nombre-funcionalidad
   ```

2. **Desarrollar y commitear**: Realizar cambios atómicos y guardar con commits semánticos.

3. **Actualizar la rama con `dev`** antes de fusionar:
   ```bash
   git fetch origin
   git merge origin/dev
   ```

4. **Fusionar en `dev` y limpiar**:
   ```bash
   git switch dev
   git merge feature/03-nombre-funcionalidad
   git push origin dev
   git branch -d feature/03-nombre-funcionalidad
   git push origin --delete feature/03-nombre-funcionalidad
   ```   

## 4. Estilo de los mensajes de commit

Los mensajes deben seguir el estándar de commits semánticos (*Conventional Commits*), usando descripciones breves en presente o imperativo:

```text 
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```
### Elementos principales:
– **`type`**: Tipo de cambio que introduce el commit
    - `feat`: Nueva funcionalidad para el usuario.
    - `fix`: Corrección de un error.
    - `docs`: Modificaciones en documentación (`README.md`, `CONTRIBUTING.md`, etc.).
    - `refactor`: Reestructuración de código sin alterar el comportamiento externo.
    - `test`: Añadir o modificar pruebas automáticas.
    - `chore`: Tareas de mantenimiento, dependencias o configuración del proyecto.
    - **Aviso de cambio disruptivo**: Puede incluir un signo `!` antes de los dos puntos (ej. `feat!: ...` o `refactor(api)!: ...`) para señalar un **BREAKING CHANGE**.

- **`scope`** *(opcional)*: Módulo o componente afectado, escrito entre paréntesis:
    - Ejemplos: `(gui)`, `(modelo)`, `(datasets)`, `(cli)`.

- **`description`**: Resumen breve, directo y en modo imperativo o presente, sin mayúscula inicial y sin punto final.

- **`body`** *(opcional)*: Párrafo explicativo que detalla el motivo y contexto del cambio. Debe separarse de la descripción por una línea en blanco.

- **`footer`** *(opcional)*: Metadatos finales, referencias a incidencias o notas de incompatibilidad (ej. `Closes #4` o `BREAKING CHANGE: se modifica la firma del método fit()`).

## 5. Gestión de dependencias con `uv`

- El entorno se administra exclusivamente mediante **`uv`**. No está permitido usar `pip install` ni alterar el entorno virtual a mano.
- **Añadir librerías del proyecto**: `uv add <paquete>`
- **Añadir dependencias de desarrollo/testing**: `uv add --dev <paquete>`
- **Actualizar paquetes**: `uv lock --upgrade`
- **Control en Git**: Los archivos `pyproject.toml` y `uv.lock` deben incluirse siempre en el commit al modificar dependencias.
- **Sincronización del entorno**: Tras hacer `git pull` o cambiar de rama, ejecutar `uv sync` para alinear el entorno local.

## 6. Procedimiento para modificar el README o la documentación

1. Crear una rama con el prefijo `docs/` desde `dev` (ej. `docs/05-ampliacion-readme`).
2. Editar los archivos Markdown (`README.md`, `CONTRIBUTING.md` o archivos en `docs/`).
3. Verificar que los bloques de código cierren correctamente con triple tilde inversa y que no existan enlaces rotos.
4. Realizar el commit con prefijo `docs:` (ej. `git commit -m "docs: actualizar instrucciones de arranque en README"`).
5. Fusionar la rama en `dev` siguiendo el procedimiento habitual.