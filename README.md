# Juego de la Vida: versión secuencial

Parcial I de Infraestructuras Paralelas y Distribuidas (750023C), Universidad del Valle.

Esta es la línea base secuencial del Juego de la Vida de Conway. Sirve como referencia para medir el speedup de las versiones paralelas (hilos o MPI).

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `juego_vida_secuencial.py` | Lógica del juego, interfaz gráfica y modo benchmark |
| `tiempos_secuencial.csv` | Tiempos que genera el modo benchmark |

## Requisitos

- Python 3.8 o superior.
- `tkinter` para la interfaz gráfica. Viene con Python en Windows y macOS. En Linux se instala aparte:

```bash
sudo apt install python3-tk
```

No se necesitan paquetes externos. El modo `--benchmark` no usa `tkinter`.

## Uso

```bash
# Interfaz gráfica
python juego_vida_secuencial.py

# Tablero más grande, celdas más pequeñas
python juego_vida_secuencial.py --filas 80 --columnas 120 --celda 8

# Medir tiempos sin interfaz (crea tiempos_secuencial.csv)
python juego_vida_secuencial.py --benchmark
```

### Opciones

| Opción | Por defecto | Descripción |
|---|---|---|
| `--benchmark` | apagado | Mide tiempos sin abrir la interfaz |
| `--filas` | 60 | Filas del tablero |
| `--columnas` | 100 | Columnas del tablero |
| `--celda` | 9 | Tamaño de cada celda en píxeles |

### Controles de la interfaz

- **Iniciar / Pausar**: avanza generaciones de forma continua.
- **Paso**: avanza una sola generación.
- **Aleatorio**: genera un tablero nuevo.
- **Limpiar**: deja todas las celdas muertas.
- **Clic sobre una celda**: la invierte, para dibujar patrones a mano.

## Reglas

- Una célula viva con menos de 2 vecinos vivos muere por soledad.
- Una célula viva con 2 o 3 vecinos vivos sobrevive.
- Una célula viva con más de 3 vecinos vivos muere por sobrepoblación.
- Una célula muerta con exactamente 3 vecinos vivos nace.

Los bordes del tablero se tratan como celdas muertas.

## Estructura del código

- `crear_matriz`: genera el tablero aleatorio. Con una semilla fija, el resultado es reproducible.
- `contar_vecinos`: cuenta los vecinos vivos de una celda.
- `calcular_filas(actual, nueva, inicio, fin)`: aplica las reglas a un rango de filas. **Es la función que la versión paralela repartirá entre hilos o procesos.**
- `siguiente_generacion`: calcula una generación completa.
- `simular`: encadena varias generaciones.
- `benchmark`: mide tiempos y guarda el CSV.

## Notas para la versión paralela

- Cada generación lee de `actual` y escribe en `nueva`, así que los trabajadores no se pisan entre sí.
- Hace falta una barrera entre generaciones: ninguna empieza hasta que todas las tareas de la anterior terminen.
- Con `threading` el GIL de Python limita la aceleración en código puro. Para ver speedup real, lo más probable es que haga falta `multiprocessing` o MPI.
- Para comprobar que la versión paralela es correcta, compara su resultado con el de la secuencial usando el mismo tablero y la misma semilla. Deben ser idénticos.

## Resultados de referencia

Medidos en un entorno de pruebas con Python 3.13 y 2 núcleos (10 generaciones, promedio de 3 repeticiones). En tu computador los valores serán distintos.

| Tamaño | Promedio (s) |
|---|---|
| 100x100 | 0.123 |
| 500x500 | 4.007 |
| 1000x1000 | 16.628 |
