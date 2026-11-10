from dataclasses import dataclass
from datetime import date


@dataclass
class Operacion:
    """Compra o venta de un activo (con la comisión cobrada por el bróker)."""
    fecha: date
    tipo: str          # "compra" | "venta"
    cantidad: float
    precio: float      # precio por unidad
    comision: float = 0.0

    def valor_bruto(self):
        return self.cantidad * self.precio

    def flujo_caja(self):
        """Compra: sale dinero (negativo). Venta: entra dinero (positivo)."""
        if self.tipo == "compra":
            return -(self.valor_bruto() + self.comision)
        return self.valor_bruto() - self.comision

    def a_dict(self):
        return {"fecha": self.fecha.isoformat(), "tipo": self.tipo,
                "cantidad": self.cantidad, "precio": self.precio,
                "comision": self.comision}

    @classmethod
    def desde_dict(cls, d):
        return cls(date.fromisoformat(d["fecha"]), d["tipo"], d["cantidad"],
                   d["precio"], d.get("comision", 0.0))
