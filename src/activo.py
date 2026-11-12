from datetime import date

from src.calculadora import Calculadora
from src.operacion import Operacion
from src.pago import Pago


class Activo:
    """Clase base de cualquier instrumento del portafolio."""
    tipo = "Activo"
    categoria = ""     # "Renta fija" | "Renta variable"
    pagos_validos = ()

    def __init__(self, nombre, precio_mercado=0.0):
        self.nombre = nombre
        self.precio_mercado = precio_mercado
        self.ejemplo = False       # True = dato de demostración (no se guarda)
        self.historial = []        # [(fecha, precio)] para ver cómo sube o baja
        self.operaciones = []
        self.pagos = []

    # ---- registro -------------------------------------------------------
    def registrar_operacion(self, op):
        if op.tipo not in ("compra", "venta"):
            raise ValueError("El tipo debe ser compra o venta.")
        if op.cantidad <= 0 or op.precio < 0 or op.comision < 0:
            raise ValueError("Cantidad, precio y comisión deben ser válidos.")
        if op.tipo == "venta" and op.cantidad > self.cantidad() + 1e-9:
            raise ValueError("No puedes vender más de lo que tienes.")
        self.operaciones.append(op)
        # primera valoración: sin precio de mercado se valora al precio de compra
        if (op.tipo == "compra" and self.tipo != "CDT" and self.precio_mercado == 0
                and not self.historial):
            self.actualizar_precio(op.precio, op.fecha)

    def dividendo_usd(self, fecha, usd_por_accion, trm):
        """Dividendo = acciones que tenías ese día × dólares por acción × TRM."""
        acciones = self.cantidad(fecha)
        if acciones <= 0:
            raise ValueError("No tenías acciones de este activo en esa fecha.")
        if usd_por_accion <= 0 or trm <= 0:
            raise ValueError("El dividendo en dólares y la TRM deben ser mayores que cero.")
        return Pago(fecha, "dividendo", acciones * usd_por_accion * trm,
                    usd_por_accion, trm, acciones)

    def registrar_pago(self, pago):
        if pago.tipo not in self.pagos_validos:
            raise ValueError(f"{self.tipo} no admite pagos de tipo {pago.tipo}.")
        if pago.monto <= 0:
            raise ValueError("El monto debe ser mayor que cero.")
        self.pagos.append(pago)

    def actualizar_precio(self, precio, fecha=None):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        fecha = fecha or date.today()
        self.historial = sorted([h for h in self.historial if h[0] != fecha] + [(fecha, precio)])
        self.precio_mercado = self.historial[-1][1]

    def precio_en(self, fecha=None):
        """Precio de mercado a una fecha (usa el historial si existe)."""
        if not self.historial or fecha is None:
            return self.precio_mercado
        previos = [h for h in self.historial if h[0] <= fecha]
        if previos:
            return previos[-1][1]
        compras = [o for o in self.operaciones if o.fecha <= fecha]
        return compras[-1].precio if compras else self.historial[0][1]

    # ---- cifras (hasta=None significa "todo") ---------------------------
    def _ops(self, hasta=None):
        return [o for o in self.operaciones if hasta is None or o.fecha <= hasta]

    def _pagos(self, hasta=None):
        return [p for p in self.pagos if hasta is None or p.fecha <= hasta]

    def cantidad(self, hasta=None):
        return sum(o.cantidad if o.tipo == "compra" else -o.cantidad for o in self._ops(hasta))

    def total_invertido(self, hasta=None):
        return sum(o.valor_bruto() + o.comision for o in self._ops(hasta) if o.tipo == "compra")

    def ingresos_ventas(self, hasta=None):
        return sum(o.flujo_caja() for o in self._ops(hasta) if o.tipo == "venta")

    def total_pagos(self, hasta=None):
        return sum(p.monto for p in self._pagos(hasta))

    def capital_amortizado(self, hasta=None):
        return sum(p.monto for p in self._pagos(hasta) if p.tipo == "capital")

    def total_comisiones(self):
        return sum(o.comision for o in self.operaciones)

    def invertido_neto(self, hasta=None):
        """Capital que sigue puesto: compras menos lo recuperado por ventas."""
        return max(0.0, self.total_invertido(hasta) - self.ingresos_ventas(hasta))

    def valor_actual(self, hoy=None):
        raise NotImplementedError

    def ganancia(self, hoy=None):
        return (self.valor_actual(hoy) + self.ingresos_ventas() + self.total_pagos()
                - self.total_invertido())

    def rentabilidad_acumulada(self, hoy=None):
        return Calculadora.rentabilidad_acumulada(
            self.total_invertido(), self.valor_actual(hoy),
            self.ingresos_ventas() + self.total_pagos())

    def rentabilidad_ea(self, hoy=None):
        hoy = hoy or date.today()
        return Calculadora.xirr(self.flujos() + [(hoy, self.valor_actual(hoy))])

    def libro(self):
        """Estado de cuenta: una fila por movimiento, con el saldo acumulado en pesos.

        acciones = las que tenías ANTES del movimiento; saldo = flujo de dinero acumulado;
        total = saldo + valor de lo que sigues teniendo; variacion = total / invertido.
        """
        eventos = sorted([(o.fecha, 0, o) for o in self.operaciones]
                         + [(p.fecha, 1, p) for p in self.pagos], key=lambda e: (e[0], e[1]))
        filas, acciones, saldo, invertido = [], 0.0, 0.0, 0.0
        for fecha, _, e in eventos:
            f = {"fecha": fecha, "acciones": acciones, "valor_usd": None, "valor_cop": None,
                 "compra": 0.0, "venta": 0.0, "trm": None, "div_usd": None, "div_cop": None,
                 "dividendos": 0.0, "comision": 0.0}
            if isinstance(e, Operacion):
                es_compra = e.tipo == "compra"
                acciones += e.cantidad if es_compra else -e.cantidad
                saldo += e.flujo_caja()
                if es_compra:
                    invertido += e.valor_bruto() + e.comision
                f.update(valor_usd=e.precio_usd or None, valor_cop=e.precio,
                         compra=e.cantidad if es_compra else 0.0,
                         venta=0.0 if es_compra else e.cantidad,
                         trm=e.trm or None, comision=e.comision)
            else:
                saldo += e.monto
                f.update(trm=e.trm or None, div_usd=e.usd_por_accion or None,
                         div_cop=e.monto / acciones if acciones > 0 else None,
                         dividendos=e.monto)
            f["saldo"] = saldo
            f["total"] = saldo + self.valor_actual(fecha)
            f["variacion"] = f["total"] / invertido if invertido else None
            filas.append(f)
        return filas

    def flujos(self):
        """Flujos de dinero reales (sin el valor actual)."""
        f = [(o.fecha, o.flujo_caja()) for o in self.operaciones]
        f += [(p.fecha, p.monto) for p in self.pagos]
        return f

    # ---- persistencia ---------------------------------------------------
    def parametros(self):
        return {}

    def a_dict(self):
        return {"tipo": self.tipo, "nombre": self.nombre,
                "precio_mercado": self.precio_mercado,
                "historial": [[f.isoformat(), p] for f, p in self.historial],
                "params": self.parametros(),
                "operaciones": [o.a_dict() for o in self.operaciones],
                "pagos": [p.a_dict() for p in self.pagos]}
