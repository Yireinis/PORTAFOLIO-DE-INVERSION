# PORTAFOLIO-DE-INVERSION
# Seguimiento de portafolio de inversión

Aplicación de escritorio en **Python (Tkinter)** para monitorear y evaluar un portafolio de
**renta variable** (acciones) y **renta fija** (CDT, bonos y TES): registra compras y ventas con
comisiones, dividendos, intereses y pagos de capital, valora los activos y calcula la
**rentabilidad acumulada** y la **rentabilidad efectiva anual (E. A.)**.
<img width="1323" height="1512" alt="WhatsApp Image 2026-11-13 at 6 39 39 AM" src="https://github.com/user-attachments/assets/1fe66516-1e83-45da-8f59-5ad9fb310b6d" />
## Ejecutar

Requiere Python 3.9+ (Tkinter viene incluido; en Linux: sudo apt install python3-tk).
No usa librerías externas.

bash
python main.py


Pulsa *"Cargar datos de ejemplo"* en el menú lateral para ver la app con un portafolio de demostración.
Los datos se guardan automáticamente en datos/portafolio.json.

## Pantallas

| Pantalla | Qué hace |
|---|---|
| Resumen | Total invertido, valor actual, rentabilidad acumulada y E. A., distribución renta fija / variable, posiciones |
| Operaciones | Registra compras y ventas (fecha, cantidad, precio, comisión) |
| Pagos | Registra dividendos, intereses y pagos de capital |
| Activos | Crea acciones, CDT, bonos y TES; actualiza precios de mercado |

## Importar un portafolio existente (Trii u otro bróker)

Menú lateral → *Guardar plantilla CSV*, llénala con tus movimientos (copiándolos desde el extracto
de tu bróker) y usa *Importar desde CSV*. Movimientos admitidos: compra, venta, dividendo,
interes, capital y precio (precio de mercado a una fecha). Fechas AAAA-MM-DD o DD/MM/AAAA;
separador ; o ,. Si hay errores no se importa nada y se indica la fila.

## Acciones en dólares (TRM) y estado de cuenta

- *Operaciones:* elige Moneda = USD, escribe el precio en dólares y la *TRM* del día; el precio en
  pesos es USD × TRM. La comisión se escribe en pesos (24262) o como porcentaje de la operación (0,21%).
- *Pagos:* para un dividendo en dólares escribe dividendo por acción (US$) y la TRM del día. El
  monto es acciones que tenías ese día × US$ por acción × TRM.
- *Estado de cuenta:* muestra los movimientos de un activo con el saldo acumulado (compras y
  comisiones restan; ventas y dividendos suman), el total y la variación, como en la hoja de cálculo.
- Ejemplo de la hoja del profesor (Nike): saldo final −$ 2.780.415; ver tests/test_portafolio.py.

## Estructura (una clase por archivo)


main.py                 Archivo principal (carga datos y abre la interfaz)
src/
  activo.py             Activo (clase base)
  accion.py  cdt.py  bono.py  tes.py    Tipos de activo (herencia)
  operacion.py          Operacion (compra/venta)
  pago.py               Pago (dividendo/interés/capital)
  portafolio.py         Portafolio (consolidado)
  calculadora.py        Calculadora (rentabilidad acumulada y TIR/E. A.)
  almacenamiento.py     Almacenamiento (JSON)
  datos_ejemplo.py      DatosEjemplo
  importador.py         Importador (CSV)
  interfaz.py           Interfaz (Tkinter)
tests/                  Pruebas unitarias (python -m unittest discover -s tests -t .)
docs/generar_uml.py     Regenera docs/uml.png
wiki/                   Páginas de la wiki del repositorio


## Cómo se calcula la rentabilidad

- *Total invertido* = Σ (cantidad × precio + comisión) de las compras.
- *Valor actual* = acciones: cantidad × precio de mercado · bonos/TES: cantidad × precio de mercado
  − capital amortizado · CDT: capital × (1 + tasa E. A.)^(días/365) − pagos recibidos.
- *Ingresos* = ventas netas de comisión + dividendos + intereses + pagos de capital.
- *Rentabilidad acumulada* = (valor actual + ingresos − total invertido) / total invertido.
- *Rentabilidad E. A.* = TIR no periódica (XIRR) de todos los flujos de dinero fechados, tomando el
  valor actual como un último ingreso hoy. Resuelve Σ flujo / (1 + r)^(días/365) = 0.

Las comisiones entran en los flujos (aumentan lo invertido en compras y reducen lo recibido en ventas),
por lo que afectan ambas rentabilidades. Ver la wiki para ejemplos.
