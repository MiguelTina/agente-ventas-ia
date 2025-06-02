# 🧠 Agente de Ventas IA - API de Cotizaciones

Este proyecto es una API desarrollada en **Python con FastAPI**, que funciona como un agente de ventas inteligente. Permite:

- Buscar productos por nombre o categoría.
- Agregar productos a un carrito virtual.
- Generar cotizaciones con total y lista de productos.
- Guardar las cotizaciones en **MongoDB**.
- Generar un archivo **PDF de la cotización** automáticamente.
- Consultar historial, última cotización o filtrar por fecha.
- ¡Todo listo para integrarse con WhatsApp, n8n o tu CRM!

---

## ⚙️ Requisitos

- Python 3.10 o superior
- MongoDB (Atlas o local)
- Git
- VS Code (opcional pero recomendado)

---

## 🚀 Instalación local (Linux o Windows)

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/agente-ventas-ia.git
cd agente-ventas-ia

# 2. Crear entorno virtual
python -m venv env

# 3. Activar entorno virtual
# En Windows
env\Scripts\activate

# En Linux/macOS
source env/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

| Método | Ruta                    | Descripción                             |
| ------ | ----------------------- | --------------------------------------- |
| GET    | `/productos`            | Ver todo el catálogo                    |
| GET    | `/buscar?nombre=...`    | Buscar por nombre                       |
| GET    | `/categoria?nombre=...` | Filtrar por categoría                   |
| POST   | `/agregar-al-carrito`   | Agrega un producto al carrito           |
| GET    | `/ver-carrito`          | Ver el contenido del carrito            |
| GET    | `/total`                | Ver el total del carrito                |
| POST   | `/finalizar-compra`     | Genera cotización y PDF + guarda en BD  |
| GET    | `/historial`            | Ver todas las cotizaciones              |
| GET    | `/cotizaciones/fecha`   | Filtrar cotizaciones por rango de fecha |
| GET    | `/ultima-cotizacion`    | Ver la cotización más reciente          |

🧠 Integración futura
 Envío de cotización por WhatsApp

 Integración con n8n para flujos automáticos

 Integración con CRM

 Hosting en VPS o Render

 Soporte multiusuario

🛡️ Seguridad
Se excluyen archivos sensibles como .env y PDF del control de versiones.

Se puede agregar validación JWT en endpoints privados (futuro).

🤝 Autor
Desarrollado por [Mau] con apoyo de IA para acelerar el desarrollo de soluciones inteligentes.

🧠 ¿Preguntas o mejoras?
¡Cualquier PR o sugerencia es bienvenida! Este bot de ventas está en evolución constante para integrarse con plataformas reales como WhatsApp y automatizadores como n8n.


---

4. Guarda el archivo (`Ctrl+S`).
5. Súbelo con:

```bash
git add README.md
git commit -m "Agregar documentación del proyecto"
git push origin main

