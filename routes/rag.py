from fastapi import APIRouter
from pydantic import BaseModel
from rag_gpt import interpretar_mensaje
from main import buscar_producto, ver_carrito, agregar_al_carrito, finalizar_compra

router = APIRouter()

class EntradaMensaje(BaseModel):
    mensaje: str

@router.post("/rag-inteligente")
def responder_con_inteligencia(data: EntradaMensaje):
    mensaje_usuario = data.mensaje
    resultado = interpretar_mensaje(mensaje_usuario)

    accion = resultado.get("accion")
    parametros = resultado.get("parametros", {})
    respuesta = resultado.get("respuesta", "")

    if accion == "buscar_producto":
        nombre = parametros.get("nombre")
        return buscar_producto(nombre)
    elif accion == "ver_carrito":
        return ver_carrito()
    elif accion == "agregar_al_carrito":
        nombre = parametros.get("nombre")
        return agregar_al_carrito(nombre)
    elif accion == "finalizar_compra":
        return finalizar_compra()
    return {"respuesta": respuesta}
