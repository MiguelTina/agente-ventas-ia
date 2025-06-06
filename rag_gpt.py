import os
import openai
import pinecone
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings

load_dotenv()

# Configurar APIs
openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT"))

# Conectar a índice
index = pinecone.Index(os.getenv("PINECONE_INDEX"))
embeddings = OpenAIEmbeddings()

def buscar_contexto(pregunta, k=3):
    # Convertir pregunta en vector
    vector = embeddings.embed_query(pregunta)
    
    # Buscar en Pinecone
    resultados = index.query(vector=vector, top_k=k, include_metadata=True)

    # Unir resultados
    bloques = [match["metadata"].get("texto", "") for match in resultados.get("matches", [])]
    return "\n\n".join(bloques)

def responder_gpt(pregunta):
    contexto = buscar_contexto(pregunta)

    mensajes = [
        {"role": "system", "content": "Eres un asistente de ventas experto. Usa el contexto proporcionado para ayudar."},
        {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}
    ]

    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=mensajes,
        temperature=0.3
    )

    return respuesta.choices[0].message["content"]

def interpretar_mensaje(mensaje_usuario):
    mensaje = mensaje_usuario.lower()

    if "ver carrito" in mensaje:
        return {
            "accion": "ver_carrito",
            "parametros": {},
            "respuesta": "Mostrando los productos que tienes en el carrito."
        }
    
    elif "agrega" in mensaje or "añade" in mensaje:
        # Detectar producto entre comillas (opcional)
        import re
        producto = re.findall(r'"([^"]+)"', mensaje)
        nombre = producto[0] if producto else mensaje.split("agrega")[-1].strip()

        return {
            "accion": "agregar_al_carrito",
            "parametros": {"nombre": nombre},
            "respuesta": f"Agregando {nombre} al carrito."
        }

    elif "total" in mensaje or "cuánto debo" in mensaje:
        return {
            "accion": "total_carrito",
            "parametros": {},
            "respuesta": "Calculando el total de tu compra."
        }

    elif "finaliza" in mensaje or "compra" in mensaje or "quiero comprar" in mensaje:
        return {
            "accion": "finalizar_compra",
            "parametros": {},
            "respuesta": "Finalizando tu compra y generando cotización."
        }

    elif "buscar" in mensaje or "tienes" in mensaje:
        import re
        producto = re.findall(r'"([^"]+)"', mensaje)
        nombre = producto[0] if producto else mensaje.split("buscar")[-1].strip()
        return {
            "accion": "buscar_producto",
            "parametros": {"nombre": nombre},
            "respuesta": f"Buscando información sobre {nombre}..."
        }

    return {
        "accion": None,
        "parametros": {},
        "respuesta": "No entendí tu intención. ¿Podrías reformular?"
    }