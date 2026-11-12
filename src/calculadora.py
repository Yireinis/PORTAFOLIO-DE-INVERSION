class Calculadora:
    """Fórmulas de rentabilidad."""

    @staticmethod
    def rentabilidad_acumulada(invertido, valor_actual, ingresos):
        """(valor actual + ingresos − invertido) / invertido."""
        if invertido <= 0:
            return None
        return (valor_actual + ingresos - invertido) / invertido

    @staticmethod
    def comision(texto, valor_bruto):
        """«24262» = pesos; «0,21%» = porcentaje del valor bruto de la operación."""
        t = (texto or "").strip().replace(" ", "").replace(",", ".")
        if not t:
            return 0.0
        if t.endswith("%"):
            return valor_bruto * float(t[:-1]) / 100
        return float(t)

    @staticmethod
    def xirr(flujos):
        """Tasa efectiva anual de flujos fechados [(fecha, monto)] (TIR no periódica).

        Resuelve  Σ monto / (1+r)^(días/365) = 0  por bisección.
        """
        fl = [(d, m) for d, m in flujos if m != 0]
        if not any(m < 0 for _, m in fl) or not any(m > 0 for _, m in fl):
            return None
        t0 = min(d for d, _ in fl)

        def f(r):
            return sum(m / (1 + r) ** ((d - t0).days / 365) for d, m in fl)

        lo, hi = -0.9999, 1000.0
        if f(lo) * f(hi) > 0:
            return None
        for _ in range(300):
            mid = (lo + hi) / 2
            if f(lo) * f(mid) <= 0:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
