from fpdf import FPDF
from datetime import datetime
import os

# Crear carpeta si no existe
os.makedirs("pdfs", exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.image("Logo Ganesha.png", x=10, y=8, w=30)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "COTIZACIÓN", border=0, ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Página " + str(self.page_no()), align="C")

# Crear documento PDF
pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# --- DATOS DE COTIZACIÓN ---
pdf.set_font("Arial", size=12)
fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
numero_cotizacion = "S02849"

pdf.cell(0, 10, f"Fecha de cotización: {fecha}", ln=True)
pdf.cell(0, 10, f"Número de cotización: {numero_cotizacion}", ln=True)
pdf.ln(5)

# --- REMITENTE ---
pdf.set_font("Arial", "B", 12)
pdf.cell(0, 10, "Remitente:", ln=True)
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 8,
    "Juan Carlos Gomez Estrada\n"
    "Miguel de Cervantes Saavedra #328 Col. El Salto\n"
    "37428 León, Gua\n"
    "RFC: GOEJ890906NR0\n"
    "Tel: 14774761092\n"
    "Correo: mostrador@prisaleon.com.mx"
)
pdf.ln(10)

# --- TABLA DE PRODUCTOS ---
productos = [
    {
        "clave": "33011",
        "descripcion": "PINTAVIN ULTRA 4 AÑOS BLANCO MATE 19L",
        "cantidad": 1,
        "precio_unitario": 1386.37,
    },
    {
        "clave": "R-32001",
        "descripcion": "RIVINOL 5 S BLANCO",
        "cantidad": 1,
        "precio_unitario": 1546.34,
    },
    {
        "clave": "17001",
        "descripcion": "SR BLANCO",
        "cantidad": 1,
        "precio_unitario": 3681.90,
    }
]

# Encabezado de tabla
pdf.set_font("Arial", "B", 11)
pdf.set_fill_color(220, 220, 220)
pdf.cell(30, 10, "CLAVE", 1, 0, "C", True)
pdf.cell(70, 10, "DESCRIPCIÓN", 1, 0, "C", True)
pdf.cell(20, 10, "CANT.", 1, 0, "C", True)
pdf.cell(30, 10, "UNITARIO", 1, 0, "C", True)
pdf.cell(20, 10, "IVA", 1, 0, "C", True)
pdf.cell(20, 10, "TOTAL", 1, 1, "C", True)

# Filas de productos
pdf.set_font("Arial", size=10)
subtotal = 0
iva_total = 0

for prod in productos:
    cantidad = prod["cantidad"]
    unitario = prod["precio_unitario"]
    total = cantidad * unitario
    iva = total * 0.16

    pdf.cell(30, 10, prod["clave"], 1)
    pdf.cell(70, 10, prod["descripcion"][:40], 1)
    pdf.cell(20, 10, f"{cantidad:.2f}", 1, 0, "C")
    pdf.cell(30, 10, f"${unitario:.2f}", 1, 0, "R")
    pdf.cell(20, 10, "16%", 1, 0, "C")
    pdf.cell(20, 10, f"${total:.2f}", 1, 1, "R")

    subtotal += total
    iva_total += iva

# --- TOTALES ---
pdf.ln(5)
pdf.set_font("Arial", "B", 11)
pdf.cell(170, 10, "Importe sin impuestos:", 0, 0, "R")
pdf.cell(20, 10, f"${subtotal:.2f}", 0, 1, "R")
pdf.cell(170, 10, "IVA 16%:", 0, 0, "R")
pdf.cell(20, 10, f"${iva_total:.2f}", 0, 1, "R")
pdf.cell(170, 10, "Total:", 0, 0, "R")
pdf.cell(20, 10, f"${subtotal + iva_total:.2f}", 0, 1, "R")

pdf.output("pdfs/cotizacion_ganesha_demo.pdf")
print("✅ PDF generado correctamente.")
