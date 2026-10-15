"""
Parcial I - Infraestructuras Paralelas y Distribuidas (750023C)
Juego de la Vida de Conway - INTERFAZ GRAFICA (secuencial y paralela)

Esta interfaz NO calcula nada por su cuenta: reutiliza el codigo del grupo.

  * Secuencial: usa juego_vida_secuencial.siguiente_generacion(matriz)
                (y crear_matriz / contar_vivas del mismo archivo).
  * Paralelo:   usa la clase JuegoParalelo de juego_vida_paralelo.py
                (hilos persistentes + barreras).

Coloca este archivo en la misma carpeta que los otros dos y ejecuta:

    python interfaz_vida.py
    python interfaz_vida.py --n 100 --hilos 4

Solo usa la biblioteca estandar (tkinter).
"""

import argparse
import math
import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import juego_vida_secuencial as sec  # noqa: E402


# vamos a mejorar lo que es el fondo, marcos y tarjetas, por ultimo tambien la caja de texto con los botones
BG = "#0a1a3a"
CARD = "#12306b"
CAMPO = "#1b3a7a"
TXT = "#e8eefc"
TXT_SUAVE = "#9db4e0"
ACENTO = "#3b82f6"

# Tablero claro
COLOR_MUERTA = "#f1f5fb"
COLOR_FONDO = "#f1f5fb"
COLOR_UNICO = "#1b5e20"
PALETA = [
    "#7F77DD",
    "#1D9E75",
    "#D85A30",
    "#D4537E",
    "#378ADD",
    "#BA7517",
    "#639922",
    "#888780",
]
LADO_MAX_PX = 780  # aqui es donde estan los colores de las celulas
SEMILLA_PRUEBA = 42  # la misma que usa medir_tiempos() del secuencial


# empezamos hacer la conexion
try:
    import juego_vida_paralelo as par

    ERROR_PARALELO = None
except Exception as _e:
    par = None
    ERROR_PARALELO = f"{type(_e).__name__}: {_e}"


def motor_secuencial(matriz, trabajadores):
    return sec.siguiente_generacion(matriz)


class MotorParalelo:
    """Envuelve JuegoParalelo para usarlo como f(matriz, hilos) -> matriz.

    JuegoParalelo guarda su propio tablero y mantiene los hilos vivos. Por eso
    solo se vuelve a crear cuando cambia algo que el no puede saber: otro
    tablero (Aleatorio, Limpiar, patron, nuevo tamano) o otro numero de hilos.
    Pintar celdas con el mouse no obliga a recrearlo: modifica el mismo
    tablero que el motor usa.
    """

    def __init__(self):
        self.juego = None
        self.p_pedido = None

    def __call__(self, matriz, hilos):
        j = self.juego
        if j is None or matriz is not j.actual or hilos != self.p_pedido:
            self.cerrar()
            self.juego = par.JuegoParalelo(matriz, hilos)
            self.p_pedido = hilos
        return self.juego.paso()

    def cerrar(self):
        if self.juego is not None:
            try:
                self.juego.cerrar()
            except Exception:  # noqa: BLE001
                pass
            self.juego = None


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def rangos_filas(n, p):
    """Reparte n filas en p bloques contiguos (solo para colorear)."""
    p = max(1, min(p, n))
    base, resto = divmod(n, p)
    rangos, inicio = [], 0
    for k in range(p):
        fin = inicio + base + (1 if k < resto else 0)
        rangos.append((inicio, fin))
        inicio = fin
    return rangos


PATRONES = {
    "Planeador": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "Parpadeador": [(0, 0), (0, 1), (0, 2)],
    "Bloque": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "Celula aislada": [(0, 0)],
}


