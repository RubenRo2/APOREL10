"""
Módulo de prueba para la interfaz gráfica con Tkinter.

Este módulo implementa una interfaz gráfica para evaluar 
la viabilidad de Tkinter en el proyecto. Incluye componentes como 
selección de archivos, tabla de datos, desplegables y campos de texto.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def open_file_dialog():
    """
    Abre un cuadro de diálogo para que el usuario seleccione un archivo.

    Si el usuario selecciona un archivo válido, actualiza la etiqueta de 
    la interfaz (lbl_path) para mostrar la ruta y cambia su color a verde.
    """
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo de datos"
    )
    if file_path:
        lbl_path.config(text=f"Ruta: {file_path}", fg="green")


def show_summary_message():
    """
    Recopila los datos y muestra un cuadro de diálogo de resumen.

    Obtiene el valor seleccionado en el desplegable y el texto 
    introducido. Si el texto está vacío o contiene el placeholder, 
    se asigna '[Vacío]'.
    """
    selected_option = combo_box.get()
    entered_text = text_input.get()

    # Validar si tiene el texto por defecto o está vacío
    if entered_text == "Escriba un comentario..." or not entered_text.strip():
        entered_text = "[Vacío]"

    mensaje = (
        f"Opción seleccionada: {selected_option}\n"
        f"Texto introducido: {entered_text}"
    )

    messagebox.showinfo("Resumen de Datos", mensaje)


def clear_placeholder(event):
    """
    Borra el texto de ayuda cuando el usuario hace clic en el input.

    Args:
        event: Objeto de evento proporcionado por Tkinter.
    """
    if text_input.get() == "Escriba un comentario...":
        text_input.delete(0, tk.END)


# Configuración Principal
root = tk.Tk()
root.title("PoC Interfaz Gráfica - Nivel Intermedio")
root.geometry("600x500")
root.config(padx=20, pady=20)  # Añadir márgenes generales a la ventana

FUENTE_NORMAL = ("Arial", 10)
FUENTE_TITULO = ("Arial", 10, "bold")

# 1. Selección de Archivos
frame_file = tk.LabelFrame(
    root,
    text="Carga de Datos",
    font=FUENTE_TITULO,
    padx=10,
    pady=10
)
frame_file.pack(fill="x", pady=10)

btn_file = tk.Button(
    frame_file,
    text="Seleccionar Archivo...",
    command=open_file_dialog,
    font=FUENTE_NORMAL,
    bg="#e0e0e0"
)
btn_file.pack(side="left", padx=10)

lbl_path = tk.Label(
    frame_file,
    text="Ningún archivo seleccionado",
    font=FUENTE_NORMAL,
    fg="gray"
)
lbl_path.pack(side="left")

# 2. Tabla de Datos
frame_table = tk.LabelFrame(
    root,
    text="Vista Previa de Datos",
    font=FUENTE_TITULO,
    padx=10,
    pady=10
)
frame_table.pack(fill="both", expand=True, pady=10)

columns = ("id", "nombre", "valor")
tree = ttk.Treeview(
    frame_table,
    columns=columns,
    show="headings",
    height=6
)

tree.heading("id", text="ID")
tree.heading("nombre", text="Nombre de Sensor")
tree.heading("valor", text="Valor Registrado")

tree.column("id", width=50)
tree.column("nombre", width=200)
tree.column("valor", width=150)

scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
tree.pack(side="left", fill="both", expand=True)

# Datos de ejemplo
MOCK_DATA = [
    ("1", "Sensor Alpha", "45.2 °C"),
    ("2", "Sensor Beta", "12.8 %"),
    ("3", "Sensor Gamma", "89.1 kPa"),
    ("4", "Sensor Delta", "34.5 °C")
]

for item in MOCK_DATA:
    tree.insert("", tk.END, values=item)

# 3. Controles de Entrada
frame_inputs = tk.LabelFrame(
    root,
    text="Configuración y Procesamiento",
    font=FUENTE_TITULO,
    padx=10,
    pady=10
)
frame_inputs.pack(fill="x", pady=10)

opciones_combo = [
    "Opción 1: Procesar",
    "Opción 2: Limpiar",
    "Opción 3: Exportar"
]

combo_box = ttk.Combobox(
    frame_inputs,
    values=opciones_combo,
    state="readonly",
    font=FUENTE_NORMAL
)
combo_box.current(0)
combo_box.pack(side="left", padx=10)

text_input = tk.Entry(frame_inputs, font=FUENTE_NORMAL, width=30)
text_input.insert(0, "Escriba un comentario...")
text_input.bind("<FocusIn>", clear_placeholder)
text_input.pack(side="left", padx=10, fill="x", expand=True)

# 4. Botón de Acción Principal
btn_submit = tk.Button(
    root,
    text="Aplicar y Mostrar Resumen",
    command=show_summary_message,
    font=FUENTE_TITULO,
    bg="#4CAF50",
    fg="white",
    padx=10,
    pady=5
)
btn_submit.pack(pady=15)

if __name__ == "__main__":
    root.mainloop()
