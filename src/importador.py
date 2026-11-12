import copy
import csv
from datetime import date, datetime

from src.almacenamiento import Almacenamiento
from src.calculadora import Calculadora
from src.operacion import Operacion
from src.pago import Pago

COLUMNAS = ["fecha", "movimiento", "tipo_activo", "activo", "cantidad", "precio",
            "comision", "monto", "tasa", "plazo_dias", "fecha_ref", "valor_nominal",
            "precio_usd", "trm", "usd_por_accion"]
MOVIMIENTOS = ("compra", "venta", "dividendo", "interes", "capital", "precio")
TIPOS = {"accion": "Acción", "acción": "Acción", "cdt": "CDT", "bono": "Bono", "tes": "TES"}


class Importador:
    """Importa movimientos desde un CSV (Trii, otro bróker o Excel guardado como CSV)."""

    @staticmethod
    def _num(txt, defecto=None):
        txt = (txt or "").strip().replace(" ", "").replace("$", "").replace(",", ".")
        if not txt:
            if defecto is None:
                raise ValueError("falta un número")
            return defecto
        return float(txt)

    @staticmethod
    def _fecha(txt):
        txt = (txt or "").strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(txt, fmt).date()
            except ValueError:
                pass
        raise ValueError(f"fecha no válida «{txt}» (usa AAAA-MM-DD o DD/MM/AAAA)")

    @staticmethod
    def plantilla(ruta):
        base = ["", "", "", "", "", "", "", ""]          # tasa ... usd_por_accion vacíos
        filas = [
            ["2025-02-10", "compra", "Acción", "ECOPETROL", "1000", "2400", "12000", "", "", "", "", "", "", "", ""],
            ["2025-09-15", "dividendo", "Acción", "ECOPETROL", "", "", "", "180000", "", "", "", "", "", "", ""],
            ["2026-06-30", "precio", "Acción", "ECOPETROL", "", "2480", "", "", "", "", "", "", "", "", ""],
            ["2025-06-01", "compra", "CDT", "CDT Davivienda", "1", "5000000", "0", "", "11.5", "360", "2025-06-01", "", "", "", ""],
            ["2025-04-22", "compra", "TES", "TES 2030", "20", "98500", "30000", "", "7.75", "", "2030-09-18", "100000", "", "", ""],
            ["2026-04-22", "interes", "TES", "TES 2030", "", "", "", "155000", "", "", "", "", "", "", ""],
            # Acción en dólares: precio_usd × trm; dividendo = acciones × usd_por_accion × trm
            ["2023-01-30", "compra", "Acción", "NIKE (NKE)", "20", "", "0.21%", "", "", "", "", "", "127", "4548.5", ""],
            ["2023-04-02", "dividendo", "Acción", "NIKE (NKE)", "", "", "", "", "", "", "", "", "", "4646.08", "0.34"],
            ["2023-06-01", "dividendo", "Acción", "NIKE (NKE)", "", "", "", "", "", "", "", "", "", "4177.58", "0.34"],
            ["2023-06-22", "venta", "Acción", "NIKE (NKE)", "20", "", "0", "", "", "", "", "", "110", "3971.38", ""],
        ]
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(COLUMNAS)
            w.writerows(filas)

    @staticmethod
    def desde_csv(portafolio, ruta):
        """Carga el CSV. Si hay errores no modifica el portafolio. Devuelve nº de filas."""
        with open(ruta, newline="", encoding="utf-8-sig") as f:
            muestra = f.read(2048)
            f.seek(0)
            sep = ";" if muestra.count(";") > muestra.count(",") else ","
            filas = list(csv.DictReader(f, delimiter=sep))
        if not filas or "movimiento" not in filas[0]:
            raise ValueError("El archivo no tiene el formato esperado (usa la plantilla).")

        errores, listas = [], []
        for n, fila in enumerate(filas, start=2):          # la fila 1 es el encabezado
            try:
                listas.append((Importador._fecha(fila.get("fecha")), n, fila))
            except ValueError as e:
                errores.append(f"Fila {n}: {e}")
        listas.sort(key=lambda x: (x[0], x[1]))            # las compras antes que las ventas

        copia = copy.deepcopy(portafolio)
        for fecha, n, fila in listas:
            try:
                Importador._aplicar(copia, fecha, fila)
            except (ValueError, KeyError) as e:
                errores.append(f"Fila {n}: {e}")
        if errores:
            raise ValueError("No se importó nada. Corrige:\n" + "\n".join(errores[:8]))
        portafolio.activos = copia.activos
        return len(listas)

    @staticmethod
    def _aplicar(p, fecha, fila):
        num = Importador._num
        mov = (fila.get("movimiento") or "").strip().lower()
        nombre = (fila.get("activo") or "").strip()
        if mov not in MOVIMIENTOS:
            raise ValueError(f"movimiento «{mov}» no válido ({', '.join(MOVIMIENTOS)})")
        if not nombre:
            raise ValueError("falta el nombre del activo")
        if nombre not in p.activos:
            tipo = TIPOS.get((fila.get("tipo_activo") or "").strip().lower())
            if not tipo:
                raise ValueError(f"«{nombre}» es nuevo: indica tipo_activo (Acción, CDT, Bono o TES)")
            params = {}
            if tipo == "CDT":
                params = {"tasa_ea": num(fila.get("tasa")) / 100,
                          "plazo_dias": int(num(fila.get("plazo_dias"))),
                          "fecha_inicio": Importador._fecha(fila.get("fecha_ref"))}
            elif tipo in ("Bono", "TES"):
                params = {"valor_nominal": num(fila.get("valor_nominal")),
                          "tasa_cupon": num(fila.get("tasa")) / 100,
                          "vencimiento": Importador._fecha(fila.get("fecha_ref"))}
            p.agregar_activo(Almacenamiento.crear_activo(tipo, nombre, params))
        usd, trm = num(fila.get("precio_usd"), 0.0), num(fila.get("trm"), 0.0)
        if usd and not trm:
            raise ValueError("falta la TRM para convertir de dólares a pesos")
        if mov in ("compra", "venta"):
            cantidad = num(fila.get("cantidad"))
            precio = usd * trm if usd else num(fila.get("precio"))
            comision = Calculadora.comision(fila.get("comision"), cantidad * precio)
            p.registrar_operacion(nombre, Operacion(fecha, mov, cantidad, precio,
                                                    comision, usd, trm))
        elif mov == "precio":
            precio = usd * trm if usd else num(fila.get("precio"))
            p.activos[nombre].actualizar_precio(precio, fecha)
        elif mov == "dividendo" and (fila.get("usd_por_accion") or "").strip():
            p.registrar_dividendo_usd(nombre, fecha, num(fila.get("usd_por_accion")), trm)
        else:
            p.registrar_pago(nombre, Pago(fecha, mov, num(fila.get("monto"))))
