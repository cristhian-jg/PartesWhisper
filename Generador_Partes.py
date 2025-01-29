import os
import re
from fpdf import FPDF
import whisper
import pyaudio
import wave
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

# Función para grabar un audio con pyaudio
def grabar_audio(filename):
    CHUNK = 1024  # Tamaño del buffer
    FORMAT = pyaudio.paInt16  # Formato de los datos de audio
    CHANNELS = 1  # Número de canales (mono)
    RATE = 44100  # Frecuencia de muestreo
    DURATION = 30  # Duración de la grabación en segundos

    # Mostrar mensaje antes de grabar
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText("Pulsa OK cuando estés preparado. Tienes 30 segundos para grabar audio.")
    msg.setWindowTitle("Iniciando Grabación.")
    msg.exec_()

    # Inicializar PyAudio
    audio = pyaudio.PyAudio()

    # Configurar el stream de entrada
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    print("Grabando...")

    # Grabar durante la duración especificada
    for _ in range(0, int(RATE / CHUNK * DURATION)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Grabación finalizada.")

    # Detener el stream y cerrarlo
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Guardar los datos en un archivo WAV
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    # Mostrar mensaje al usuario
    msg.setText(f"Audio guardado en: {filename}")
    msg.exec_()

# Función para transcribir el audio con Whisper
def transcribir_audio(audio):
    modelo = whisper.load_model("medium")
    resultado = modelo.transcribe(audio, language="es")
    texto = resultado['text']
    texto_procesado = texto.replace(".", "").replace(",", "")
    return texto_procesado

# Función para procesar la transcripción y extraer datos
def extraer_datos(transcripcion):
    patrones = {
        "fecha": r"(?i)fecha\s*(.*?)(?=\s*cliente)",
        "cliente": r"(?i)cliente\s*(.*?)(?=\s*domicilio)",
        "domicilio": r"(?i)domicilio\s*(.*?)(?=\s*concepto)",
        "concepto": r"(?i)concepto\s*(.*?)(?=\s*horas)", 
        "horas": r"(?i)horas\s*(.*?)(?:\.|$)"
    }
    datos = {}

    # Buscar cada patrón en la transcripción
    for campo, patron in patrones.items():
        match = re.search(patron, transcripcion)
        if match:
            datos[campo] = match.group(1).strip().title()
        else:
            datos[campo] = "No especificado"

    return datos

# Función para generar el parte en PDF
def generar_parte(fecha, cliente, domicilio, concepto, horas):

    print(f"Fecha: {fecha}", f"Cliente: {cliente}", f"Dirección: {domicilio}", f"Concepto: {concepto}", f"Horas: {horas}", sep="\n")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Encabezado
    pdf.cell(200, 10, text="", ln=True, align="C")
    pdf.ln(10)

    pdf.image("Logo/Logo.png", x=10, y=10, w=30)  # Posición (x, y) y ancho (w)

    # Dimensiones de la página
    page_width = pdf.w  # Ancho total de la página
    margin_right = 10  # Margen derecho
    cell_width = 65  # Ancho de la celda
    cell_height = 10  # Altura de la celda

    # Calcular posición horizontal (alinear a la derecha)
    x_position = page_width - margin_right - cell_width
    pdf.set_x(x_position)

    # Fecha
    pdf.cell(cell_width, cell_height, text="Fecha", border=1, align="C", ln=True)
    pdf.cell(0, 10, text=f"{fecha}", ln=True, align="R")

    # Cliente
    pdf.set_fill_color(84,84,84)
    pdf.set_text_color(255,255,255)
    pdf.cell(60, 10, text=f"Cliente", border=1, align="L", fill=True)

    pdf.set_text_color(0,0,0)

    pdf.cell(0, 10, text=f"{cliente}", border=1, ln=True, align="L")
    

    # Dirección
    pdf.set_fill_color(84,84,84)
    pdf.set_text_color(255,255,255)
    pdf.cell(60, 10, text=f"Dirección", border=1, align="L", fill=True)

    pdf.set_text_color(0,0,0)
    
    pdf.cell(0, 10, text=f"{domicilio}", border=1, ln=True, align="L")

    pdf.ln(10)

    # Concepto
    pdf.set_fill_color(84, 84, 84)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(0, 10, text="Concepto", border=1, align="C", ln=True, fill=True)

    pdf.set_text_color(0, 0, 0)

    concepto_modificado = concepto.replace(",", "\n")

    pdf.multi_cell(0, 10, text=concepto_modificado, border=1, align='C')
    pdf.ln(10)

    # Horas
    pdf.set_fill_color(84,84,84)
    pdf.set_text_color(255,255,255)

    pdf.cell(0, 10, text=f"Horas", border=1, align="C", ln=True, fill=True)

    horas_modificado = horas.replace(",", "\n")

    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 10, text=horas_modificado, border=1, ln=True, align='C')
    pdf.ln(10)

   # Sección de cierre
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Conforme al presente parte, las tareas han sido ejecutadas según lo descrito anteriormente.", ln=True, align='C')
    pdf.ln(10)

    # Firmas
    pdf.ln(10)
    pdf.cell(0, 10, "Cliente: ___________________________", align='C', ln=True)
    pdf.ln(10)

    # Guardar el archivo
    filename = os.path.join("Partes", f"{cliente.replace(' ', '_')}_parte.pdf")
    pdf.output(filename)
    print(f"Parte generado: {filename}")

# Clase principal para la interfaz
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Partes")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        label = QLabel("Generador de Partes")
        label.setStyleSheet("font-size: 18px;")
        layout.addWidget(label)

        instrucciones = QLabel("Instrucciones:\n1. Pulsa comenzar.\n2. Indica donde guardar la grabación.\n3. Pulsa 'OK' para iniciar la grabación.\n4. Revisar en la carpeta 'Partes' el PDF generado.")
        instrucciones.setStyleSheet("font-size:12px;")
        layout.addWidget(instrucciones)

        grabar_btn = QPushButton("Comenzar")
        grabar_btn.clicked.connect(self.procesar_audio)
        layout.addWidget(grabar_btn)

        salir_btn = QPushButton("Salir")
        salir_btn.clicked.connect(self.close)
        layout.addWidget(salir_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def procesar_audio(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Audio", "", "Archivo WAV (*.wav)", options=options
        )
        if filename:
            grabar_audio(filename)
            transcripcion = transcribir_audio("Audio/synthesis.wav")
            print(transcripcion)
            datos = extraer_datos(transcripcion)
            generar_parte(
                datos["fecha"], datos["cliente"], datos["domicilio"], datos["concepto"], datos["horas"]
            )

# Configuración de la aplicación
def main():
    app = QApplication([])
    ventana = MainWindow()
    ventana.show()
    app.exec_()

if __name__ == "__main__":
    main()