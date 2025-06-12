# 📦 IMPORTACIONES
import os
import json
import re
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI

# 🌱 CARGAR VARIABLES DE ENTORNO
load_dotenv()

# 🤖 CONFIGURAR MODELO LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # o "gpt-4"
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 🛠️ HERRAMIENTAS DE AGENTE
def buscar_productos(nombre):
    res = requests.get(f"http://localhost:8000/buscar?nombre={nombre}")
    return res.json()

def agregar_al_carrito(nombre):
    res = requests.post("http://localhost:8000/agregar-al-carrito", json={"nombre": nombre})
    return res.json()

tools = [
    Tool(name="BuscarProducto", func=buscar_productos, description="Busca productos por nombre"),
    Tool(name="AgregarAlCarrito", func=agregar_al_carrito, description="Agrega productos al carrito")
]

# INICIALIZAR AGENTE
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# FUNCIÓN PARA INTERPRETAR MENSAJE
def interpretar_mensaje(mensaje: str):
    system_prompt = """
Eres un asistente de ventas amable y profesional. Tu tarea es interpretar lo que el cliente quiere comprar, consultar o hacer, y devolver una acción en JSON.

Con base en el mensaje del usuario, detecta si quiere:
- Buscar un producto (si quiere saber qué tienes de cierto tipo)
- Agregar un producto al carrito (con o sin cantidad)
- Ver el carrito
- Vaciar el carrito
- Finalizar una compra
- Consultar más información de un producto (precio, características, uso, presentación)

Además:
- Si el cliente menciona una **cantidad** (por ejemplo: “2 botes de pintura blanca”), extrae esa cantidad y el nombre del producto.
- Si NO menciona cantidad, asigna 1 por defecto.
- Si el cliente quiere saber más de un producto (por ejemplo: “¿Qué precio tiene?”, “¿Qué características tiene?”, “¿Para qué sirve?”), interpreta como `consultar_producto`.

Responde SOLO con un JSON como este:

{
  "accion": "consultar_producto",
  "parametros": {
    "nombre": "pintura blanca"
  },
  "respuesta": "Claro, aquí tienes más detalles sobre la pintura blanca."
}

✅ Ajusta nombres largos (“impermeabilizante para techo blanco”) a un nombre base.
✅ Si no entiendes, responde con algo como: “Perdón, ¿podrías decirlo de otra forma?”
✅ NO repitas exactamente el mensaje del usuario.
✅ Devuelve solo un JSON válido.
"""

    prompt = f'Usuario: "{mensaje}"\n\nDevuelve solo el JSON correspondiente.'

    respuesta_obj = llm.invoke(system_prompt + "\n" + prompt)
    respuesta = respuesta_obj.content if hasattr(respuesta_obj, "content") else str(respuesta_obj)

    try:
        json_str_match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if json_str_match:
            return json.loads(json_str_match.group())
        else:
            raise ValueError("No se encontró JSON en la respuesta")
    except Exception as e:
        print("❌ Error interpretando JSON:", e)
        return {
            "accion": "ninguna",
            "parametros": {},
            "respuesta": "Lo siento, no entendí tu solicitud. ¿Puedes intentar de otra forma?"
        }

def eliminar_producto(nombre):
    global carrito
    inicial = len(carrito)
    carrito = [item for item in carrito if item["nombre"].lower() != nombre.lower()]
    if len(carrito) < inicial:
        return {"mensaje": f"✅ Producto '{nombre}' eliminado del carrito."}
    else:
        return {"mensaje": f"⚠️ No se encontró '{nombre}' en el carrito."}

def vaciar_carrito():
    global carrito
    carrito = []
    return {"mensaje": "🧹 Carrito vaciado correctamente."}

Tool(name="VaciarCarrito", func=vaciar_carrito, description="Vacía completamente el carrito"),

# 🧪 RESPUESTA SIMULADA GPT (si no usas agente)
def responder_gpt(pregunta: str):
    return f"Simulación de respuesta a: {pregunta}"
