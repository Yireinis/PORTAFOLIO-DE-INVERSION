"""Archivo principal: carga los datos y arranca la interfaz."""
from src.almacenamiento import Almacenamiento
from src.interfaz import Interfaz

RUTA_DATOS = "datos/portafolio.json"


def main():
    portafolio = Almacenamiento.cargar(RUTA_DATOS)
    Interfaz(portafolio, RUTA_DATOS).mainloop()


if __name__ == "__main__":
    main()
