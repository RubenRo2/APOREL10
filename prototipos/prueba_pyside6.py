"""
Módulo de prueba para la interfaz gráfica con PySide6.

Este módulo implementa una interfaz gráfica para evaluar 
la viabilidad de PySide6 en el proyecto. Incluye componentes nativos como 
selección de archivos, tabla de datos con scroll automático, desplegables y 
campos de texto con placeholder nativo.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QMessageBox, QGroupBox, QHeaderView
)


class PoCWindow(QMainWindow):
    """
    Ventana principal usando PySide6.
    Configura la estructura visual y la lógica de los eventos (señales y slots).
    """

    def __init__(self):
        """Inicializa la ventana, layouts y componentes gráficos."""
        super().__init__()

        # Configuración Principal
        self.setWindowTitle(
            "PoC Interfaz Gráfica - PySide6 (Nivel Intermedio)"
        )
        self.resize(600, 500)

        # Contenedor central y layout principal (vertical)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Selección de Archivos
        group_file = QGroupBox("Carga de Datos")
        file_layout = QHBoxLayout(group_file)

        self.btn_file = QPushButton("Seleccionar Archivo...")
        self.btn_file.clicked.connect(self.open_file_dialog)

        self.lbl_path = QLabel("Ningún archivo seleccionado")
        self.lbl_path.setStyleSheet("color: gray;")

        file_layout.addWidget(self.btn_file)
        file_layout.addWidget(self.lbl_path)
        file_layout.addStretch()  # Empuja los elementos a la izquierda

        main_layout.addWidget(group_file)

        # 2. Tabla de Datos
        group_table = QGroupBox("Vista Previa de Datos")
        table_layout = QVBoxLayout(group_table)

        self.table = QTableWidget(4, 3)
        cabeceras = ["ID", "Nombre de Sensor", "Valor Registrado"]
        self.table.setHorizontalHeaderLabels(cabeceras)

        # Hacer que las columnas ocupen todo el ancho disponible
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Llenar con datos de ejemplo
        mock_data = [
            ("1", "Sensor Alpha", "45.2 °C"),
            ("2", "Sensor Beta", "12.8 %"),
            ("3", "Sensor Gamma", "89.1 kPa"),
            ("4", "Sensor Delta", "34.5 °C")
        ]

        for row_idx, row_data in enumerate(mock_data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                self.table.setItem(row_idx, col_idx, item)

        table_layout.addWidget(self.table)
        main_layout.addWidget(group_table)

        # 3. Controles de Entrada
        group_inputs = QGroupBox("Configuración y Procesamiento")
        input_layout = QHBoxLayout(group_inputs)

        self.combo_box = QComboBox()
        opciones = ["Opción 1: Procesar", "Opción 2: Limpiar", "Opción 3: Exportar"]
        self.combo_box.addItems(opciones)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Escriba un comentario...")

        input_layout.addWidget(self.combo_box)
        input_layout.addWidget(self.text_input)

        main_layout.addWidget(group_inputs)

        # 4. Botón de Acción Principal
        self.btn_submit = QPushButton("Aplicar y Mostrar Resumen")
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_submit.clicked.connect(self.show_summary_message)

        main_layout.addWidget(self.btn_submit)

    def open_file_dialog(self):
        """
        Abre un cuadro nativo para seleccionar un archivo.
        Actualiza el texto y color de la etiqueta si hay selección.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de datos",
            "",
            "Todos los archivos (*)"
        )
        if file_name:
            self.lbl_path.setText(f"Ruta: {file_name}")
            self.lbl_path.setStyleSheet("color: green;")

    def show_summary_message(self):
        """
        Muestra un cuadro emergente con las opciones elegidas.
        Si el campo de texto está vacío, muestra '[Vacío]'.
        """
        selected_option = self.combo_box.currentText()
        entered_text = self.text_input.text().strip()

        # PySide6 gestiona el placeholder internamente;
        # si text() está vacío, el usuario no escribió nada.
        if not entered_text:
            entered_text = "[Vacío]"

        mensaje = (
            f"Opción seleccionada: {selected_option}\n"
            f"Texto introducido: {entered_text}"
        )

        QMessageBox.information(self, "Resumen de Datos", mensaje)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoCWindow()
    window.show()
    sys.exit(app.exec())
