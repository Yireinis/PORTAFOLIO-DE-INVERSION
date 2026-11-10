from src.activo import Activo


class Bono(Activo):
    """Renta fija con cupones. El precio de mercado es por título (en pesos)."""
    tipo = "Bono"
    categoria = "Renta fija"
    pagos_validos = ("interes", "capital")

    def __init__(self, nombre, valor_nominal, tasa_cupon, vencimiento,
                 precio_mercado=0.0):
        super().__init__(nombre, precio_mercado)
        self.valor_nominal = valor_nominal
        self.tasa_cupon = tasa_cupon      # 0.08 = 8 % anual
        self.vencimiento = vencimiento

    def valor_actual(self, hoy=None):
        return max(0.0, self.cantidad(hoy) * self.precio_en(hoy) - self.capital_amortizado(hoy))

    def parametros(self):
        return {"valor_nominal": self.valor_nominal, "tasa_cupon": self.tasa_cupon,
                "vencimiento": self.vencimiento.isoformat()}
