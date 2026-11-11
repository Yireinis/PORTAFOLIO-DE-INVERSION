from datetime import date
from src.almacenamiento import Almacenamiento
from src.operacion import Operacion
from src.pago import Pago


class DatosEjemplo:
    """Carga un portafolio de demostración (con historial de precios)."""

    @staticmethod
    def cargar(portafolio):
        crear = Almacenamiento.crear_activo
        d = date
        casos = [
            (crear("Acción", "ECOPETROL"),
             [Operacion(d(2025, 2, 10), "compra", 1000, 2400, 12000)],
             [Pago(d(2025, 9, 15), "dividendo", 180000)],
             [(d(2025, 2, 10), 2400), (d(2025, 6, 30), 2250), (d(2025, 10, 31), 2380),
              (d(2026, 2, 27), 2550), (d(2026, 6, 30), 2480), (None, 2650)]),
            (crear("Acción", "BANCOLOMBIA"),
             [Operacion(d(2025, 3, 5), "compra", 100, 52000, 25000),
              Operacion(d(2026, 3, 20), "venta", 40, 56000, 12000)],
             [Pago(d(2025, 10, 1), "dividendo", 240000)],
             [(d(2025, 3, 5), 52000), (d(2025, 7, 31), 54500), (d(2025, 12, 31), 49800),
              (d(2026, 3, 20), 56000), (d(2026, 8, 31), 57400), (None, 58500)]),
            # Cifras ilustrativas en pesos (no son precios reales de mercado)
            (crear("Acción", "COCA-COLA (KO)"),
             [Operacion(d(2025, 5, 12), "compra", 10, 265000, 18000)],
             [Pago(d(2025, 9, 30), "dividendo", 21000), Pago(d(2026, 3, 31), "dividendo", 22000)],
             [(d(2025, 5, 12), 265000), (d(2025, 9, 30), 270000), (d(2026, 1, 30), 262000),
              (d(2026, 6, 30), 275000), (None, 281000)]),
            (crear("Acción", "NIKE (NKE)"),
             [Operacion(d(2025, 7, 8), "compra", 5, 330000, 18000)],
             [Pago(d(2026, 1, 2), "dividendo", 8000)],
             [(d(2025, 7, 8), 330000), (d(2025, 11, 28), 312000), (d(2026, 3, 31), 298000),
              (d(2026, 8, 31), 289000), (None, 285000)]),
            (crear("CDT", "CDT Davivienda", {"tasa_ea": 0.115, "plazo_dias": 360,
                                             "fecha_inicio": d(2025, 6, 1)}),
             [Operacion(d(2025, 6, 1), "compra", 1, 5000000, 0)], [], []),
            (crear("TES", "TES 2030", {"valor_nominal": 100000, "tasa_cupon": 0.0775,
                                        "vencimiento": d(2030, 9, 18)}),
             [Operacion(d(2025, 4, 22), "compra", 20, 98500, 30000)],
             [Pago(d(2026, 4, 22), "interes", 155000)],
             [(d(2025, 4, 22), 98500), (d(2025, 10, 31), 99800), (d(2026, 4, 22), 100400),
              (d(2026, 8, 31), 100900), (None, 101200)]),
        ]
        for activo, ops, pagos, precios in casos:
            if activo.nombre in portafolio.activos:
                continue
            activo.ejemplo = True
            portafolio.agregar_activo(activo)
            for o in ops:
                activo.registrar_operacion(o)
            for p in pagos:
                activo.registrar_pago(p)
            for fecha, precio in precios:
                activo.actualizar_precio(precio, fecha)
