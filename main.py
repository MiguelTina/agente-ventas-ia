from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from fpdf import FPDF
from rag_gpt import interpretar_mensaje,responder_gpt
import uuid
import os

carrito = []

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

from routes.rag import router as rag_router
app.include_router(rag_router)

# Conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
cliente = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = cliente["agente_ventas"]  # Nombre de tu base de datos
coleccion_productos = db["productos"]  # Colección para los productos
coleccion_cotizaciones = db["cotizaciones"]

@app.get("/productos")
def obtener_productos():
    productos = list(coleccion_productos.find({}, {"_id": 0}))
    return JSONResponse(content=productos)

@app.get("/buscar")
def buscar_producto(nombre: str = Query(..., description="Nombre del producto a buscar")):
    resultados = list(coleccion_productos.find(
        {"nombre": {"$regex": nombre, "$options": "i"}},  # i = ignorar mayúsculas
        {"_id": 0}
    ))
    if resultados:
        return {"resultados": resultados}
    else:
        return {"mensaje": f"No se encontraron productos que coincidieran con \"{nombre}\"."}
    
@app.get("/categoria")
def buscar_por_categoria(nombre: str = Query(..., description="Nombre exacto de la categoría")):
    resultados = list(coleccion_productos.find(
        {"categoria": nombre.lower()},  # comparación directa
        {"_id": 0}
    ))

    if resultados:
        return {"resultados": resultados}
    else:
        return {"mensaje": f"No se encontraron productos en la categoría '{nombre}'."}

@app.post("/agregar-al-carrito")
def agregar_al_carrito(nombre: str = Body(..., embed=True)):
    producto = coleccion_productos.find_one(
        {"nombre": {"$regex": nombre, "$options": "i"}},
        {"_id": 0}
    )
    if producto:
        carrito.append(producto)
        return {"mensaje": f"✅ '{producto['nombre']}' agregado al carrito."}
    else:
        return {"mensaje": f"❌ No se encontró ningún producto que coincida con '{nombre}'."}

@app.get("/ver-carrito")
def ver_carrito():
    carrito_serializable = []

    for producto in carrito:
        item = producto.copy()
        item["_id"] = str(item["_id"]) if "_id" in item else None
        carrito_serializable.append(item)

    return {"carrito": carrito_serializable}

@app.get("/total")
def total_carrito():
    if not carrito:
        return {"mensaje": "El carrito está vacío, no hay total que calcular."}

    total = sum(producto["precio"] for producto in carrito)
    return {"total": f"${total:.2f}", "productos_en_carrito": len(carrito)}

@app.delete("/vaciar-carrito")
def vaciar_carrito():
    carrito.clear()
    return {"mensaje": "🧹 Carrito vaciado correctamente."}

@app.get("/")
def read_root():
    return {"mensaje": "¡El agente de ventas IA está activo!"} 

