# Investigación sobre persistencia de modelos de regresión lineal

## 1. Objetivo

Evaluar métodos para guardar y recuperar modelos entrenados de Python junto con sus metadatos, elegir un formato para la aplicación y comprobar experimentalmente la persistencia y sus riesgos de seguridad.

**Decisión propuesta:** `pickle`, con extensión **`.pkl`**. La aplicación deberá cargar únicamente archivos de origen conocido y confiable.

## 2. Métodos investigados

| Criterio | Pickle | Joblib | JSON | Skops |
|---|---|---|---|---|
| Facilidad de uso | Alta | Alta | Media | Alta para modelos compatibles |
| Guarda un estimador entrenado | Sí | Sí | No directamente | Sí, si es compatible |
| Legibilidad | Binario | Binario | Texto legible | Requiere herramientas de inspección |
| Seguridad con archivos desconocidos | Inseguro | Inseguro | No ejecuta código al deserializar | Mayor control mediante revisión de tipos |
| Compatibilidad entre versiones | Limitada por las dependencias | Limitada por las dependencias | Buena, con esquema compatible | Limitada por las dependencias |
| Metadatos adicionales | Mediante diccionario | Mediante diccionario | Campos explícitos | Estructuras compatibles |
| Grandes arrays NumPy | Compatible | Especialmente adecuado | Conversión manual | Compatible según los tipos |

### Pickle

Pickle forma parte de la biblioteca estándar de Python. Permite serializar objetos completos mediante `pickle.dump()` y recuperarlos mediante `pickle.load()`.

Permite guardar un diccionario que contenga tanto el modelo como su información asociada.

Su principal ventaja es que no necesitamos implementar un mecanismo de reconstrucción para cada estimador.

Su inconveniente más relevante es la posibilidad de ejecutar código arbitrario al cargar archivos de origen desconocido.

### Joblib

Joblib ofrece una interfaz similar a Pickle y resulta especialmente útil para modelos con grandes arrays NumPy.

Es habitual en proyectos de `scikit-learn`, pero se basa en Pickle y comparte sus problemas de seguridad.

### JSON

JSON permite guardar información en un formato legible y portable.

Es adecuado para registrar coeficientes, interceptos, columnas, descripciones y métricas.

Sin embargo, no conserva directamente los objetos entrenados de `scikit-learn`, por lo que obliga a implementar su reconstrucción o a reproducir manualmente las operaciones necesarias para predecir.

### Skops

`skops.io` permite guardar modelos compatibles de `scikit-learn` y revisar los tipos desconocidos antes de permitir su carga.

Ofrece un mayor control frente a la deserialización ejecutable de Pickle, aunque es necesario revisar correctamente los tipos que se autorizan.

Se ha investigado documentalmente, pero no se ha incluido en la prueba experimental.

## 3. Seguridad de Pickle y Joblib

La documentación oficial de Python advierte de que deserializar archivos Pickle de origen no confiable puede ejecutar código arbitrario.

Esto ocurre porque la reconstrucción de los objetos puede implicar llamadas a funciones indicadas por el propio archivo.

Joblib utiliza este mecanismo y comparte el riesgo.

### Demostración práctica

Se creó `prototipos/seguridad_pickle.py`, que define una clase con el método `__reduce__()`.

Dicho método permite indicar una función y sus argumentos para que se invoque durante la deserialización.

En nuestro ejemplo se utiliza `print()`, sin realizar operaciones peligrosas.

**Resultado obtenido:**

```text
Antes de pickle.load:
[DEMOSTRACION] Se ejecuto codigo al cargar el archivo
Despues de pickle.load.

Antes de joblib.load:
[DEMOSTRACION] Se ejecuto codigo al cargar el archivo
Despues de joblib.load.
```

El resultado demuestra que se ejecutó una instrucción durante la carga, sin que el código consumidor llamase expresamente a dicha función.

### Conclusión de seguridad

Pickle y Joblib no son seguros para cargar archivos de origen desconocido.

JSON no presenta esta vía concreta de ejecución durante `json.load()`, aunque sus datos deben seguir validándose.

Skops permite inspeccionar tipos desconocidos y autorizar únicamente aquellos en los que se confía.

Para utilizar Pickle, la aplicación deberá limitar la carga a modelos de origen confiable y advertir de este riesgo en el `README.md`.

Una extensión correcta o una validación realizada después de `pickle.load()` no eliminan este riesgo.

