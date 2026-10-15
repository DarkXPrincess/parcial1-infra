"""
Parcial I - Infraestructuras Paralelas y Distribuidas (750023C)
Análisis: versión secuencial vs. versión paralela (hilos)

Mide cuánto tarda cada versión con los mismos tableros y dibuja dos gráficas:
  1. Tiempo de ejecución de la secuencial frente a la paralela con 2, 4 y 8 hilos.
  2. Speedup (tiempo secuencial / tiempo paralelo): cuántas veces más rápida
     (o más lenta) es la paralela que la secuencial.

Necesita estar en la misma carpeta que juego_vida_secuencial.py y
juego_vida_paralelo.py. Si quieres cambiar el experimento, edita las cuatro
constantes de abajo.

Uso:
    python analisis_secuencialVSparalelo.py
"""

import time

import matplotlib.pyplot as plt

from juego_vida_secuencial import crear_matriz, simular
from juego_vida_paralelo import simular_paralela

# --- Parámetros del experimento ---------------------------------------------
TAMANOS = [100, 500, 1000]   # tableros de 100x100, 500x500 y 1000x1000
GENERACIONES = 10
REPETICIONES = 3             # se promedia para que un tiempo raro no pese tanto
HILOS = [2, 4, 8]            # cantidades de hilos a comparar
# -----------------------------------------------------------------------------

COLOR_SECUENCIAL = "#7f7f7f"
COLORES_HILOS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def tiempo_promedio(funcion):
    """Ejecuta 'funcion' varias veces y devuelve (tiempo promedio, resultado)."""
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        resultado = funcion()
        tiempos.append(time.perf_counter() - inicio)
    return sum(tiempos) / len(tiempos), resultado


def medir():
    """Devuelve dos diccionarios:
         t_seq[n]    -> tiempo secuencial para el tablero de n x n
         t_par[n][p] -> tiempo paralelo con p hilos
    """
    t_seq, t_par = {}, {}
    for n in TAMANOS:
        tablero = crear_matriz(n, n, semilla=42)   # mismo tablero para todos

        t_seq[n], esperado = tiempo_promedio(lambda: simular(tablero, GENERACIONES))
        print(f"{n}x{n}  secuencial: {t_seq[n]:.3f} s")

        t_par[n] = {}
        for p in HILOS:
            t_par[n][p], obtenido = tiempo_promedio(
                lambda: simular_paralela(tablero, GENERACIONES, p))
            ok = "OK" if obtenido == esperado else "RESULTADO DISTINTO"
            print(f"{n}x{n}  {p} hilos: {t_par[n][p]:.3f} s  "
                  f"(speedup {t_seq[n] / t_par[n][p]:.2f})  {ok}")
        print()
    return t_seq, t_par


def graficar(t_seq, t_par):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    posiciones_base = range(len(TAMANOS))
    etiquetas = [f"{n}x{n}" for n in TAMANOS]

    # --- Gráfica 1: tiempo de la secuencial frente a la paralela -------------
    versiones = ["Secuencial"] + [f"Paralela, {p} hilos" for p in HILOS]
    colores = [COLOR_SECUENCIAL] + COLORES_HILOS[:len(HILOS)]
    ancho = 0.8 / len(versiones)
    for k, (nombre, color) in enumerate(zip(versiones, colores)):
        tiempos = [t_seq[n] if k == 0 else t_par[n][HILOS[k - 1]] for n in TAMANOS]
        posiciones = [i + k * ancho for i in posiciones_base]
        barras = ax1.bar(posiciones, tiempos, ancho, label=nombre, color=color)
        ax1.bar_label(barras, fmt="%.2f", fontsize=8, padding=2)
    ax1.set_xticks([i + 0.4 - ancho / 2 for i in posiciones_base])
    ax1.set_xticklabels(etiquetas)
    ax1.set_xlabel("Tamaño del tablero")
    ax1.set_ylabel("Tiempo (s)")
    ax1.set_title(f"Tiempo de ejecución ({GENERACIONES} generaciones)")
    ax1.set_ylim(0, ax1.get_ylim()[1] * 1.08)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)

    # --- Gráfica 2: speedup de la paralela respecto a la secuencial ----------
    ancho2 = 0.8 / len(HILOS)
    for k, p in enumerate(HILOS):
        speedups = [t_seq[n] / t_par[n][p] for n in TAMANOS]
        posiciones = [i + k * ancho2 for i in posiciones_base]
        barras = ax2.bar(posiciones, speedups, ancho2, label=f"{p} hilos",
                         color=COLORES_HILOS[k])
        ax2.bar_label(barras, fmt="%.2f", fontsize=8, padding=2)
    ax2.axhline(1, color=COLOR_SECUENCIAL, linestyle="--", linewidth=1.2,
                label="Secuencial (speedup = 1)")
    ax2.set_xticks([i + 0.4 - ancho2 / 2 for i in posiciones_base])
    ax2.set_xticklabels(etiquetas)
    ax2.set_xlabel("Tamaño del tablero")
    ax2.set_ylabel("Speedup (veces más rápida que la secuencial)")
    ax2.set_title("Speedup de la paralela")
    ax2.set_ylim(0, max(1.2, ax2.get_ylim()[1] * 1.08))
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)

    fig.tight_layout()
    fig.savefig("resultados.png", dpi=150)
    print("Gráfica guardada en resultados.png")
    plt.show()


if __name__ == "__main__":
    t_seq, t_par = medir()
    graficar(t_seq, t_par)