from dataclasses import dataclass
from datetime import date


@dataclass
class Pago:
    """Ingreso recibido: dividendo, interés (cupón) o pago de capital."""
    fecha: date
    tipo: str          # "dividendo" | "interes" | "capital"
    monto: float

    def a_dict(self):
        return {"fecha": self.fecha.isoformat(), "tipo": self.tipo,
                "monto": self.monto}

    @classmethod
    def desde_dict(cls, d):
        return cls(date.fromisoformat(d["fecha"]), d["tipo"], d["monto"])