## 4. Prueba de concepto

### Datos utilizados

Se utilizó el conjunto `housing.csv`, con 20.640 registros.

La variable objetivo es `median_house_value`.

Para simplificar la prueba se seleccionaron los ocho predictores numéricos y se excluyó la variable categórica `ocean_proximity`.

Se detectaron 207 valores ausentes en `total_bedrooms`.

### Entrenamiento

Se utilizó un `Pipeline` de `scikit-learn` formado por:

1. `SimpleImputer(strategy="median")`.
2. `LinearRegression()`.

La imputación se ajustó exclusivamente con los datos de entrenamiento para evitar fugas de información.

La división fue del 80 % para entrenamiento y 20 % para test, utilizando `random_state=42`.

El pipeline completo, incluido el preprocesamiento aprendido, se guarda junto con sus metadatos.

### Métricas

| Métrica | Entrenamiento | Test |
|---|---:|---:|
| MAE | 50.626,79 | 51.810,09 |
| MSE | 4.811.134.397,88 | 5.059.656.033,13 |
| RMSE | 69.362,34 | 71.131,26 |
| R² | 0,6401 | 0,6139 |

### Tamaño de archivos

Pruebas realizadas con Python 3.13.5, scikit-learn 1.8.0, NumPy 2.3.5 y Joblib 1.5.3.

| Archivo | Tamaño | Contenido |
|---|---:|---|
| `modelo_regresion.pkl` | 2.174 bytes | Modelo completo y metadatos |
| `modelo_regresion.joblib` | 2.581 bytes | Modelo completo y metadatos |
| `modelo_regresion.json` | 1.854 bytes | Parámetros y metadatos, sin objeto de modelo |

Los tamaños dependen del contenido y las opciones de serialización. La representación JSON no contiene el mismo objeto que los formatos binarios.

### Validación de predicciones

Se guardaron y recuperaron los archivos y se compararon las predicciones con las del modelo original.

La comprobación utilizó `numpy.testing.assert_allclose`, con tolerancias `rtol=1e-12` y `atol=1e-8`.

Los tres formatos produjeron resultados equivalentes dentro de dichas tolerancias.

En Pickle y Joblib se recuperó el objeto entrenado. En JSON se reprodujeron las predicciones a partir de sus parámetros, sin recuperar el estimador original.

## 5. Método seleccionado

**Se propone utilizar Pickle (`.pkl`).**

La decisión se fundamenta en los siguientes aspectos:

- Conserva el modelo entrenado directamente, incluidos sus atributos internos.
- Permite persistir un `Pipeline` completo con sus transformaciones.
- Evita implementar lógica propia de reconstrucción de estimadores.
- Facilita ampliar la aplicación a otros algoritmos compatibles.
- Permite guardar el modelo y sus metadatos en un único archivo.
- Forma parte de la biblioteca estándar de Python.

Frente a JSON, Pickle reduce el acoplamiento de la aplicación con los detalles internos de cada estimador.

Frente a Joblib, proporciona una solución general sin dependencias de serialización adicionales. Si posteriormente se incorporan modelos con arrays muy grandes, Joblib podría reconsiderarse.

### Limitaciones

**Seguridad:** solo se podrán cargar archivos de procedencia confiable. Los modelos de terceros desconocidos no deben deserializarse mediante Pickle.

**Compatibilidad:** scikit-learn no garantiza recuperar correctamente estimadores serializados utilizando versiones diferentes de la librería.

**Tipos compatibles:** Pickle admite numerosos objetos Python, pero no absolutamente todos. Por ejemplo, determinadas funciones locales y recursos abiertos no pueden serializarse directamente.

**Intercambio de modelos:** si la aplicación incorpora funciones para compartir modelos entre usuarios, será necesario reconsiderar el formato o implantar mecanismos de confianza verificables antes de la carga.

Estas limitaciones se consideran aceptables para el alcance actual de la aplicación, siempre que se respete la restricción de seguridad indicada.

## 6. Estructura de la información guardada

Se almacenará un diccionario Python con los siguientes campos:

