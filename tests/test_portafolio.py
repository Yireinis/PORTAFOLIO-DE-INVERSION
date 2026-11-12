import unittest
from datetime import date, timedelta
from src.accion import Accion
from src.cdt import CDT
from src.operacion import Operacion
from src.pago import Pago
from src.portafolio import Portafolio
from src.datos_ejemplo import DatosEjemplo
from src.importador import Importador


class TestRentabilidad(unittest.TestCase):
    def test_ejemplo_del_enunciado(self):
        """Compra de 1.000.000 que vale 1.060.000 a los 180 días: 6 % y ≈12,5 % E. A."""
        p, a = Portafolio(), Accion("X", 1060)
        p.agregar_activo(a)
        ini = date(2026, 1, 1)
        p.registrar_operacion("X", Operacion(ini, "compra", 1000, 1000, 0))
        hoy = ini + timedelta(days=180)
        self.assertAlmostEqual(p.rentabilidad_acumulada(hoy), 0.06)
        self.assertAlmostEqual(p.rentabilidad_ea(hoy), 1.06 ** (365 / 180) - 1, places=5)

    def test_cdt_a_un_ano_rinde_su_tasa(self):
        p = Portafolio()
        p.agregar_activo(CDT("C", 0.10, 365, date(2025, 1, 1)))
        p.registrar_operacion("C", Operacion(date(2025, 1, 1), "compra", 1, 1_000_000, 0))
        self.assertAlmostEqual(p.rentabilidad_ea(date(2026, 1, 1)), 0.10, places=4)

    def test_comisiones_reducen_rentabilidad(self):
        p, a = Portafolio(), Accion("X", 1000)
        p.agregar_activo(a)
        p.registrar_operacion("X", Operacion(date(2026, 1, 1), "compra", 100, 1000, 5000))
        self.assertLess(p.rentabilidad_acumulada(date(2026, 6, 1)), 0)

    def test_no_se_puede_vender_de_mas(self):
        p = Portafolio(); p.agregar_activo(Accion("X"))
        p.registrar_operacion("X", Operacion(date(2026, 1, 1), "compra", 5, 10))
        with self.assertRaises(ValueError):
            p.registrar_operacion("X", Operacion(date(2026, 2, 1), "venta", 6, 10))

    def test_dividendos_suman_ingresos(self):
        p = Portafolio(); p.agregar_activo(Accion("X", 100))
        p.registrar_operacion("X", Operacion(date(2026, 1, 1), "compra", 10, 100))
        p.registrar_pago("X", Pago(date(2026, 3, 1), "dividendo", 50))
        self.assertAlmostEqual(p.rentabilidad_acumulada(date(2026, 6, 1)), 0.05)

    def test_datos_ejemplo(self):
        p = Portafolio(); DatosEjemplo.cargar(p)
        r = p.resumen(date(2026, 11, 4))
        self.assertGreater(r["valor_actual"], 0)
        self.assertAlmostEqual(sum(r["distribucion"].values()), r["valor_actual"])

    def test_serie_y_precio_historico(self):
        p = Portafolio(); a = Accion("X"); p.agregar_activo(a)
        p.registrar_operacion("X", Operacion(date(2026, 1, 1), "compra", 10, 100))
        a.actualizar_precio(100, date(2026, 1, 1))
        a.actualizar_precio(150, date(2026, 3, 1))
        self.assertEqual(a.precio_en(date(2026, 2, 1)), 100)
        self.assertEqual(a.precio_en(date(2026, 4, 1)), 150)
        s = p.serie(date(2026, 5, 1))
        self.assertEqual(s[0][1], 1000)
        self.assertEqual(s[-1][1], 1500)
        self.assertTrue(all(x[2] == 1000 for x in s))

    def test_importar_csv(self):
        import os, tempfile
        ruta = os.path.join(tempfile.mkdtemp(), "p.csv")
        Importador.plantilla(ruta)
        p = Portafolio()
        self.assertEqual(Importador.desde_csv(p, ruta), 10)
        self.assertEqual(set(p.activos), {"ECOPETROL", "CDT Davivienda", "TES 2030", "NIKE (NKE)"})
        self.assertEqual(p.activos["ECOPETROL"].precio_mercado, 2480)
        self.assertGreater(p.valor_actual(date(2026, 11, 4)), 0)

    def test_importar_csv_con_errores_no_modifica(self):
        import os, tempfile
        ruta = os.path.join(tempfile.mkdtemp(), "m.csv")
        open(ruta, "w", encoding="utf-8").write(
            "fecha,movimiento,tipo_activo,activo,cantidad,precio,comision,monto\n"
            "2026-01-01,compra,Acción,X,10,100,0,\n2026-02-01,venta,Acción,X,99,100,0,\n")
        p = Portafolio()
        with self.assertRaises(ValueError):
            Importador.desde_csv(p, ruta)
        self.assertEqual(p.activos, {})

    def test_ejemplo_no_se_guarda_y_se_puede_quitar(self):
        import os, tempfile
        from src.almacenamiento import Almacenamiento
        ruta = os.path.join(tempfile.mkdtemp(), "d.json")
        p = Portafolio(); DatosEjemplo.cargar(p)
        p.agregar_activo(Accion("REAL", 10))
        Almacenamiento.guardar(p, ruta)
        self.assertEqual(list(Almacenamiento.cargar(ruta).activos), ["REAL"])
        self.assertTrue(p.hay_ejemplo())
        p.quitar_ejemplo()
        self.assertEqual(list(p.activos), ["REAL"])
        p.eliminar_activo("REAL"); self.assertEqual(p.activos, {})

    def test_compra_sin_precio_de_mercado_se_valora_al_costo(self):
        p = Portafolio(); p.agregar_activo(Accion("NUEVA"))
        p.registrar_operacion("NUEVA", Operacion(date(2026, 1, 1), "compra", 10, 100, 0))
        self.assertEqual(p.valor_actual(date(2026, 2, 1)), 1000)
        p.actualizar_precio("NUEVA", 120)
        self.assertEqual(p.activos["NUEVA"].precio_mercado, 120)

    def test_caso_nike_de_la_hoja_del_profesor(self):
        """Compra 20 NKE a US$127 (TRM 4.548,5), 2 dividendos de US$0,34 y venta a US$110."""
        from src.calculadora import Calculadora
        p = Portafolio(); p.agregar_activo(Accion("NKE"))
        compra = 20 * 127 * 4548.5
        p.registrar_operacion("NKE", Operacion(date(2023, 1, 30), "compra", 20, 127 * 4548.5,
                              Calculadora.comision("0,21%", compra), 127, 4548.5))
        p.registrar_dividendo_usd("NKE", date(2023, 4, 2), 0.34, 4646.08)
        p.registrar_dividendo_usd("NKE", date(2023, 6, 1), 0.34, 4177.58)
        p.registrar_operacion("NKE", Operacion(date(2023, 6, 22), "venta", 20, 110 * 3971.38, 0,
                              110, 3971.38))
        filas = p.libro("NKE")
        self.assertEqual([round(f["saldo"]) for f in filas],
                         [-11577452, -11545858, -11517451, -2780415])   # = hoja del profesor
        self.assertEqual([f["acciones"] for f in filas], [0, 20, 20, 20])
        self.assertEqual(round(filas[1]["div_cop"], 2), 1579.67)
        a = p.activos["NKE"]
        self.assertAlmostEqual(a.ganancia(date(2023, 7, 1)), filas[-1]["saldo"], places=4)
        self.assertAlmostEqual(filas[-1]["variacion"], -2780414.81 / 11577451.70, places=5)
        self.assertEqual(Calculadora.comision("24262", 1), 24262)

    def test_dividendo_sin_acciones_falla(self):
        p = Portafolio(); p.agregar_activo(Accion("X"))
        with self.assertRaises(ValueError):
            p.registrar_dividendo_usd("X", date(2026, 1, 1), 0.3, 4000)


if __name__ == "__main__":
    unittest.main()
