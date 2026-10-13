"""
Parcial I - Infraestructuras Paralelas y Distribuidas (750023C)
Juego de la Vida de Conway - VERSION SECUENCIAL (línea base)

Uso:
    python juego_vida_secuencial.py                 -> abre la interfaz gráfica
    python juego_vida_secuencial.py 
    python juego_vida_secuencial.py --filas 80 --columnas 120 --celda 8

Decisiones de diseño (pensadas para que la versión paralela reutilice todo):
  * La matriz es una lista de listas de enteros (1 = viva, 0 = muerta).
    No se usa NumPy a propósito: queremos una base secuencial "pura" para que
    la comparación con hilos/procesos sea justa.
  * El cálculo de una generación se separa en dos funciones:
      - contar_vecinos():  cuántos vecinos vivos tiene una celda.
      - calcular_filas():  calcula las filas [inicio, fin) de la siguiente
        generación. La versión secuencial la llama con todas las filas;
        la paralela solo tendrá que llamarla con rangos distintos por hilo.
  * Los bordes se tratan como celdas muertas (el mundo no da la vuelta).
"""

import argparse
import random
import time


# ----------------------------------------------------------------------------
# Lógica del juego
# ----------------------------------------------------------------------------

def crear_matriz(filas, columnas, densidad=0.25, semilla=None):
    """Crea una matriz aleatoria. 'densidad' es la probabilidad de que una
    celda empiece viva. Con una semilla fija el resultado es reproducible,
    lo que permite comparar secuencial y paralelo sobre el mismo tablero."""
    rng = random.Random(semilla)
    return [[1 if rng.random() < densidad else 0 for _ in range(columnas)]
            for _ in range(filas)]


def contar_vecinos(matriz, i, j, filas, columnas):
    """Cuenta los vecinos vivos de la celda (i, j) revisando las 8 celdas
    que la rodean. Lo que cae fuera de la matriz cuenta como muerto."""
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue  # la celda no es vecina de sí misma
            ni, nj = i + di, j + dj
            if 0 <= ni < filas and 0 <= nj < columnas:
                total += matriz[ni][nj]
    return total


def calcular_filas(actual, nueva, inicio, fin):
    """Calcula las filas [inicio, fin) de la siguiente generación.

    Lee de 'actual' y escribe SOLO en 'nueva'. Esa separación es lo que evita
    condiciones de carrera: nadie modifica el tablero que los demás están
    leyendo. Cada rango de filas es independiente, así que es la unidad de
    trabajo que se repartirá entre hilos más adelante.
    """
    filas = len(actual)
    columnas = len(actual[0])
    for i in range(inicio, fin):
        fila_actual = actual[i]
        fila_nueva = nueva[i]
        for j in range(columnas):
            vecinos = contar_vecinos(actual, i, j, filas, columnas)
            if fila_actual[j] == 1:
                # Viva: sobrevive con 2 o 3 vecinos, si no muere
                fila_nueva[j] = 1 if vecinos in (2, 3) else 0
            else:
                # Muerta: nace con exactamente 3 vecinos
                fila_nueva[j] = 1 if vecinos == 3 else 0


def siguiente_generacion(actual):
    """Versión secuencial: una sola llamada que cubre todas las filas."""
    filas = len(actual)
    columnas = len(actual[0])
    nueva = [[0] * columnas for _ in range(filas)]
    calcular_filas(actual, nueva, 0, filas)
    return nueva


def simular(matriz, generaciones):
    """Avanza 'generaciones' pasos y devuelve la matriz final."""
    for _ in range(generaciones):
        matriz = siguiente_generacion(matriz)
    return matriz


def contar_vivas(matriz):
    return sum(sum(fila) for fila in matriz)


# ----------------------------------------------------------------------------
# Medición de rendimiento
# ----------------------------------------------------------------------------

def medir_tiempos(tamanos=(100, 500, 1000), generaciones=10):
    """Mide cuánto tarda la versión secuencial en simular varias generaciones
    para cada tamaño de tablero e imprime el resultado."""
    for n in tamanos:
        matriz = crear_matriz(n, n, semilla=42)  # mismo tablero siempre
        inicio = time.perf_counter()
        simular(matriz, generaciones)
        fin = time.perf_counter()
        print(f"{n}x{n}, {generaciones} generaciones: {fin - inicio:.4f} s")


