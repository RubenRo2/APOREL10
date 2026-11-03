# Elección de la librería para la interfaz gráfica

## 1. Pruebas y comparativa

Para el desarrollo de la interfaz gráfica del proyecto, el equipo ha evaluado dos librerías distintas: **Tkinter** y **PySide6**. 

A continuación, presentamos un resumen del comportamiento de cada opción frente a los requisitos del proyecto:

| Requisito a implementar | Con Tkinter | Con PySide6 |
| :--- | :--- | :--- |
| **Título de la ventana** | Soportado sin problemas. | Soportado sin problemas. |
| **Botón de selección de archivos** | Funciona correctamente. | Funciona de manera óptima, utilizando la ventana nativa del sistema operativo. |
| **Tabla de datos con desplazamiento (scroll)** | **Poco práctico.** Tkinter no cuenta con tablas reales; requiere adaptar un componente de listas y vincular la barra de desplazamiento de forma manual. | **Excelente.** Incluye un componente de tabla real que gestiona el desplazamiento de forma automática. |
| **Menú desplegable de opciones** | Soportado y fácil de implementar. | Soportado y fácil de implementar. |
| **Cuadro de texto (con texto de ayuda)** | **Requiere trabajo extra.** El componente básico está bien, pero para que el texto de ayuda ("Escriba aquí...") desaparezca al hacer clic, es necesario programar esa acción a mano. | **Muy eficiente.** Incluye de fábrica la propiedad de texto de ayuda, que desaparece automáticamente al interactuar con el cuadro. |
| **Botón con mensaje emergente** | Cumple su función correctamente. | Cumple su función correctamente. |

## 2. Librería seleccionada y justificación

**Librería elegida:** PySide6.

**¿Por qué?** 
Se ha descartado Tkinter por resultar demasiado básico para las necesidades del proyecto. Durante las pruebas, comprobamos que requeriría invertir demasiado tiempo en programar manualmente comportamientos que ya deberían estar resueltos por defecto (como el funcionamiento de una tabla o el borrado automático de los textos indicativos).

Se ha seleccionado PySide6 porque ofrece herramientas mucho más completas. Cuenta con tablas de datos reales, botones de aspecto más moderno y un sistema que reorganiza automáticamente los elementos cuando el usuario cambia el tamaño de la ventana. Esta decisión agilizará el trabajo y evitará complicaciones durante el desarrollo.

## 3. Dificultades encontradas durante las pruebas y cómo se resolvieron

1. **La limitación de las tablas en Tkinter:** Al notar que no existía un componente de tabla nativo, tuvimos que buscar una alternativa adaptando un componente tipo "árbol" y desarrollando código adicional para conectarle una barra de desplazamiento vertical. 
2. **Desajustes al redimensionar la ventana:** En Tkinter, al hacer la ventana más grande, los elementos perdían su alineación original. En PySide6, el reto inicial fue aprender a organizar los componentes dentro de bloques invisibles (llamados *Layouts*), pero una vez asimilado este concepto, la ventana se adaptó a los cambios de tamaño de manera impecable.
3. **El texto de ayuda estático en Tkinter:** El texto indicativo ("Escriba un comentario...") permanecía fijo en el cuadro al intentar escribir. Para solucionarlo, hubo que programar una función específica que detectara el clic del ratón y borrara el contenido. En PySide6, este problema no existió gracias a que la librería ya lo gestiona internamente.



