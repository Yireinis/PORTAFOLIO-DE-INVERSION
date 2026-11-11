import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

from src.almacenamiento import Almacenamiento
from src.datos_ejemplo import DatosEjemplo
from src.importador import Importador
from src.operacion import Operacion
from src.pago import Pago

C = dict(fondo="#F3F5F9", lateral="#14213D", lateral_sel="#22345F", acento="#2A9D8F",
         variable="#E76F51", texto="#1F2937", gris="#6B7280", blanco="#FFFFFF",
         verde="#15803D", rojo="#B91C1C")
FUENTE = "Segoe UI"


def cop(v):
    return "$ " + f"{v:,.0f}".replace(",", ".")


def pct(v):
    return "N/D" if v is None else f"{v * 100:.2f} %".replace(".", ",")


def variacion(v):
    """▲ si sube, ▼ si baja."""
    return "N/D" if v is None else ("▲ " if v >= 0 else "▼ ") + pct(v)


class Interfaz(tk.Tk):
    """Ventana principal: Resumen, Operaciones, Pagos y Activos."""

    def __init__(self, portafolio, ruta):
        super().__init__()
        self.p, self.ruta = portafolio, ruta
        self.title("Seguimiento de portafolio de inversión")
        self.geometry("1200x740")
        self.minsize(1050, 650)
        self.configure(bg=C["fondo"])
        self._estilos()
        self._lateral()
        self.cont = tk.Frame(self, bg=C["fondo"])
        self.cont.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        self.paginas = {
            "Resumen": self._pag_resumen(), "Operaciones": self._pag_operaciones(),
            "Pagos": self._pag_pagos(), "Activos": self._pag_activos()}
        self.mostrar("Resumen")
        self.refrescar()

    # ---------------- estructura general ----------------
    def _estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=C["blanco"], fieldbackground=C["blanco"],
                    foreground=C["texto"], rowheight=28, borderwidth=0, font=(FUENTE, 10))
        s.configure("Treeview.Heading", background="#E5E9F2", foreground=C["texto"],
                    font=(FUENTE, 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", "#CFE8E5")],
              foreground=[("selected", C["texto"])])
        s.configure("TCombobox", padding=4)

    def _lateral(self):
        lat = tk.Frame(self, bg=C["lateral"], width=210)
        lat.pack(side="left", fill="y")
        lat.pack_propagate(False)
        tk.Label(lat, text="◆ Mi Portafolio", bg=C["lateral"], fg="white",
                 font=(FUENTE, 15, "bold")).pack(anchor="w", padx=20, pady=(28, 4))
        tk.Label(lat, text="Renta fija y variable", bg=C["lateral"], fg="#9FB0D0",
                 font=(FUENTE, 9)).pack(anchor="w", padx=20, pady=(0, 24))
        self.botones = {}
        for n in ("Resumen", "Operaciones", "Pagos", "Activos"):
            b = tk.Button(lat, text="   " + n, anchor="w", bd=0, relief="flat",
                          bg=C["lateral"], fg="white", activebackground=C["lateral_sel"],
                          activeforeground="white", font=(FUENTE, 11), cursor="hand2",
                          command=lambda n=n: self.mostrar(n))
            b.pack(fill="x", ipady=8)
            self.botones[n] = b
        for clave, texto, cmd, bg in (
                ("borrar", "Borrar todos los datos", self._borrar_todo, "#8B2E2E"),
                ("ejemplo", "Cargar datos de ejemplo", self._ejemplo, "#3B4C77"),
                ("plantilla", "Guardar plantilla CSV", self._plantilla, "#3B4C77"),
                ("importar", "Importar desde CSV", self._importar, C["acento"])):
            b = tk.Button(lat, text=texto, bd=0, bg=bg, fg="white", font=(FUENTE, 10, "bold"),
                          cursor="hand2", activebackground="#238579", activeforeground="white",
                          command=cmd)
            b.pack(side="bottom", fill="x", padx=18, pady=(0, 8), ipady=7)
            self.acciones = getattr(self, "acciones", {})
            self.acciones[clave] = b

    def mostrar(self, nombre):
        for n, f in self.paginas.items():
            f.pack_forget()
            self.botones[n].configure(bg=C["lateral"])
        self.paginas[nombre].pack(fill="both", expand=True)
        self.botones[nombre].configure(bg=C["lateral_sel"])

    # ---------------- utilidades de widgets ----------------
    def _titulo(self, parent, texto, sub=""):
        tk.Label(parent, text=texto, bg=C["fondo"], fg=C["texto"],
                 font=(FUENTE, 20, "bold")).pack(anchor="w")
        tk.Label(parent, text=sub, bg=C["fondo"], fg=C["gris"],
                 font=(FUENTE, 10)).pack(anchor="w", pady=(0, 14))

    def _tarjeta(self, parent, **kw):
        return tk.Frame(parent, bg=C["blanco"], padx=16, pady=14, **kw)

    def _tabla(self, parent, columnas, anchos):
        marco = tk.Frame(parent, bg=C["blanco"])
        t = ttk.Treeview(marco, columns=columnas, show="headings", height=8)
        for c, a in zip(columnas, anchos):
            t.heading(c, text=c)
            t.column(c, width=a, anchor="w" if c in ("Activo", "Tipo", "Fecha", "Categoría") else "e")
        sb = ttk.Scrollbar(marco, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=sb.set)
        t.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return marco, t

    def _formulario(self, parent, campos):
        """campos: lista de (etiqueta, widget). Devuelve el frame."""
        f = self._tarjeta(parent)
        for i, (et, w) in enumerate(campos):
            tk.Label(f, text=et, bg=C["blanco"], fg=C["gris"], font=(FUENTE, 9)
                     ).grid(row=0, column=i, sticky="w", padx=6)
            w.grid(in_=f, row=1, column=i, padx=6, pady=(2, 0), sticky="we")
            w.lift()
        return f

    def _entry(self, parent, valor="", ancho=14):
        e = tk.Entry(parent, width=ancho, font=(FUENTE, 10), relief="solid", bd=1)
        e.insert(0, valor)
        return e

    def _combo(self, parent, valores, ancho=16, estado="readonly"):
        return ttk.Combobox(parent, values=valores, width=ancho, state=estado,
                            font=(FUENTE, 10))

    def _boton(self, parent, texto, comando):
        return tk.Button(parent, text=texto, command=comando, bg=C["acento"], fg="white",
                         bd=0, font=(FUENTE, 10, "bold"), cursor="hand2",
                         activebackground="#238579", activeforeground="white", padx=14)

    @staticmethod
    def _num(txt):
        return float(txt.strip().replace(" ", "").replace(",", "."))

    @staticmethod
    def _fecha(txt):
        return date.fromisoformat(txt.strip())

    def _guardar(self, accion):
        """Ejecuta una acción, muestra errores y guarda/refresca la pantalla."""
        try:
            accion()
        except (ValueError, KeyError) as e:
            msg = str(e)
            if "convert" in msg or "isoformat" in msg or "Invalid" in msg or not msg:
                msg = "Revisa los campos: números sin separador de miles y fechas AAAA-MM-DD."
            messagebox.showerror("Dato no válido", msg)
            return
        Almacenamiento.guardar(self.p, self.ruta)
        self.refrescar()

    # ---------------- páginas ----------------
    def _pag_resumen(self):
        pag = tk.Frame(self.cont, bg=C["fondo"])
        self._titulo(pag, "Resumen del portafolio", "Valoración a la fecha de hoy")
        fila = tk.Frame(pag, bg=C["fondo"])
        fila.pack(fill="x")
        self.kpi = {}
        for i, (clave, et) in enumerate([("invertido", "Total invertido"),
                ("valor_actual", "Valor actual"), ("acumulada", "Rentabilidad acumulada"),
                ("ea", "Rentabilidad E. A.")]):
            t = self._tarjeta(fila)
            t.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            fila.columnconfigure(i, weight=1)
            tk.Label(t, text=et, bg=C["blanco"], fg=C["gris"], font=(FUENTE, 10)).pack(anchor="w")
            l = tk.Label(t, text="-", bg=C["blanco"], fg=C["texto"], font=(FUENTE, 18, "bold"))
            l.pack(anchor="w", pady=(4, 0))
            self.kpi[clave] = l
        self.detalle = tk.Label(pag, text="", bg=C["fondo"], fg=C["gris"], font=(FUENTE, 10))
        self.detalle.pack(anchor="w", pady=(10, 8))
        medio = tk.Frame(pag, bg=C["fondo"])
        medio.pack(fill="x")
        graf = self._tarjeta(medio)
        graf.pack(side="left", fill="both", expand=True)
        tk.Label(graf, text="Evolución del portafolio", bg=C["blanco"], fg=C["texto"],
                 font=(FUENTE, 12, "bold")).pack(anchor="w")
        self.linea = tk.Canvas(graf, height=210, bg=C["blanco"], highlightthickness=0)
        self.linea.pack(fill="both", expand=True, pady=(6, 0))
        self.linea.bind("<Configure>", lambda e: self._dibujar_linea())
        izq = self._tarjeta(medio)
        izq.pack(side="left", fill="y", padx=(12, 0))
        tk.Label(izq, text="Distribución", bg=C["blanco"], fg=C["texto"],
                 font=(FUENTE, 12, "bold")).pack(anchor="w")
        self.dona = tk.Canvas(izq, width=190, height=190, bg=C["blanco"], highlightthickness=0)
        self.dona.pack(pady=6)
        self.leyenda = tk.Frame(izq, bg=C["blanco"])
        self.leyenda.pack(fill="x")
        abajo = self._tarjeta(pag)
        abajo.pack(fill="both", expand=True, pady=(12, 0))
        tk.Label(abajo, text="Posiciones", bg=C["blanco"], fg=C["texto"],
                 font=(FUENTE, 12, "bold")).pack(anchor="w", pady=(0, 6))
        marco, self.t_pos = self._tabla(abajo, ("Activo", "Categoría", "Invertido",
                                                "Valor actual", "Ganancia", "Variación"),
                                        (150, 110, 120, 120, 120, 110))
        self.t_pos.configure(height=5)
        marco.pack(fill="both", expand=True)
        self.t_pos.tag_configure("g", foreground=C["verde"])
        self.t_pos.tag_configure("p", foreground=C["rojo"])
        return pag

    def _pag_operaciones(self):
        pag = tk.Frame(self.cont, bg=C["fondo"])
        self._titulo(pag, "Operaciones", "Compras y ventas, con la comisión del bróker")
        self.o_fecha = self._entry(pag, date.today().isoformat(), 12)
        self.o_tipo = self._combo(pag, ["compra", "venta"], 9)
        self.o_tipo.current(0)
        self.o_activo = self._combo(pag, [], 18, estado="normal")   # se puede escribir uno nuevo
        self.o_nuevo = self._combo(pag, ["Acción", "CDT", "Bono", "TES"], 9)
        self.o_nuevo.current(0)
        self.o_cant = self._entry(pag, "", 10)
        self.o_precio = self._entry(pag, "", 12)
        self.o_com = self._entry(pag, "0", 10)
        f = self._formulario(pag, [("Fecha (AAAA-MM-DD)", self.o_fecha), ("Tipo", self.o_tipo),
            ("Activo (elige o escribe uno nuevo)", self.o_activo), ("Si es nuevo", self.o_nuevo),
            ("Cantidad", self.o_cant),
            ("Precio por unidad", self.o_precio), ("Comisión", self.o_com),
            ("", self._boton(pag, "Registrar", self._registrar_operacion))])
        f.pack(fill="x", pady=(0, 12))
        marco, self.t_ops = self._tabla(pag, ("Fecha", "Activo", "Tipo", "Cantidad", "Precio",
                                              "Comisión", "Flujo de caja"),
                                        (100, 150, 80, 90, 110, 100, 130))
        marco.pack(fill="both", expand=True)
        return pag

    def _pag_pagos(self):
        pag = tk.Frame(self.cont, bg=C["fondo"])
        self._titulo(pag, "Pagos recibidos", "Dividendos, intereses (cupones) y pagos de capital")
        self.p_fecha = self._entry(pag, date.today().isoformat(), 12)
        self.p_activo = self._combo(pag, [], 18)
        self.p_tipo = self._combo(pag, ["dividendo", "interes", "capital"], 12)
        self.p_tipo.current(0)
        self.p_monto = self._entry(pag, "", 14)
        f = self._formulario(pag, [("Fecha (AAAA-MM-DD)", self.p_fecha), ("Activo", self.p_activo),
            ("Tipo", self.p_tipo), ("Monto recibido", self.p_monto),
            ("", self._boton(pag, "Registrar", self._registrar_pago))])
        f.pack(fill="x", pady=(0, 12))
        marco, self.t_pagos = self._tabla(pag, ("Fecha", "Activo", "Tipo", "Monto"),
                                          (110, 200, 120, 140))
        marco.pack(fill="both", expand=True)
        return pag

    def _pag_activos(self):
        pag = tk.Frame(self.cont, bg=C["fondo"])
        self._titulo(pag, "Activos y valoración",
                     "Crea instrumentos y actualiza su precio de mercado")
        self.a_tipo = self._combo(pag, ["Acción", "CDT", "Bono", "TES"], 10)
        self.a_tipo.current(0)
        self.a_nombre = self._entry(pag, "", 16)
        self.a_tasa = self._entry(pag, "", 9)
        self.a_plazo = self._entry(pag, "", 9)
        self.a_fecha = self._entry(pag, "", 12)
        self.a_nominal = self._entry(pag, "", 11)
        f = self._formulario(pag, [("Tipo", self.a_tipo), ("Nombre", self.a_nombre),
            ("Tasa % (E. A. o cupón)", self.a_tasa), ("Plazo CDT (días)", self.a_plazo),
            ("Inicio CDT / vencim. bono", self.a_fecha), ("Valor nominal", self.a_nominal),
            ("", self._boton(pag, "Crear activo", self._crear_activo))])
        f.pack(fill="x", pady=(0, 8))
        self.v_activo = self._combo(pag, [], 18)
        self.v_precio = self._entry(pag, "", 14)
        g = self._formulario(pag, [("Activo", self.v_activo), ("Nuevo precio de mercado (por unidad)",
            self.v_precio), ("", self._boton(pag, "Actualizar precio", self._actualizar_precio)),
            ("", self._boton(pag, "Eliminar activo", self._eliminar_activo))])
        g.pack(fill="x", pady=(0, 12))
        marco, self.t_act = self._tabla(pag, ("Activo", "Tipo", "Categoría", "Cantidad",
                                              "Precio mercado", "Valor actual"),
                                        (150, 80, 120, 90, 120, 130))
        marco.pack(fill="both", expand=True)
        return pag

    # ---------------- acciones ----------------
    def _registrar_operacion(self):
        def hacer():
            op = Operacion(self._fecha(self.o_fecha.get()), self.o_tipo.get(),
                           self._num(self.o_cant.get()), self._num(self.o_precio.get()),
                           self._num(self.o_com.get() or "0"))
            nombre = self.o_activo.get().strip()
            if not nombre:
                raise ValueError("Escribe o elige el activo.")
            creado = nombre not in self.p.activos
            if creado:
                tipo = self.o_nuevo.get()
                if tipo != "Acción":
                    raise ValueError(f"Para un {tipo} nuevo, créalo primero en la pestaña "
                                     "Activos (necesita tasa, plazo y fechas).")
                self.p.agregar_activo(Almacenamiento.crear_activo("Acción", nombre))
            try:
                self.p.registrar_operacion(nombre, op)
            except ValueError:
                if creado:                      # no dejar un activo vacío si la operación falla
                    self.p.eliminar_activo(nombre)
                raise
            self.o_cant.delete(0, "end")
            self.o_precio.delete(0, "end")
        self._guardar(hacer)

    def _registrar_pago(self):
        def hacer():
            self.p.registrar_pago(self.p_activo.get(), Pago(
                self._fecha(self.p_fecha.get()), self.p_tipo.get(),
                self._num(self.p_monto.get())))
            self.p_monto.delete(0, "end")
        self._guardar(hacer)

    def _crear_activo(self):
        def hacer():
            tipo, nombre = self.a_tipo.get(), self.a_nombre.get().strip()
            if not nombre:
                raise ValueError("Escribe un nombre para el activo.")
            params = {}
            if tipo == "CDT":
                params = {"tasa_ea": self._num(self.a_tasa.get()) / 100,
                          "plazo_dias": int(self._num(self.a_plazo.get())),
                          "fecha_inicio": self._fecha(self.a_fecha.get())}
            elif tipo in ("Bono", "TES"):
                params = {"valor_nominal": self._num(self.a_nominal.get()),
                          "tasa_cupon": self._num(self.a_tasa.get()) / 100,
                          "vencimiento": self._fecha(self.a_fecha.get())}
            self.p.agregar_activo(Almacenamiento.crear_activo(tipo, nombre, params))
            self.a_nombre.delete(0, "end")
        self._guardar(hacer)

    def _actualizar_precio(self):
        def hacer():
            nombre = self.v_activo.get()
            if nombre in self.p.activos and self.p.activos[nombre].tipo == "CDT":
                raise ValueError("El CDT se valora por los intereses causados, no por precio.")
            self.p.actualizar_precio(nombre, self._num(self.v_precio.get()))
            self.v_precio.delete(0, "end")
        self._guardar(hacer)

    def _importar(self):
        ruta = filedialog.askopenfilename(title="Importar movimientos",
                                          filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            n = Importador.desde_csv(self.p, ruta)
        except (ValueError, OSError, UnicodeDecodeError) as e:
            messagebox.showerror("No se pudo importar", str(e))
            return
        Almacenamiento.guardar(self.p, self.ruta)
        self.refrescar()
        messagebox.showinfo("Importación lista", f"Se importaron {n} filas.")

    def _plantilla(self):
        ruta = filedialog.asksaveasfilename(title="Guardar plantilla", defaultextension=".csv",
                                            initialfile="plantilla_portafolio.csv")
        if ruta:
            Importador.plantilla(ruta)
            messagebox.showinfo("Plantilla guardada", "Llénala con tus movimientos y usa «Importar desde CSV».")

    def _ejemplo(self):
        """Carga o quita los datos de demostración (nunca se guardan en disco)."""
        if self.p.hay_ejemplo():
            self.p.quitar_ejemplo()
        else:
            DatosEjemplo.cargar(self.p)
        self.refrescar()

    def _borrar_todo(self):
        if not self.p.activos:
            return
        if messagebox.askyesno("Borrar todos los datos",
                               "Se eliminarán todos los activos, operaciones y pagos.\n"
                               "Esta acción no se puede deshacer. ¿Continuar?", icon="warning"):
            self.p.borrar_todo()
            Almacenamiento.guardar(self.p, self.ruta)
            self.refrescar()

    def _eliminar_activo(self):
        nombre = self.v_activo.get()
        if nombre not in self.p.activos:
            messagebox.showerror("Dato no válido", "Selecciona un activo en la lista.")
            return
        if messagebox.askyesno("Eliminar activo", f"¿Eliminar «{nombre}» con todas sus "
                               "operaciones y pagos?", icon="warning"):
            self.p.eliminar_activo(nombre)
            self.v_activo.set("")
            Almacenamiento.guardar(self.p, self.ruta)
            self.refrescar()

    # ---------------- refresco ----------------
    def refrescar(self):
        hoy = date.today()
        self.acciones["ejemplo"].config(text="Quitar datos de ejemplo" if self.p.hay_ejemplo()
                                        else "Cargar datos de ejemplo")
        nombres = list(self.p.activos)
        for c in (self.o_activo, self.p_activo, self.v_activo):
            c.configure(values=nombres)
        r = self.p.resumen(hoy)
        self.kpi["invertido"].config(text=cop(r["invertido"]))
        self.kpi["valor_actual"].config(text=cop(r["valor_actual"]))
        for k in ("acumulada", "ea"):
            v = r[k]
            self.kpi[k].config(text=variacion(v), fg=C["texto"] if v is None else
                               (C["verde"] if v >= 0 else C["rojo"]))
        self.detalle.config(text=f"Ingresos recibidos: {cop(r['ingresos'])}    ·    "
                                 f"Comisiones pagadas: {cop(r['comisiones'])}    ·    "
                                 f"Ganancia total: {cop(r['ganancia'])}")
        self._dibujar_dona(r["distribucion"])
        self.serie = self.p.serie(hoy)
        self._dibujar_linea()
        filas = []
        for a in self.p.activos.values():
            g, inv = a.ganancia(hoy), a.total_invertido()
            var = g / inv if inv else None
            filas.append((a.nombre, a.categoria, cop(inv), cop(a.valor_actual(hoy)), cop(g),
                          variacion(var), "g" if g >= 0 else "p"))
        self._llenar(self.t_pos, filas)
        ops = sorted(((o, a.nombre) for a in self.p.activos.values() for o in a.operaciones),
                     key=lambda x: x[0].fecha, reverse=True)
        self._llenar(self.t_ops, [(o.fecha.isoformat(), n, o.tipo, f"{o.cantidad:g}",
                     cop(o.precio), cop(o.comision), cop(o.flujo_caja())) for o, n in ops])
        pagos = sorted(((x, a.nombre) for a in self.p.activos.values() for x in a.pagos),
                       key=lambda x: x[0].fecha, reverse=True)
        self._llenar(self.t_pagos, [(x.fecha.isoformat(), n, x.tipo, cop(x.monto))
                                    for x, n in pagos])
        self._llenar(self.t_act, [(a.nombre, a.tipo, a.categoria, f"{a.cantidad():g}",
                     "—" if a.tipo == "CDT" else cop(a.precio_mercado), cop(a.valor_actual(hoy)))
                     for a in self.p.activos.values()])

    @staticmethod
    def _llenar(tabla, filas):
        tabla.delete(*tabla.get_children())
        for f in filas:
            if len(f) == len(tabla["columns"]) + 1:     # el último elemento es la etiqueta de color
                tabla.insert("", "end", values=f[:-1], tags=(f[-1],))
            else:
                tabla.insert("", "end", values=f)

    def _dibujar_dona(self, dist):
        cv, total = self.dona, sum(dist.values())
        cv.delete("all")
        for w in self.leyenda.winfo_children():
            w.destroy()
        colores = {"Renta fija": C["acento"], "Renta variable": C["variable"]}
        caja = (8, 8, 182, 182)
        if total <= 0:
            cv.create_oval(*caja, fill="#E5E9F2", outline="")
        else:
            inicio = 90
            for nombre, valor in dist.items():
                if valor > 0:
                    ext = -359.99 if valor == total else -360 * valor / total
                    cv.create_arc(*caja, start=inicio, extent=ext, fill=colores[nombre],
                                  outline="white", width=2)
                    inicio += ext
        cv.create_oval(48, 48, 142, 142, fill="white", outline="")
        cv.create_text(95, 86, text="Total", fill=C["gris"], font=(FUENTE, 9))
        cv.create_text(95, 104, text=cop(total), fill=C["texto"], font=(FUENTE, 9, "bold"))
        for nombre, valor in dist.items():
            fila = tk.Frame(self.leyenda, bg=C["blanco"])
            fila.pack(fill="x", pady=1)
            tk.Frame(fila, bg=colores[nombre], width=12, height=12).pack(side="left", padx=(0, 8))
            p = valor / total if total else 0
            tk.Label(fila, text=nombre, bg=C["blanco"], fg=C["texto"],
                     font=(FUENTE, 10)).pack(side="left")
            tk.Label(fila, text=f"{p * 100:.1f} %".replace(".", ","), bg=C["blanco"],
                     fg=C["texto"], font=(FUENTE, 10, "bold")).pack(side="right", padx=(14, 0))

    def _dibujar_linea(self):
        """Gráfica de línea: valor del portafolio vs. capital neto invertido."""
        cv = self.linea
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        serie = getattr(self, "serie", [])
        if w < 120 or h < 80:
            return
        if len(serie) < 2:
            cv.create_text(w / 2, h / 2, fill=C["gris"], font=(FUENTE, 10),
                           text="Registra operaciones para ver la evolución")
            return
        ml, mr, mt, mb = 74, 16, 10, 26
        fechas = [x[0] for x in serie]
        valores = [x[1] for x in serie]
        invertido = [x[2] for x in serie]
        vmin, vmax = min(valores + invertido), max(valores + invertido)
        pad = (vmax - vmin) * 0.12 or vmax * 0.1 or 1
        lo, hi = max(0, vmin - pad), vmax + pad
        d0, dias = fechas[0], max(1, (fechas[-1] - fechas[0]).days)
        X = lambda f: ml + (f - d0).days / dias * (w - ml - mr)
        Y = lambda v: mt + (hi - v) / (hi - lo) * (h - mt - mb)
        sube = valores[-1] >= invertido[-1]
        color = C["verde"] if sube else C["rojo"]
        relleno = "#DDF3E4" if sube else "#FBE1E1"
        for i in range(5):                                   # cuadrícula y eje Y
            v = lo + (hi - lo) * i / 4
            cv.create_line(ml, Y(v), w - mr, Y(v), fill="#E5E9F2")
            cv.create_text(ml - 8, Y(v), text=f"{v / 1e6:.1f} M".replace(".", ","),
                           anchor="e", fill=C["gris"], font=(FUENTE, 8))
        for i in range(4):                                   # eje X
            f = fechas[0] + (fechas[-1] - fechas[0]) * i // 3
            cv.create_text(X(f), h - 10, text=f.isoformat()[:7], fill=C["gris"],
                           font=(FUENTE, 8))
        pts = [c for f, v in zip(fechas, valores) for c in (X(f), Y(v))]
        cv.create_polygon(*pts, X(fechas[-1]), h - mb, X(fechas[0]), h - mb,
                          fill=relleno, outline="")
        pi = [c for f, v in zip(fechas, invertido) for c in (X(f), Y(v))]
        cv.create_line(*pi, fill="#9CA3AF", width=2, dash=(5, 3))
        cv.create_line(*pts, fill=color, width=3, smooth=True)
        cv.create_oval(X(fechas[-1]) - 5, Y(valores[-1]) - 5, X(fechas[-1]) + 5,
                       Y(valores[-1]) + 5, fill=color, outline="white", width=2)
        cv.create_line(ml + 6, mt + 8, ml + 30, mt + 8, fill=color, width=3)
        cv.create_text(ml + 36, mt + 8, text="Valor del portafolio", anchor="w",
                       fill=C["texto"], font=(FUENTE, 8))
        cv.create_line(ml + 160, mt + 8, ml + 184, mt + 8, fill="#9CA3AF", width=2, dash=(5, 3))
        cv.create_text(ml + 190, mt + 8, text="Capital neto invertido", anchor="w",
                       fill=C["texto"], font=(FUENTE, 8))
