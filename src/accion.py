from src.activo import Activo


class Accion(Activo):
    """Renta variable: valor = cantidad × precio de mercado."""
    tipo = "Acción"
    categoria = "Renta variable"
    pagos_validos = ("dividendo",)

    def valor_actual(self, hoy=None):
        return max(0.0, self.cantidad(hoy) * self.precio_en(hoy))