# ----------------------------------------------------------------------------
# Interfaz
# ----------------------------------------------------------------------------
class Aplicacion:
    def __init__(self, raiz, n, hilos, densidad):
        self.raiz = raiz
        raiz.title("Juego de la Vida - secuencial vs paralelo")
        self.densidad = densidad
        self.n = n
        self.matriz = sec.crear_matriz(n, n, densidad)
        self.generacion = 0
        self.ultimo_ms = None
        self.corriendo = False
        self.escala = 1.0
        self.id_img = None

        self.motores = {"Secuencial": motor_secuencial}
        self.motor_par = None
        if par is not None:
            self.motor_par = MotorParalelo()
            self.motores["Paralelo"] = self.motor_par
            self.mensaje_motor = (
                "Motor paralelo: juego_vida_paralelo.JuegoParalelo (hilos)"
            )
        else:
            self.mensaje_motor = (
                f"No se pudo importar juego_vida_paralelo.py ({ERROR_PARALELO})"
            )

        self._construir(hilos)
        self._preparar_imagen()
        self._refrescar()

    # dandole temas
    def _aplicar_tema(self):
        self.raiz.configure(bg=BG)
        for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            tkfont.nametofont(nombre).configure(size=11)
        familia = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.f_tit = (familia, 11, "bold")

        e = ttk.Style()
        e.theme_use("clam")
        e.configure(
            ".",
            background=BG,
            foreground=TXT,
            fieldbackground=CAMPO,
            bordercolor=CARD,
            lightcolor=CARD,
            darkcolor=CARD,
            troughcolor=CAMPO,
        )
        e.configure("TFrame", background=BG)
        e.configure("TLabel", background=BG, foreground=TXT)
        e.configure("TLabelframe", background=BG, bordercolor=ACENTO)
        e.configure(
            "TLabelframe.Label", background=BG, foreground=TXT_SUAVE, font=self.f_tit
        )
        e.configure(
            "TButton",
            background=CAMPO,
            foreground=TXT,
            padding=(14, 9),
            borderwidth=0,
            focusthickness=0,
        )
        e.map("TButton", background=[("active", ACENTO), ("pressed", ACENTO)])
        e.configure(
            "Accent.TButton", background=ACENTO, foreground="white", font=self.f_tit
        )
        e.map("Accent.TButton", background=[("active", "#60a5fa")])
        e.configure("TCheckbutton", background=BG, foreground=TXT)
        e.map(
            "TCheckbutton",
            background=[("active", BG)],
            indicatorcolor=[("selected", ACENTO), ("!selected", CAMPO)],
        )
        e.configure(
            "TCombobox",
            fieldbackground=CAMPO,
            background=CAMPO,
            foreground=TXT,
            arrowcolor=TXT,
            padding=4,
        )
        e.map(
            "TCombobox",
            fieldbackground=[("readonly", CAMPO)],
            foreground=[("readonly", TXT)],
            selectbackground=[("readonly", CAMPO)],
            selectforeground=[("readonly", TXT)],
        )
        e.configure(
            "TSpinbox",
            fieldbackground=CAMPO,
            background=CAMPO,
            foreground=TXT,
            arrowcolor=TXT,
            padding=4,
        )
        e.configure("Horizontal.TScale", background=ACENTO, troughcolor=CAMPO)
        self.raiz.option_add("*TCombobox*Listbox.background", CAMPO)
        self.raiz.option_add("*TCombobox*Listbox.foreground", TXT)
        self.raiz.option_add("*TCombobox*Listbox.selectBackground", ACENTO)

    # ------------------------------------------------------------ widgets
    def _construir(self, hilos):
        self._aplicar_tema()  # aqui es donde hacemos el llamado a los temas de la funcion de arriba
        marco = ttk.Frame(self.raiz, padding=16)
        marco.pack(fill="both", expand=True)
        izq = tk.Frame(marco, bg=CARD, padx=10, pady=10)
        izq.grid(row=0, column=0, sticky="n")
        der = ttk.Frame(marco, padding=(12, 0))
        der.grid(row=0, column=1, sticky="n")
        col1 = ttk.Frame(der)
        col1.grid(row=0, column=0, sticky="n", padx=(0, 16))
        col2 = ttk.Frame(der)
        col2.grid(row=0, column=1, sticky="n")

        self.canvas = tk.Canvas(izq, bg=COLOR_FONDO, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._pintar)
        self.canvas.bind("<B1-Motion>", self._pintar)

        # Estadisticas
        est = ttk.LabelFrame(col1, text="Estado", padding=6)
        est.pack(fill="x")
        self.var_gen = tk.StringVar()
        self.var_vivas = tk.StringVar()
        self.var_ms = tk.StringVar()
        for var in (self.var_gen, self.var_vivas, self.var_ms):
            ttk.Label(est, textvariable=var, font=self.f_tit).pack(anchor="w")

        # Botones
        fila = ttk.Frame(col1)
        fila.pack(fill="x", pady=8)
        self.btn_play = ttk.Button(
            fila, text="Iniciar", width=9, style="Accent.TButton", command=self.alternar
        )
        self.btn_play.grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(fila, text="Paso", width=7, command=self.paso).grid(
            row=0, column=1, padx=2
        )
        ttk.Button(fila, text="Aleatorio", width=9, command=self.aleatorio).grid(
            row=1, column=0, padx=2, pady=2
        )
        ttk.Button(fila, text="Limpiar", width=7, command=self.limpiar).grid(
            row=1, column=1, padx=2
        )
        ttk.Button(
            col1,
            text=f"Tablero de prueba (semilla {SEMILLA_PRUEBA})",
            command=self.tablero_prueba,
        ).pack(fill="x")

        # Motor e hilos
        cfg = ttk.LabelFrame(col1, text="Ejecucion", padding=6)
        cfg.pack(fill="x", pady=8)
        ttk.Label(cfg, text="Motor").grid(row=0, column=0, sticky="w")
        self.var_motor = tk.StringVar(value="Secuencial")
        cb = ttk.Combobox(
            cfg,
            textvariable=self.var_motor,
            values=list(self.motores),
            state="readonly",
            width=12,
        )
        cb.grid(row=0, column=1, pady=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._refrescar())
        ttk.Label(cfg, text="Hilos/procesos").grid(row=1, column=0, sticky="w")
        self.var_hilos = tk.IntVar(value=hilos)
        sp = ttk.Spinbox(
            cfg,
            from_=1,
            to=64,
            width=5,
            textvariable=self.var_hilos,
            command=self._refrescar,
        )
        sp.grid(row=1, column=1, sticky="w", pady=2)
        sp.bind("<KeyRelease>", lambda e: self._refrescar())
        ttk.Label(cfg, text="Velocidad").grid(row=2, column=0, sticky="w")
        self.var_vel = tk.IntVar(value=6)
        ttk.Scale(
            cfg, from_=1, to=10, variable=self.var_vel, orient="horizontal", length=110
        ).grid(row=2, column=1, pady=2)

        # Tablero
        tab = ttk.LabelFrame(col2, text="Tablero", padding=6)
        tab.pack(fill="x")
        ttk.Label(tab, text="Tamano NxN").grid(row=0, column=0, sticky="w")
        self.var_n = tk.StringVar(value=str(self.n))
        ttk.Combobox(
            tab,
            textvariable=self.var_n,
            width=6,
            values=["30", "50", "100", "200", "500", "1000"],
        ).grid(row=0, column=1, pady=2)
        ttk.Button(tab, text="Aplicar", width=7, command=self.cambiar_tamano).grid(
            row=0, column=2, padx=2
        )
        ttk.Label(tab, text="Patron").grid(row=1, column=0, sticky="w")
        self.var_patron = tk.StringVar(value="Planeador")
        ttk.Combobox(
            tab,
            textvariable=self.var_patron,
            values=list(PATRONES),
            state="readonly",
            width=12,
        ).grid(row=1, column=1, columnspan=2, sticky="w", pady=2)
        ttk.Button(tab, text="Cargar patron", command=self.cargar_patron).grid(
            row=2, column=0, columnspan=3, sticky="ew"
        )
        self.var_colorear = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab,
            text="Colorear por hilo",
            variable=self.var_colorear,
            command=self._refrescar,
        ).grid(row=3, column=0, columnspan=3, sticky="w")
        self.var_dibujar = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab,
            text="Dibujar tablero",
            variable=self.var_dibujar,
            command=self._refrescar,
        ).grid(row=4, column=0, columnspan=3, sticky="w")

        # Comparacion
        cmp_ = ttk.LabelFrame(col2, text="Comparar secuencial vs paralelo", padding=6)
        cmp_.pack(fill="x", pady=8)
        ttk.Label(cmp_, text="Generaciones").grid(row=0, column=0, sticky="w")
        self.var_gens = tk.IntVar(value=5)
        ttk.Spinbox(cmp_, from_=1, to=100, width=5, textvariable=self.var_gens).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Button(cmp_, text="Comparar", command=self.comparar).grid(
            row=0, column=2, padx=4
        )
        self.var_cmp = tk.StringVar(value="")
        ttk.Label(cmp_, textvariable=self.var_cmp, wraplength=250, justify="left").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

        # Leyenda de hilos
        self.leyenda = ttk.LabelFrame(col2, text="Reparto de filas", padding=6)
        self.leyenda.pack(fill="x")

        # Barra de estado
        self.var_estado = tk.StringVar(value=self.mensaje_motor)
        ttk.Label(
            self.raiz, textvariable=self.var_estado, padding=4, foreground=TXT_SUAVE
        ).pack(side="bottom", fill="x")

    def _preparar_imagen(self):
        n = self.n
        if n <= LADO_MAX_PX:
            px = max(1, LADO_MAX_PX // n)
            self.escala = float(px)
            lado = n * px
        else:
            k = math.ceil(n / LADO_MAX_PX)
            self.escala = 1.0 / k
            lado = n // k
        self.canvas.config(width=lado, height=lado)
        self.canvas.delete("all")
        self.img = tk.PhotoImage(width=n, height=n)
        self.vista = None
        self.id_img = None
        if self.escala >= 6:
            lado = self.n * self.escala
            for k in range(self.n + 1):
                p = k * self.escala
                self.canvas.create_line(p, 0, p, lado, fill="#cfd8e6", tags="grid")
                self.canvas.create_line(0, p, lado, p, fill="#cfd8e6", tags="grid")

    # ------------------------------------------------------------ dibujo
    def _hilos(self):
        try:
            return max(1, int(self.var_hilos.get()))
        except (tk.TclError, ValueError):
            return 1

    def _bandas(self):
        """Lista de (inicio, fin, color) o None si no se colorea por hilo."""
        if not self.var_colorear.get() or self.var_motor.get() == "Secuencial":
            return None
        return [
            (a, b, PALETA[k % len(PALETA)])
            for k, (a, b) in enumerate(par._rangos(self.n, self._hilos()))
        ]

    def dibujar(self):
        if not self.var_dibujar.get():
            return
        bandas = self._bandas()
        color_fila = [COLOR_UNICO] * self.n
        if bandas:
            for a, b, c in bandas:
                for i in range(a, b):
                    color_fila[i] = c
        partes = []
        for i, fila in enumerate(self.matriz):
            tabla = (COLOR_MUERTA, color_fila[i])
            partes.append("{" + " ".join([tabla[v] for v in fila]) + "}")
        self.img.put(" ".join(partes), to=(0, 0))

        if self.escala >= 1:
            px = int(self.escala)
            self.vista = self.img.zoom(px) if px > 1 else self.img
        else:
            self.vista = self.img.subsample(int(round(1 / self.escala)))
        if self.id_img is None:
            self.id_img = self.canvas.create_image(0, 0, anchor="nw", image=self.vista)
        else:
            self.canvas.itemconfig(self.id_img, image=self.vista)

        if bandas:
            self.canvas.tag_raise("grid")
            lado = self.n * self.escala
            for a, _, _ in bandas[1:]:
                y = a * self.escala
                self.canvas.create_line(
                    0, y, lado, y, fill="#ffffff", dash=(4, 4), tags="sep"
                )

    def _quitar_separadores(self):
        self.canvas.delete("sep")

    def _actualizar_leyenda(self):
        for w in self.leyenda.winfo_children():
            w.destroy()
        bandas = self._bandas()
        if not bandas:
            ttk.Label(self.leyenda, text="(un solo bloque: secuencial)").pack(
                anchor="w"
            )
            return
        for k, (a, b, c) in enumerate(bandas):
            f = ttk.Frame(self.leyenda)
            f.pack(anchor="w")
            tk.Label(f, bg=c, width=2).pack(side="left", padx=(0, 6))
            ttk.Label(f, text=f"Hilo {k + 1}: filas {a} a {b - 1}").pack(side="left")

    def _actualizar_info(self):
        self.var_gen.set(f"Generacion: {self.generacion}")
        self.var_vivas.set(f"Celulas vivas: {sec.contar_vivas(self.matriz)}")
        if self.ultimo_ms is None:
            self.var_ms.set("Ultimo paso: -")
        else:
            self.var_ms.set(f"Ultimo paso: {self.ultimo_ms:.2f} ms")

    def _refrescar(self):
        self._quitar_separadores()
        self.dibujar()
        self._actualizar_leyenda()
        self._actualizar_info()

    # ------------------------------------------------------------ acciones
    def _pintar(self, evento):
        j, i = int(evento.x / self.escala), int(evento.y / self.escala)
        if 0 <= i < self.n and 0 <= j < self.n:
            self.matriz[i][j] = 1
            self._quitar_separadores()
            self.dibujar()
            self._actualizar_info()

    def aleatorio(self):
        self.matriz = sec.crear_matriz(self.n, self.n, self.densidad)
        self._reiniciar()

    def tablero_prueba(self):
        self.matriz = sec.crear_matriz(self.n, self.n, self.densidad, SEMILLA_PRUEBA)
        self._reiniciar()

    def limpiar(self):
        self.matriz = [[0] * self.n for _ in range(self.n)]
        self._reiniciar()

    def cargar_patron(self):
        self.matriz = [[0] * self.n for _ in range(self.n)]
        celdas = PATRONES[self.var_patron.get()]
        oi = self.n // 2 - 1 if self.var_patron.get() != "Planeador" else 2
        oj = self.n // 2 - 1 if self.var_patron.get() != "Planeador" else 2
        for di, dj in celdas:
            if 0 <= oi + di < self.n and 0 <= oj + dj < self.n:
                self.matriz[oi + di][oj + dj] = 1
        self._reiniciar()

    def _reiniciar(self):
        self.generacion = 0
        self.ultimo_ms = None
        self._refrescar()

    def cambiar_tamano(self):
        self.pausar()
        try:
            n = max(5, min(2000, int(self.var_n.get())))
        except ValueError:
            messagebox.showwarning("Tamano", "Escribe un numero entero.")
            return
        self.n = n
        self.var_n.set(str(n))
        self._preparar_imagen()
        self.aleatorio()

    def paso(self):
        motor = self.motores[self.var_motor.get()]
        inicio = time.perf_counter()
        try:
            nueva = motor(self.matriz, self._hilos())
        except Exception as e:  # noqa: BLE001
            self.pausar()
            messagebox.showerror("Error en el motor", f"{type(e).__name__}: {e}")
            return
        self.ultimo_ms = (time.perf_counter() - inicio) * 1000
        self.matriz = nueva
        self.generacion += 1
        self._refrescar()

    def cerrar(self):
        self.pausar()
        if self.motor_par is not None:
            self.motor_par.cerrar()
        self.raiz.destroy()

    def pausar(self):
        self.corriendo = False
        self.btn_play.config(text="Iniciar")

    def alternar(self):
        if self.corriendo:
            self.pausar()
        else:
            self.corriendo = True
            self.btn_play.config(text="Pausar")
            self._ciclo()

    def _ciclo(self):
        if not self.corriendo:
            return
        self.paso()
        if self.corriendo:
            self.raiz.after(max(1, 520 - int(self.var_vel.get()) * 48), self._ciclo)

    # ------------------------------------------------------------ comparar
    def comparar(self):
        if "Paralelo" not in self.motores:
            messagebox.showinfo(
                "Comparar", "No se encontro el motor paralelo.\n\n" + self.mensaje_motor
            )
            return
        self.pausar()
        n, hilos = self.n, self._hilos()
        try:
            gens = max(1, int(self.var_gens.get()))
        except (tk.TclError, ValueError):
            gens = 5
        self.var_cmp.set("Midiendo...")
        self.raiz.update_idletasks()

        base = sec.crear_matriz(n, n, self.densidad, SEMILLA_PRUEBA)
        tiempos, finales = {}, {}
        try:
            inicio = time.perf_counter()
            finales["Secuencial"] = sec.simular(base, gens)
            tiempos["Secuencial"] = time.perf_counter() - inicio
            inicio = time.perf_counter()
            finales["Paralelo"] = par.simular_paralela(base, gens, hilos)
            tiempos["Paralelo"] = time.perf_counter() - inicio
        except Exception as e:  # noqa: BLE001
            self.var_cmp.set("")
            messagebox.showerror("Error al comparar", f"{type(e).__name__}: {e}")
            return

        ts, tp = tiempos["Secuencial"], tiempos["Paralelo"]
        speedup = ts / tp if tp > 0 else float("inf")
        iguales = finales["Secuencial"] == finales["Paralelo"]
        self.var_cmp.set(
            f"{n}x{n}, {gens} gen., {len(par._rangos(n, hilos))} hilos\n"
            f"Secuencial: {ts:.3f} s\n"
            f"Paralelo:   {tp:.3f} s\n"
            f"Speedup: {speedup:.2f}x   Eficiencia: {speedup / hilos:.2f}\n"
            f"Resultados: {'IDENTICOS' if iguales else 'DIFERENTES (revisar paralelo)'}"
        )


def main():
    parser = argparse.ArgumentParser(description="Interfaz del Juego de la Vida")
    parser.add_argument("--n", type=int, default=60, help="lado del tablero (NxN)")
    parser.add_argument("--hilos", type=int, default=4, help="hilos/procesos iniciales")
    parser.add_argument("--densidad", type=float, default=0.25)
    args = parser.parse_args()

    raiz = tk.Tk()
    app = Aplicacion(raiz, args.n, args.hilos, args.densidad)
    raiz.protocol("WM_DELETE_WINDOW", app.cerrar)
    raiz.mainloop()


if __name__ == "__main__":
    main()
