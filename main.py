from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

carrito = []

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
cliente = MongoClient(MONGO_URI)
db = cliente["agente_ventas"]  # Nombre de tu base de datos
coleccion_productos = db["productos"]  # Colección para los productos
coleccion_cotizaciones = db["cotizaciones"]

from fastapi.responses import JSONResponse

@app.get("/productos")
def obtener_productos():
    productos = list(coleccion_productos.find({}, {"_id": 0}))
    return JSONResponse(content=productos)

from fastapi import Query

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

from fastapi import Body

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

from datetime import datetime

from bson import ObjectId  # ⬅️ Asegúrate de importar esto arriba

@app.post("/finalizar-compra")
def finalizar_compra():
    try:
        if not carrito:
            return {"mensaje": "El carrito está vacío. No se puede generar cotización."}

        total = sum(producto["precio"] for producto in carrito)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        cotizacion = {
            "fecha": fecha,
            "productos": [producto.copy() for producto in carrito],
            "total": round(total, 2)
        }

        resultado = coleccion_cotizaciones.insert_one(cotizacion)
        cotizacion["_id"] = str(resultado.inserted_id)

        carrito.clear()

        return {
            "mensaje": f"🧾 Cotización generada el {fecha} por ${total:.2f} y guardada exitosamente.",
            "id_cotizacion": cotizacion["_id"],
            "cotizacion": cotizacion
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.on_event("startup")
def cargar_productos():
    with open("catalogo.json", "r", encoding="utf-8") as archivo:
        productos = json.load(archivo)
    
    if coleccion_productos.count_documents({}) == 0:
        coleccion_productos.insert_many(productos)
        print("✅ Productos cargados exitosamente en MongoDB")
    else:
        print("📦 Los productos ya están en la base de datos")

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
    
    from fastapi import Query

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

from fastapi import Query

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

def generar_pdf_cotizacion(cotizacion: dict) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_title("Cotización")

    pdf.cell(200, 10, txt="🧾 Cotización de Productos", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Fecha: {cotizacion.get('fecha', 'Sin fecha')}", ln=True)

    pdf.ln(10)
    for producto in cotizacion.get("productos", []):
        pdf.cell(200, 10, txt=f"- {producto['nombre']} (${producto['precio']})", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Total: ${cotizacion.get('total', 0)}", ln=True)

    # Guardar el PDF con nombre único
    filename = f"cotizacion_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(filename)

    return filename