def generar_pdf_cotizacion(cotizacion: dict) -> str:
    
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

    os.makedirs("pdfs", exist_ok=True)
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    fecha = cotizacion.get("fecha", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    numero = cotizacion.get("_id", "S/N")

    # Encabezado
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Fecha de cotización: {fecha}", ln=True)
    pdf.cell(0, 10, f"Número de cotización: {numero}", ln=True)
    pdf.ln(5)

    # Remitente
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

    # Cliente
    cliente = cotizacion.get("cliente", {})

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Cliente:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8,
    f"{cliente.get('nombre', '')}\n"
    f"{cliente.get('direccion', '')}\n"
    f"{cliente.get('cp', '')} {cliente.get('ciudad', '')}, {cliente.get('estado', '')}\n"
    f"RFC: {cliente.get('rfc', '')}\n"
    f"Correo: {cliente.get('correo', '')}\n"
    f"Tel: {cliente.get('telefono', '')}"
)
    pdf.ln(10)


    # Tabla de productos
    productos = cotizacion.get("productos", [])
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(80, 10, "DESCRIPCIÓN", 1, 0, "C", True)
    pdf.cell(30, 10, "PRECIO", 1, 0, "C", True)
    pdf.cell(30, 10, "IVA", 1, 0, "C", True)
    pdf.cell(30, 10, "TOTAL", 1, 1, "C", True)

    pdf.set_font("Arial", size=10)
    subtotal = 0
    iva_total = 0

    for p in productos:
        nombre = p["nombre"]
        precio = p["precio"]
        iva = precio * 0.16
        total = precio + iva

        pdf.cell(80, 10, nombre[:40], 1)
        pdf.cell(30, 10, f"${precio:.2f}", 1, 0, "R")
        pdf.cell(30, 10, "16%", 1, 0, "C")
        pdf.cell(30, 10, f"${total:.2f}", 1, 1, "R")

        subtotal += precio
        iva_total += iva

    # Totales
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(140, 10, "Importe sin impuestos:", 0, 0, "R")
    pdf.cell(30, 10, f"${subtotal:.2f}", 0, 1, "R")
    pdf.cell(140, 10, "IVA (16%):", 0, 0, "R")
    pdf.cell(30, 10, f"${iva_total:.2f}", 0, 1, "R")
    pdf.cell(140, 10, "Total:", 0, 0, "R")
    pdf.cell(30, 10, f"${subtotal + iva_total:.2f}", 0, 1, "R")

    # Guardar PDF
    filename = f"cotizacion_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(f"pdfs/{filename}")
    return filename

@app.post("/finalizar-compra")
def finalizar_compra():
    try:
        if not carrito:
            return {"mensaje": "El carrito está vacío. No se puede generar cotización."}

        total = sum(producto["precio"] for producto in carrito)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        cliente = {
    "nombre": "Luis Torres",
    "direccion": "Av. Insurgentes 123, Col. Centro",
    "cp": "37000",
    "ciudad": "León",
    "estado": "Guanajuato",
    "rfc": "TORL850102ABC",
    "correo": "luis@email.com",
    "telefono": "4771234567"
}

        cotizacion = {
            "fecha": fecha,
            "cliente": cliente,
            "productos": [producto.copy() for producto in carrito],
            "total": round(total, 2)
        }

        resultado = coleccion_cotizaciones.insert_one(cotizacion)
        cotizacion["_id"] = str(resultado.inserted_id)

        # ✅ Aquí generamos el PDF
        filename = generar_pdf_cotizacion(cotizacion)

        carrito.clear()

        return {
            "mensaje": f"Cotización generada el {fecha} por ${total:.2f} y guardada exitosamente.",
            "archivo_pdf": filename,
            "descarga_pdf": f"/descargar-pdf/{filename}",
            "id_cotizacion": cotizacion["_id"],
            "cotizacion": cotizacion
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
    
@app.get("/descargar-pdf/{filename}")
def descargar_pdf(filename: str):
    path = f"pdfs/{filename}"
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
    return FileResponse(path, media_type="application/pdf", filename=filename)

@app.post("/cotizar-directo")
def cotizar_directo(datos: dict):
    cliente = datos.get("cliente", {})
    productos = datos.get("productos", [])

    total = sum(p["precio"] for p in productos)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    cotizacion = {
        "fecha": fecha,
        "cliente": cliente,
        "productos": productos,
        "total": round(total, 2)
    }

    resultado = coleccion_cotizaciones.insert_one(cotizacion)
    cotizacion["_id"] = str(resultado.inserted_id)

    filename = generar_pdf_cotizacion(cotizacion)

    return {
        "mensaje": f"Cotización generada el {fecha} por ${total:.2f}",
        "archivo_pdf": filename,
        "descarga_pdf": f"/descargar-pdf/{filename}",
        "id_cotizacion": cotizacion["_id"],
        "cotizacion": cotizacion
    }
   
@app.on_event("startup")
def cargar_productos():
    with open("catalogo.json", "r", encoding="utf-8") as archivo:
        productos = json.load(archivo)
    
    if coleccion_productos.count_documents({}) == 0:
        coleccion_productos.insert_many(productos)
        print("✅ Productos cargados exitosamente en MongoDB")
    else:
        print("📦 Los productos ya están en la base de datos")

@app.post("/gpt-asistente")
def asistente_gpt(pregunta: str = Body(..., embed=True)):
    respuesta = responder_gpt(pregunta)
    return {"respuesta": respuesta}

@app.get("/cotizaciones")
def obtener_cotizaciones():
    cotizaciones = list(coleccion_cotizaciones.find())
    for cot in cotizaciones:
        cot["_id"] = str(cot["_id"])  # Convertimos el ObjectId a string
    return JSONResponse(content={"cotizaciones": cotizaciones})

@app.get("/cotizaciones/fecha")
def obtener_cotizaciones_por_fecha(
    inicio: str = Query(..., description="Fecha inicio en formato dd/mm/yyyy"),
    fin: str = Query(..., description="Fecha fin en formato dd/mm/yyyy")
):
    try:
        fecha_inicio = datetime.strptime(inicio, "%d/%m/%Y")
        fecha_fin = datetime.strptime(fin, "%d/%m/%Y")
        fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)

        cotizaciones = list(coleccion_cotizaciones.find())
        resultado = []

        for cot in cotizaciones:
            try:
                fecha_valor = cot.get("fecha", "")
                if isinstance(fecha_valor, str) and fecha_valor.strip() != "":
                    fecha_cot = datetime.strptime(fecha_valor, "%d/%m/%Y %H:%M:%S")
                    if fecha_inicio <= fecha_cot <= fecha_fin:
                        cot["_id"] = str(cot["_id"])
                        resultado.append(cot)
            except Exception as e:
                print("⚠️ Error procesando cotización:", str(cot.get("_id", "sin_id")), "|", e)
                continue

        return JSONResponse(content={"cotizaciones": resultado})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/gpt-asistente")