# ----------------------------------------------------------------------------
# Interfaz gráfica (tkinter)
# ----------------------------------------------------------------------------

def abrir_interfaz(filas, columnas, tam_celda, densidad):
    import tkinter as tk

    class Aplicacion:
        def __init__(self, raiz):
            self.raiz = raiz
            raiz.title("Juego de la Vida - versión secuencial")
            self.matriz = crear_matriz(filas, columnas, densidad)
            self.generacion = 0
            self.corriendo = False
            self.retardo_ms = 60

            self.lienzo = tk.Canvas(raiz, width=columnas * tam_celda,
                                    height=filas * tam_celda,
                                    bg="white", highlightthickness=0)
            self.lienzo.pack()
            # Se crea un rectángulo por celda una sola vez y luego solo se
            # cambia su color; es mucho más rápido que borrar y redibujar.
            self.rectangulos = [
                [self.lienzo.create_rectangle(
                    j * tam_celda, i * tam_celda,
                    (j + 1) * tam_celda, (i + 1) * tam_celda,
                    outline="#e0e0e0", fill="white")
                 for j in range(columnas)]
                for i in range(filas)]
            self.lienzo.bind("<Button-1>", self.alternar_celda)

            panel = tk.Frame(raiz)
            panel.pack(fill="x", pady=4)
            self.boton = tk.Button(panel, text="Iniciar", width=9,
                                   command=self.alternar)
            self.boton.pack(side="left", padx=4)
            tk.Button(panel, text="Paso", width=7,
                      command=self.paso).pack(side="left", padx=4)
            tk.Button(panel, text="Aleatorio", width=9,
                      command=self.aleatorio).pack(side="left", padx=4)
            tk.Button(panel, text="Limpiar", width=8,
                      command=self.limpiar).pack(side="left", padx=4)
            self.etiqueta = tk.Label(panel, text="")
            self.etiqueta.pack(side="right", padx=8)
            self.dibujar()

        def dibujar(self):
            for i in range(filas):
                for j in range(columnas):
                    color = "#1b5e20" if self.matriz[i][j] else "white"
                    self.lienzo.itemconfig(self.rectangulos[i][j], fill=color)
            self.etiqueta.config(
                text=f"Generación {self.generacion}   "
                     f"Vivas: {contar_vivas(self.matriz)}   "
                     f"Último paso: {self.ultimo_paso_ms:.1f} ms"
                if hasattr(self, "ultimo_paso_ms") else
                f"Generación {self.generacion}   Vivas: {contar_vivas(self.matriz)}")

        def paso(self):
            inicio = time.perf_counter()
            self.matriz = siguiente_generacion(self.matriz)
            self.ultimo_paso_ms = (time.perf_counter() - inicio) * 1000
            self.generacion += 1
            self.dibujar()

        def ciclo(self):
            if self.corriendo:
                self.paso()
                self.raiz.after(self.retardo_ms, self.ciclo)

        def alternar(self):
            self.corriendo = not self.corriendo
            self.boton.config(text="Pausar" if self.corriendo else "Iniciar")
            if self.corriendo:
                self.ciclo()

        def aleatorio(self):
            self.matriz = crear_matriz(filas, columnas, densidad)
            self.generacion = 0
            self.dibujar()

        def limpiar(self):
            self.matriz = [[0] * columnas for _ in range(filas)]
            self.generacion = 0
            self.dibujar()

        def alternar_celda(self, evento):
            j, i = evento.x // tam_celda, evento.y // tam_celda
            if 0 <= i < filas and 0 <= j < columnas:
                self.matriz[i][j] = 1 - self.matriz[i][j]
                self.dibujar()

    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()


# ----------------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Juego de la Vida secuencial")
    parser.add_argument("--medir_tiempos", action="store_true",
                        help="mide tiempos sin abrir la interfaz")
    parser.add_argument("--filas", type=int, default=60)
    parser.add_argument("--columnas", type=int, default=100)
    parser.add_argument("--celda", type=int, default=9,
                        help="tamaño en píxeles de cada celda")
    parser.add_argument("--densidad", type=float, default=0.25)
    args = parser.parse_args()

    if args.medir_tiempos:
        medir_tiempos()
    else:
        abrir_interfaz(args.filas, args.columnas, args.celda, args.densidad)