| Campo | Contenido |
|---|---|
| `version_esquema` | Versión de la estructura, inicialmente 1 |
| `modelo` | Objeto `Pipeline` entrenado |
| `tipo_modelo` | Identificación del estimador |
| `columnas_entrada` | Lista ordenada de variables predictoras |
| `columna_salida` | Variable objetivo |
| `formula` | Representación textual de la ecuación |
| `metricas_entrenamiento` | MAE, MSE, RMSE y R² de entrenamiento |
| `metricas_test` | MAE, MSE, RMSE y R² de test |
| `descripcion` | Descripción asociada al modelo |
| `preprocesamiento` | Descripción del tratamiento de datos |
| `entrenamiento` | Información sobre la partición utilizada |
| `entorno` | Versiones de Python, scikit-learn, NumPy y pandas |

El campo `modelo` conserva también los parámetros aprendidos por el imputador. No es necesario reconstruirlo manualmente.

El campo `formula` tiene fines informativos y no debe ejecutarse mediante `eval()`.

La versión del esquema permite detectar cambios futuros en la estructura, pero no garantiza la compatibilidad del estimador ni protege contra archivos maliciosos.

## 7. Guardar y recuperar modelos

Para guardar un modelo:

1. Entrenar el estimador o pipeline.
2. Construir el diccionario con el modelo y sus metadatos.
3. Abrir un archivo `.pkl` en modo binario de escritura.
4. Utilizar `pickle.dump()`.

Para recuperarlo:

1. Comprobar que el archivo procede de una fuente confiable.
2. Abrirlo en modo binario de lectura.
3. Utilizar `pickle.load()`.
4. Validar la estructura recuperada.
5. Recuperar el modelo y utilizar `predict()`.

Las validaciones posteriores a la carga no impiden que un archivo malicioso ejecute código durante la deserialización.

### Ejemplo de código

```python
import pickle

# Guardar un modelo previamente entrenado.
contenido = {
    "version_esquema": 1,
    "modelo": modelo,
    "columnas_entrada": columnas_entrada,
    "columna_salida": columna_salida,
    "formula": formula,
    "metricas_entrenamiento": metricas_train,
    "metricas_test": metricas_test,
    "descripcion": descripcion,
}

with open("modelo.pkl", "wb") as archivo:
    pickle.dump(
        contenido,
        archivo,
        protocol=pickle.HIGHEST_PROTOCOL
    )

# Recuperar UNICAMENTE archivos confiables.
with open("modelo.pkl", "rb") as archivo:
    recuperado = pickle.load(archivo)

modelo_cargado = recuperado["modelo"]
predicciones = modelo_cargado.predict(X_nuevos)

print(recuperado["descripcion"])
print(predicciones)
```

El prototipo completo se encuentra en `prototipos/persistencia_regresion.py`.

## 8. Dificultades y soluciones

**Valores ausentes:** se encontraron valores nulos en `total_bedrooms`. Se incorporó `SimpleImputer` al pipeline para conservar el tratamiento aprendido junto con el modelo.

**Variable categórica:** se excluyó `ocean_proximity` para simplificar el experimento. Podría incorporarse posteriormente mediante transformaciones apropiadas.

**Limitaciones de JSON:** no permitía guardar directamente el estimador. Se utilizó como método comparativo, exportando sus parámetros.

**Reproducción de predicciones:** se compararon los resultados originales y recuperados mediante `assert_allclose`.

**Metadatos:** se decidió agrupar el modelo y su información en un diccionario.

**Seguridad:** se demostró la ejecución de código con Pickle y Joblib y se estableció la necesidad de restringir los archivos admitidos a fuentes confiables.

**Compatibilidad:** se incorporaron las versiones del entorno como metadatos y se documentó la ausencia de garantías de compatibilidad entre versiones distintas de scikit-learn.

## 9. Conclusión

Pickle resulta adecuado para el alcance actual de la aplicación porque permite conservar directamente los modelos entrenados y sus metadatos, facilita su recuperación y permite ampliar el sistema a nuevos estimadores compatibles.

La extensión propuesta es `.pkl`.

La principal condición de esta decisión es la seguridad: no deben deserializarse modelos de origen desconocido.

Esta restricción debe figurar expresamente en el `README.md` y tenerse en cuenta durante la futura integración del sistema de persistencia.

## 10. Referencias

- [Python — módulo Pickle](https://docs.python.org/3/library/pickle.html)
- [Python — módulo JSON](https://docs.python.org/3/library/json.html)
- [scikit-learn — Persistencia de modelos](https://scikit-learn.org/stable/model_persistence.html)
- [Joblib — load](https://joblib.readthedocs.io/en/stable/generated/joblib.load.html)
- [Skops — Persistencia](https://skops.readthedocs.io/en/stable/persistence.html)