def gpt_asistente(pregunta: str = Body(..., embed=True)):
    respuesta = responder_gpt(pregunta)
    return {"respuesta": respuesta}

@app.get("/cotizaciones/buscar")
def buscar_cotizaciones_por_palabra(palabra: str = Query(..., description="Palabra clave para buscar en productos")):
    try:
        cotizaciones = list(coleccion_cotizaciones.find())
        resultado = []

        for cot in cotizaciones:
            for producto in cot.get("productos", []):
                # Buscamos en nombre y características (ignorando mayúsculas)
                nombre = producto.get("nombre", "").lower()
                caracteristicas = producto.get("características", "").lower()
                if palabra.lower() in nombre or palabra.lower() in caracteristicas:
                    cot["_id"] = str(cot["_id"])
                    resultado.append(cot)
                    break  # Ya encontramos una coincidencia en esta cotización

        return JSONResponse(content={"cotizaciones": resultado})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/cotizaciones/{cotizacion_id}")
def obtener_cotizacion_por_id(cotizacion_id: str):
    try:
        cotizacion = coleccion_cotizaciones.find_one({"_id": ObjectId(cotizacion_id)})
        if cotizacion:
            cotizacion["_id"] = str(cotizacion["_id"])
            return JSONResponse(content={"cotizacion": cotizacion})
        else:
            return JSONResponse(status_code=404, content={"mensaje": "❌ Cotización no encontrada."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/historial")
def obtener_historial():
    historial = []
    cotizaciones = list(coleccion_cotizaciones.find())
    for cot in cotizaciones:
        resumen = {
            "id": str(cot["_id"]),
            "fecha": cot.get("fecha", "Sin fecha"),
            "total": cot.get("total", 0)
        }
        historial.append(resumen)
    return JSONResponse(content={"historial": historial})

@app.get("/ultima-cotizacion")
def obtener_ultima_cotizacion():
    try:
        cotizacion = coleccion_cotizaciones.find_one(sort=[("_id", -1)])
        if cotizacion:
            resumen = {
                "fecha": cotizacion.get("fecha", "Sin fecha"),
                "total": cotizacion.get("total", 0),
                "productos": len(cotizacion.get("productos", []))
            }
            return JSONResponse(content={"ultima_cotizacion": resumen})
        else:
            return JSONResponse(content={"mensaje": "No hay cotizaciones registradas."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
    from fpdf import FPDF
import uuid

for route in app.routes:
    print(f"🔍 Ruta cargada: {route.path} - {route.methods}")