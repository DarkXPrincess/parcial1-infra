"""
Parcial I - Infraestructuras Paralelas y Distribuidas (750023C)
Juego de la Vida de Conway - PARTE PARALELA con HILOS (threading)

Reutiliza calcular_filas de juego_vida_secuencial.py (misma carpeta).

Estrategia de paralelización:
  * División del trabajo: bloques de filas contiguas, un bloque por hilo.
  * Los hilos se crean UNA sola vez y se reutilizan en todas las generaciones.
  * Memoria compartida: todos los hilos LEEN del tablero 'actual' y cada uno
    ESCRIBE solo en sus propias filas de 'nueva'. Como los rangos de escritura
    no se solapan y nadie escribe en lo que otros leen, no hay condiciones de
    carrera y no se necesitan mutexes.
  * Sincronización con dos barreras por generación:
      - 'inicio': ningún hilo calcula hasta que el hilo principal da la orden
        (y ya hizo el intercambio de tableros de la generación anterior).
      - 'fin': el hilo principal no intercambia 'actual' y 'nueva' hasta que
        TODOS los hilos terminaron de escribir.

Nota sobre el GIL: en CPython normal solo un hilo ejecuta bytecode a la vez,
así que este código es correcto pero casi no acelera. Con una versión de
Python sin GIL (build "free-threaded", p. ej. python3.13t o 3.14t) los hilos
sí corren en paralelo real y se ve el speedup.
"""

import threading

from juego_vida_secuencial import calcular_filas


def _rangos(n_filas, p):
    """Divide n_filas en hasta p bloques contiguos [inicio, fin)."""
    paso = (n_filas + p - 1) // p
    return [(a, min(a + paso, n_filas)) for a in range(0, n_filas, paso)]


class JuegoParalelo:
    """Mantiene p hilos vivos y avanza el tablero una generación por paso()."""

    def __init__(self, matriz, p):
        self.actual = [fila[:] for fila in matriz]          # copia
        self.nueva = [[0] * len(matriz[0]) for _ in matriz]
        self.rangos = _rangos(len(matriz), p)
        self.p = len(self.rangos)                            # hilos reales
        self.detenido = False
        # p hilos trabajadores + 1 hilo principal esperando en cada barrera
        self.inicio = threading.Barrier(self.p + 1)
        self.fin = threading.Barrier(self.p + 1)
        self.hilos = [threading.Thread(target=self._trabajador, args=(a, b),
                                       daemon=True)
                      for a, b in self.rangos]
        for h in self.hilos:
            h.start()

    def _trabajador(self, a, b):
        while True:
            self.inicio.wait()              # espera la orden de arrancar
            if self.detenido:
                return
            calcular_filas(self.actual, self.nueva, a, b)
            self.fin.wait()                 # avisa que terminó su bloque

    def paso(self):
        """Avanza una generación y devuelve el tablero resultante.
        OJO: el tablero devuelto se reutiliza en el paso siguiente; si lo
        necesitas guardar, cópialo."""
        self.inicio.wait()                  # suelta a los hilos
        self.fin.wait()                     # espera a que todos terminen
        self.actual, self.nueva = self.nueva, self.actual
        return self.actual

    def cerrar(self):
        """Detiene los hilos. Llamar al terminar."""
        self.detenido = True
        self.inicio.wait()
        for h in self.hilos:
            h.join()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()


def simular_paralela(matriz, generaciones, p):
    """Avanza 'generaciones' pasos con p hilos y devuelve el tablero final."""
    with JuegoParalelo(matriz, p) as juego:
        for _ in range(generaciones):
            juego.paso()
        return [fila[:] for fila in juego.actual]


# ----------------------------------------------------------------------------
# Verificación de correctitud: el resultado debe ser idéntico al secuencial
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    from juego_vida_secuencial import crear_matriz, simular

    base = crear_matriz(120, 150, semilla=42)
    esperado = simular(base, 15)
    for p in (1, 2, 4, 7):
        obtenido = simular_paralela(base, 15, p)
        print(f"hilos p={p}: {'OK' if obtenido == esperado else 'DIFERENTE'}")