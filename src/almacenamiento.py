import json
import os
from datetime import date
from src.portafolio import Portafolio
from src.operacion import Operacion
from src.pago import Pago
from src.accion import Accion
from src.cdt import CDT
from src.bono import Bono
from src.tes import TES


class Almacenamiento:
    """Guarda y carga el portafolio en un archivo JSON."""

    @staticmethod
    def crear_activo(tipo, nombre, params=None, precio=0.0):
        p = params or {}
        fecha = lambda s: s if isinstance(s, date) else date.fromisoformat(s)
        if tipo == "Acción":
            return Accion(nombre, precio)
        if tipo == "CDT":
            return CDT(nombre, p["tasa_ea"], int(p["plazo_dias"]), fecha(p["fecha_inicio"]))
        if tipo in ("Bono", "TES"):
            clase = Bono if tipo == "Bono" else TES
            return clase(nombre, p["valor_nominal"], p["tasa_cupon"],
                         fecha(p["vencimiento"]), precio)
        raise ValueError(f"Tipo de activo desconocido: {tipo}")

    @staticmethod
    def guardar(portafolio, ruta):
        os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
        datos = {"activos": [a.a_dict() for a in portafolio.activos.values()
                              if not a.ejemplo]}
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    @staticmethod
    def cargar(ruta):
        portafolio = Portafolio()
        if not os.path.exists(ruta):
            return portafolio
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        for d in datos["activos"]:
            a = Almacenamiento.crear_activo(d["tipo"], d["nombre"], d["params"],
                                            d.get("precio_mercado", 0.0))
            a.historial = [(date.fromisoformat(f), p) for f, p in d.get("historial", [])]
            a.operaciones = [Operacion.desde_dict(o) for o in d["operaciones"]]
            a.pagos = [Pago.desde_dict(p) for p in d["pagos"]]
            portafolio.agregar_activo(a)
        return portafolio
