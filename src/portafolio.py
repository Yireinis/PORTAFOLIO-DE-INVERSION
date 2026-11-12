from datetime import date, timedelta
from src.calculadora import Calculadora


class Portafolio:
    """Agrupa los activos y consolida los resultados."""

    def __init__(self):
        self.activos = {}

    def agregar_activo(self, activo):
        if activo.nombre in self.activos:
            raise ValueError("Ya existe un activo con ese nombre.")
        self.activos[activo.nombre] = activo

    def eliminar_activo(self, nombre):
        self._activo(nombre)
        del self.activos[nombre]

    def hay_ejemplo(self):
        return any(a.ejemplo for a in self.activos.values())

    def quitar_ejemplo(self):
        self.activos = {n: a for n, a in self.activos.items() if not a.ejemplo}

    def borrar_todo(self):
        self.activos = {}

    def _activo(self, nombre):
        if nombre not in self.activos:
            raise ValueError("Ese activo no existe: créalo en la pestaña Activos "
                             "(o escribe su nombre al registrar una compra de acciones).")
        return self.activos[nombre]

    def registrar_operacion(self, nombre, operacion):
        self._activo(nombre).registrar_operacion(operacion)

    def registrar_pago(self, nombre, pago):
        self._activo(nombre).registrar_pago(pago)

    def registrar_dividendo_usd(self, nombre, fecha, usd_por_accion, trm):
        activo = self._activo(nombre)
        activo.registrar_pago(activo.dividendo_usd(fecha, usd_por_accion, trm))

    def libro(self, nombre):
        return self._activo(nombre).libro()

    def actualizar_precio(self, nombre, precio):
        self._activo(nombre).actualizar_precio(precio)

    # ---- consolidado ----------------------------------------------------
    def total_invertido(self):
        return sum(a.total_invertido() for a in self.activos.values())

    def valor_actual(self, hoy=None):
        hoy = hoy or date.today()
        return sum(a.valor_actual(hoy) for a in self.activos.values())

    def ingresos(self):
        """Dinero ya recibido: ventas netas + dividendos/intereses/capital."""
        return sum(a.ingresos_ventas() + a.total_pagos() for a in self.activos.values())

    def comisiones(self):
        return sum(a.total_comisiones() for a in self.activos.values())

    def distribucion(self, hoy=None):
        hoy = hoy or date.today()
        d = {"Renta fija": 0.0, "Renta variable": 0.0}
        for a in self.activos.values():
            d[a.categoria] += a.valor_actual(hoy)
        return d

    def flujos(self, hoy=None):
        hoy = hoy or date.today()
        f = [x for a in self.activos.values() for x in a.flujos()]
        f.append((hoy, self.valor_actual(hoy)))   # se "liquida" el portafolio hoy
        return f

    def rentabilidad_acumulada(self, hoy=None):
        return Calculadora.rentabilidad_acumulada(
            self.total_invertido(), self.valor_actual(hoy), self.ingresos())

    def rentabilidad_ea(self, hoy=None):
        return Calculadora.xirr(self.flujos(hoy))

    def serie(self, hoy=None):
        """Evolución en el tiempo: [(fecha, valor del portafolio, capital neto invertido)]."""
        hoy = hoy or date.today()
        fechas = [o.fecha for a in self.activos.values() for o in a.operaciones]
        if not fechas or min(fechas) >= hoy:
            return []
        ini = min(fechas)
        paso = max(15, (hoy - ini).days // 60)
        dias, d = [], ini
        while d < hoy:
            dias.append(d)
            d += timedelta(days=paso)
        dias.append(hoy)
        return [(d, self.valor_actual(d),
                 sum(a.invertido_neto(d) for a in self.activos.values())) for d in dias]

    def resumen(self, hoy=None):
        hoy = hoy or date.today()
        invertido, actual = self.total_invertido(), self.valor_actual(hoy)
        return {"invertido": invertido, "valor_actual": actual,
                "ingresos": self.ingresos(), "comisiones": self.comisiones(),
                "ganancia": actual + self.ingresos() - invertido,
                "acumulada": self.rentabilidad_acumulada(hoy),
                "ea": self.rentabilidad_ea(hoy),
                "distribucion": self.distribucion(hoy)}
