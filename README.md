# Juego de la Vida de Conway: secuencial vs. paralelo

Parcial I de Infraestructuras Paralelas y Distribuidas (750023C), Universidad del Valle.

El proyecto implementa el Juego de la Vida de Conway en dos versiones, una secuencial y una paralela con hilos (`threading`), y compara su rendimiento con gráficas de tiempo y speedup.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `juego_vida_secuencial.py` | Versión secuencial (línea base): lógica del juego e interfaz gráfica |
| `juego_vida_paralelo.py` | Versión paralela con hilos. Reutiliza la lógica del secuencial |
| `analisis_secuencialVSparalelo.py` | Mide ambas versiones y genera las gráficas de comparación |

Los tres archivos deben estar en la misma carpeta.

## Requisitos

- Python 3.8 o superior.
- `tkinter`, para la interfaz gráfica. Viene con Python en Windows y macOS. En Linux se instala aparte:

```bash
sudo apt install python3-tk
```

- `matplotlib`, solo para el análisis de resultados:

```bash
pip install matplotlib
```

## Uso

### Interfaz gráfica (versión secuencial)

```bash
python juego_vida_secuencial.py

# Tablero más grande, celdas más pequeñas
python juego_vida_secuencial.py --filas 80 --columnas 120 --celda 8
```

| Opción | Por defecto | Descripción |
|---|---|---|
| `--filas` | 60 | Filas del tablero |
| `--columnas` | 100 | Columnas del tablero |
| `--celda` | 9 | Tamaño de cada celda en píxeles |
| `--densidad` | 0.25 | Probabilidad de que una celda empiece viva |

Controles de la interfaz:

- **Iniciar / Pausar**: avanza generaciones de forma continua.
- **Paso**: avanza una sola generación.
- **Aleatorio**: genera un tablero nuevo.
- **Limpiar**: deja todas las celdas muertas.
- **Clic sobre una celda**: la invierte, para dibujar patrones a mano.

### Verificar la versión paralela

```bash
python juego_vida_paralelo.py
```

Ejecuta la simulación paralela con 1, 2, 4 y 7 hilos y la compara con la secuencial sobre el mismo tablero. Debe imprimir `OK` para cada cantidad de hilos.

### Análisis de resultados

```bash
python analisis_secuencialVSparalelo.py
```

Mide la secuencial y la paralela, imprime los tiempos en consola, muestra dos gráficas y las guarda en `resultados.png`:

1. Tiempo de ejecución de la secuencial frente a la paralela con 2, 4 y 8 hilos, para cada tamaño de tablero.
2. Speedup de la paralela (tiempo secuencial dividido por tiempo paralelo). Un valor mayor que 1 significa que la paralela fue más rápida.

Para cambiar el experimento, edita las constantes al inicio del archivo:

| Constante | Valor por defecto | Qué controla |
|---|---|---|
| `TAMANOS` | `[100, 500, 1000]` | Tableros de 100x100, 500x500 y 1000x1000 |
| `GENERACIONES` | `10` | Generaciones simuladas en cada medición |
| `REPETICIONES` | `3` | Veces que se repite cada medición para promediarla |
| `HILOS` | `[2, 4, 8]` | Cantidades de hilos a comparar |

Con los tamaños por defecto puede tardar varios minutos, sobre todo por el tablero de 1000x1000. Para una prueba rápida, baja `TAMANOS` y `REPETICIONES`.

## Reglas del juego

- Una célula viva con menos de 2 vecinos vivos muere por soledad.
- Una célula viva con 2 o 3 vecinos vivos sobrevive.
- Una célula viva con más de 3 vecinos vivos muere por sobrepoblación.
- Una célula muerta con exactamente 3 vecinos vivos nace.

Los bordes del tablero se tratan como celdas muertas.

## Cómo está organizado el código

### Versión secuencial

- `crear_matriz`: genera el tablero aleatorio. Con una semilla fija, el resultado es reproducible.
- `contar_vecinos`: cuenta los vecinos vivos de una celda.
- `calcular_filas(actual, nueva, inicio, fin)`: aplica las reglas a un rango de filas. **Es la función que la versión paralela reparte entre los hilos.**
- `siguiente_generacion`: calcula una generación completa.
- `simular`: encadena varias generaciones.

### Versión paralela

- **División del trabajo:** la matriz se parte en bloques de filas contiguas, un bloque por hilo (`_rangos`).
- **Hilos reutilizados:** `JuegoParalelo` crea los hilos una sola vez y los mantiene vivos durante todas las generaciones, en lugar de crearlos de nuevo en cada paso.
- **Sin condiciones de carrera:** todos los hilos leen del tablero `actual` y cada uno escribe solo en sus propias filas de `nueva`. Como los rangos de escritura no se solapan, no hacen falta mutexes.
- **Sincronización con dos barreras por generación:** la barrera de inicio libera a los hilos cuando el tablero ya está listo, y la barrera de fin hace que el hilo principal espere a que todos terminen antes de intercambiar `actual` y `nueva`.
- `simular_paralela(matriz, generaciones, p)`: avanza las generaciones con `p` hilos y devuelve el tablero final.

## Nota sobre el GIL

En CPython normal solo un hilo ejecuta código Python a la vez (GIL), así que la versión con hilos es correcta pero casi no se acelera: el speedup suele quedar cerca de 1, o incluso por debajo por el costo de coordinar los hilos. Con una versión de Python sin GIL (los *builds* `3.13t` o `3.14t`) los hilos sí corren en paralelo real y se espera ver aceleración, con el mismo código.