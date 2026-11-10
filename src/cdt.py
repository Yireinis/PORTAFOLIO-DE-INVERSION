from datetime import date, timedelta
from src.activo import Activo


class CDT(Activo):
    """Renta fija: el capital crece a la tasa E. A. pactada hasta el vencimiento."""
    tipo = "CDT"
    categoria = "Renta fija"
    pagos_validos = ("interes", "capital")

    def __init__(self, nombre, tasa_ea, plazo_dias, fecha_inicio):
        super().__init__(nombre)
        self.tasa_ea = tasa_ea            # 0.11 = 11 % E. A.
        self.plazo_dias = plazo_dias
        self.fecha_inicio = fecha_inicio

    def vencimiento(self):
        return self.fecha_inicio + timedelta(days=self.plazo_dias)

    def valor_actual(self, hoy=None):
        hoy = hoy or date.today()
        if self.cantidad(hoy) <= 0:
            return 0.0
        capital = sum(o.valor_bruto() for o in self._ops(hoy) if o.tipo == "compra")
        dias = max(0, min((hoy - self.fecha_inicio).days, self.plazo_dias))
        devengado = capital * (1 + self.tasa_ea) ** (dias / 365)
        # lo que ya se pagó (intereses + capital) deja de estar en el título
        return max(0.0, devengado - self.total_pagos(hoy))

    def parametros(self):
        return {"tasa_ea": self.tasa_ea, "plazo_dias": self.plazo_dias,
                "fecha_inicio": self.fecha_inicio.isoformat()}
