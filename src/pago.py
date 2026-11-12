from dataclasses import dataclass
from datetime import date


@dataclass
class Pago:
    """Ingreso recibido: dividendo, interés (cupón) o pago de capital."""
    fecha: date
    tipo: str          # "dividendo" | "interes" | "capital"
    monto: float                 # total recibido en pesos
    usd_por_accion: float = 0.0  # opcional: dividendo por acción en dólares
    trm: float = 0.0             # opcional: TRM del día del pago
    acciones: float = 0.0        # opcional: acciones que tenías ese día

    def a_dict(self):
        return {"fecha": self.fecha.isoformat(), "tipo": self.tipo,
                "monto": self.monto,
                "usd_por_accion": self.usd_por_accion, "trm": self.trm,
                "acciones": self.acciones}

    @classmethod
    def desde_dict(cls, d):
        return cls(date.fromisoformat(d["fecha"]), d["tipo"], d["monto"],
                   d.get("usd_por_accion", 0.0), d.get("trm", 0.0), d.get("acciones", 0.0))
