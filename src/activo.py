from datetime import date


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
