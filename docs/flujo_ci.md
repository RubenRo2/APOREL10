# Inegración Continua (CI) con Github Actions

El archivo `.github/worlflows/ci.yml` define nuestro flujo de trabajo automatizado. Se ejecuta automáticamente con cada `push` a cualquier rama.

## Secuencia de ejecución
**Checkout del código**: Descarga el repositorio en el servidor.
2. **Instalar uv**: Instala el gestor de paquetes activando la caché.
3. **Configurar Python**: Lee el archivo `.python-version` para usar la versión exacta.
4. **Instalar dependencias del sistema**: Instala `xvfb` para simular una pantalla y evitar que PySide6 falle en el servidor sin monitor.
5. **Instalar dependencias del proyecto**: Ejecuta `uv sync --locked`. Falla intencionadamente si `uv.lock` no está actualizado.
6. **Ejecutar pruebas**: Lanza `xvfb-run -a uv run pytest` para ejecutar los tests en la pantalla virtual.
