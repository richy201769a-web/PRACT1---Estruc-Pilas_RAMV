"""
Simulador gráfico e interactivo de una PILA (capacidad máxima = 8, TOPE = 0 al inicio).

Cómo ejecutarlo:   python pila_interactiva.py
(Solo usa tkinter, que ya viene con Python. En Linux: sudo apt install python3-tk)

Qué se puede hacer:
  * Modo libre: escribir un valor (máx. 4 caracteres) y pulsar "Insertar", o pulsar "Eliminar".
  * Ejercicio 1: ejecutar las 9 operaciones (a-i) paso a paso o todas seguidas.
  * Se ve la pila con animación, la flecha del TOPE y los errores en rojo
    (desbordamiento = insertar con la pila llena, subdesbordamiento = eliminar con la pila vacía).

RESPUESTAS DEL EJERCICIO
  ¿Con cuántos elementos quedó la pila?
    Con 2 elementos: V (base) y R (tope). TOPE = 2.

  ¿Hubo algún caso de error (desbordamiento o subdesbordamiento)?
    Sí, uno: en la operación e) Eliminar (PILA, U) hubo SUBDESBORDAMIENTO
    (underflow). Después de c) y d) la pila quedó vacía (TOPE = 0) y se intentó
    eliminar de una pila vacía. La operación no se realiza, el TOPE sigue en 0
    y la variable U no recibe ningún valor.
    No hubo desbordamiento: la pila nunca pasó de 2 elementos (capacidad = 8).
"""

import tkinter as tk

CAPACIDAD = 8
MAX_CHARS = 4                # máximo de caracteres por elemento de la pila

# ---- Dibujo ---------------------------------------------------------------
W, H = 450, 510
SLOT_H = 50
Y_BASE = 480                 # línea inferior de la pila
X0, X1 = 90, 270             # borde izquierdo / derecho de las celdas
Y_ENTRADA = 25               # altura desde donde "cae" / hacia donde "sube" un elemento

BG, CARD, TXT = "#eef1f7", "#ffffff", "#1f2937"
AZUL, ROJO, VERDE, GRIS = "#2563eb", "#dc2626", "#16a34a", "#8892a6"
PALETA = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#059669", "#0891b2", "#ca8a04", "#4f46e5"]

# ---- Ejercicio ------------------------------------------------------------
EJERCICIO = [
    ("a", "insertar", "X"), ("b", "insertar", "Y"), ("c", "eliminar", "Z"),
    ("d", "eliminar", "T"), ("e", "eliminar", "U"), ("f", "insertar", "V"),
    ("g", "insertar", "W"), ("h", "eliminar", "p"), ("i", "insertar", "R"),
]


class Pila:
    """Pila con capacidad fija. El TOPE es la cantidad de elementos guardados."""

    def __init__(self, capacidad=CAPACIDAD):
        self.capacidad = capacidad
        self.datos = []

    @property
    def tope(self):
        return len(self.datos)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Simulador de PILA - Estructuras de datos")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.pila = Pila()
        self.colores = {}
        self.anim = None          # elemento que se está animando: {"v": valor, "y": posición}
        self.busy = False         # hay una animación en curso
        self.auto = False         # "Ejecutar todo" en curso
        self.flash = False        # fondo rojo al ocurrir un error
        self.paso = 0
        self.errores = []

        self.construir_interfaz()
        self.actualizar()
        self.log("Pila vacía (TOPE = 0). Capacidad máxima: 8.", "info")

    # ------------------------------------------------------------ interfaz
    def construir_interfaz(self):
        izq = tk.Frame(self.root, bg=BG)
        izq.grid(row=0, column=0, padx=(14, 7), pady=14)
        self.canvas = tk.Canvas(izq, width=W, height=H, bg=CARD, highlightthickness=1,
                                highlightbackground="#d5dbe8")
        self.canvas.pack()

        der = tk.Frame(self.root, bg=BG)
        der.grid(row=0, column=1, padx=(7, 14), pady=14, sticky="n")

        tk.Label(der, text="Simulador de PILA", bg=BG, fg=TXT,
                 font=("Helvetica", 20, "bold")).pack(anchor="w")
        self.estado = tk.Label(der, text="", bg=BG, fg=AZUL, font=("Helvetica", 14, "bold"))
        self.estado.pack(anchor="w", pady=(0, 8))

        # --- modo libre
        c1 = self.tarjeta(der, "Modo libre")
        fila = tk.Frame(c1, bg=CARD)
        fila.pack(fill="x")
        # Validación: no deja escribir (ni pegar) más de MAX_CHARS caracteres
        vcmd = (self.root.register(lambda s: len(s) <= MAX_CHARS), "%P")
        self.entrada = tk.Entry(fila, width=7, font=("Helvetica", 14), justify="center",
                                validate="key", validatecommand=vcmd)
        self.entrada.pack(side="left", padx=(0, 8))
        self.entrada.bind("<Return>", lambda e: self.manual(self.click_insertar))
        self.entrada.focus()
        self.boton(fila, "Insertar", VERDE, lambda: self.manual(self.click_insertar)).pack(side="left", padx=3)
        self.boton(fila, "Eliminar", ROJO, lambda: self.manual(self.eliminar)).pack(side="left", padx=3)
        tk.Label(c1, text=f"Máximo {MAX_CHARS} caracteres por elemento", bg=CARD, fg=GRIS,
                 font=("Helvetica", 9)).pack(anchor="w", pady=(4, 0))

        # --- ejercicio
        c2 = self.tarjeta(der, "Ejercicio 1 (operaciones a - i)")
        self.lista = tk.Listbox(c2, height=len(EJERCICIO), width=34, font=("Courier", 12),
                                activestyle="none", selectbackground="#dbe5ff",
                                selectforeground=TXT, relief="flat", highlightthickness=0)
        self.lista.pack(fill="x")
        self.llenar_lista()
        fila2 = tk.Frame(c2, bg=CARD)
        fila2.pack(fill="x", pady=(8, 0))
        self.boton(fila2, "Siguiente ▶", AZUL, lambda: self.manual(self.siguiente)).pack(side="left", padx=2)
        self.boton(fila2, "Ejecutar todo ⏩", "#7c3aed", lambda: self.manual(self.todo)).pack(side="left", padx=2)
        self.boton(fila2, "Reiniciar ↺", "#6b7280", lambda: self.manual(self.reiniciar)).pack(side="left", padx=2)

        # --- bitácora
        c3 = self.tarjeta(der, "Bitácora")
        self.txt = tk.Text(c3, width=44, height=9, font=("Courier", 11), relief="flat",
                           state="disabled", wrap="word", bg="#f8fafc")
        self.txt.pack(fill="x")
        self.txt.tag_config("ok", foreground=TXT)
        self.txt.tag_config("info", foreground=AZUL)
        self.txt.tag_config("err", foreground=ROJO, font=("Courier", 11, "bold"))
        self.txt.tag_config("fin", foreground=VERDE, font=("Courier", 11, "bold"))

    def tarjeta(self, padre, titulo):
        marco = tk.Frame(padre, bg=CARD, padx=10, pady=8, highlightthickness=1,
                         highlightbackground="#d5dbe8")
        marco.pack(fill="x", pady=5)
        tk.Label(marco, text=titulo, bg=CARD, fg=GRIS, font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 4))
        return marco

    def boton(self, padre, texto, color, cmd):
        return tk.Button(padre, text=texto, command=cmd, bg=color, fg="white",
                         activebackground=color, activeforeground="white", relief="flat",
                         font=("Helvetica", 11, "bold"), padx=10, pady=4, cursor="hand2")

    def llenar_lista(self):
        self.lista.delete(0, tk.END)
        for letra, tipo, arg in EJERCICIO:
            self.lista.insert(tk.END, f" {letra}) {tipo.capitalize()} (PILA, {arg})")

    # ------------------------------------------------------------ dibujo
    def color(self, v):
        if v not in self.colores:
            self.colores[v] = PALETA[len(self.colores) % len(PALETA)]
        return self.colores[v]

    def bloque(self, v, y):
        c = self.canvas
        c.create_rectangle(X0 + 8, y + 6, X1 - 8, y + SLOT_H - 4, fill="#cbd2e0", outline="")  # sombra
        c.create_rectangle(X0 + 8, y + 4, X1 - 8, y + SLOT_H - 6, fill=self.color(v), outline="")
        c.create_text((X0 + X1) / 2, y + SLOT_H / 2 - 1, text=v, fill="white",
                      font=("Helvetica", 18, "bold"))

    def draw(self):
        c = self.canvas
        c.delete("all")
        c.create_rectangle(0, 0, W, H, fill="#fdecea" if self.flash else CARD, outline="")
        c.create_text(W / 2, 12, text=f"PILA  (capacidad = {CAPACIDAD})", fill=GRIS,
                      font=("Helvetica", 11, "bold"))

        for i in range(1, CAPACIDAD + 1):
            y = Y_BASE - i * SLOT_H
            c.create_rectangle(X0, y, X1, y + SLOT_H, outline="#cfd6e4", dash=(4, 3))
            c.create_text(X0 - 22, y + SLOT_H / 2, text=str(i), fill=GRIS, font=("Helvetica", 12))
        c.create_line(X0 - 12, Y_BASE, X1 + 12, Y_BASE, width=5, fill="#44506b")

        for i, v in enumerate(self.pila.datos, 1):
            self.bloque(v, Y_BASE - i * SLOT_H)
        if self.anim:
            self.bloque(self.anim["v"], self.anim["y"])

        # flecha del TOPE
        n = self.pila.tope
        y = Y_BASE - n * SLOT_H + (SLOT_H / 2 if n > 0 else 0)
        col = ROJO if self.flash else AZUL
        c.create_line(X1 + 90, y, X1 + 12, y, arrow=tk.LAST, width=4, fill=col, arrowshape=(14, 16, 6))
        c.create_text(X1 + 95, y, text=f"TOPE = {n}", anchor="w", fill=col,
                      font=("Helvetica", 12, "bold"))
        if n == CAPACIDAD:
            c.create_text(W / 2, 40, text="¡PILA LLENA!", fill=ROJO, font=("Helvetica", 12, "bold"))

    def actualizar(self):
        n = self.pila.tope
        self.estado.config(text=f"TOPE = {n}   ·   {n}/{CAPACIDAD} elementos")
        self.draw()

    def log(self, texto, tag="ok"):
        self.txt.config(state="normal")
        self.txt.insert("end", texto + "\n", tag)
        self.txt.see("end")
        self.txt.config(state="disabled")

    # ------------------------------------------------------------ animación
    def animar(self, v, y0, y1, fin):
        self.anim = {"v": v, "y": y0}
        paso = 16 if y1 > y0 else -16

        def tick():
            self.anim["y"] += paso
            if (paso > 0 and self.anim["y"] >= y1) or (paso < 0 and self.anim["y"] <= y1):
                self.anim = None
                fin()
                return
            self.draw()
            self.root.after(12, tick)

        tick()

    def error(self, tipo, etq, mensaje, fin):
        self.busy = True
        self.errores.append(f"{etq}{tipo.lower()}")
        self.log(f"{etq}ERROR de {tipo}: {mensaje}", "err")
        self.flash = True
        self.draw()

        def quitar():
            self.flash = False
            self.busy = False
            self.actualizar()
            if fin:
                fin()

        self.root.after(800, quitar)

    # ------------------------------------------------------------ operaciones
    def insertar(self, v, etq="", fin=None):
        if self.busy:
            return
        self.log(f"{etq}Insertar (PILA, {v})")
        if self.pila.tope == CAPACIDAD:
            self.error("DESBORDAMIENTO", etq,
                       f"la pila está llena (TOPE = {CAPACIDAD}), no cabe '{v}'.", fin)
            return
        self.busy = True
        destino = Y_BASE - (self.pila.tope + 1) * SLOT_H

        def listo():
            self.pila.datos.append(v)
            self.busy = False
            self.actualizar()
            if fin:
                fin()

        self.animar(v, Y_ENTRADA, destino, listo)

    def eliminar(self, var="", etq="", fin=None):
        if self.busy:
            return
        self.log(f"{etq}Eliminar (PILA, {var or '-'})")
        if self.pila.tope == 0:
            self.error("SUBDESBORDAMIENTO", etq,
                       "la pila está vacía (TOPE = 0), no hay nada que eliminar.", fin)
            return
        self.busy = True
        y0 = Y_BASE - self.pila.tope * SLOT_H
        v = self.pila.datos.pop()
        self.log(f"   {var} = {v}" if var else f"   Se eliminó: {v}", "info")
        self.actualizar()

        def listo():
            self.busy = False
            self.actualizar()
            if fin:
                fin()

        self.animar(v, y0, Y_ENTRADA, listo)

    # ------------------------------------------------------------ controles
    def manual(self, funcion):
        if not self.busy and not self.auto:
            funcion()

    def click_insertar(self):
        v = self.entrada.get().strip()[:MAX_CHARS]
        if not v:
            self.log("Escribe un valor para insertar.", "info")
            return
        self.entrada.delete(0, tk.END)
        self.insertar(v)

    def siguiente(self, fin=None):
        if self.busy or self.paso >= len(EJERCICIO):
            return
        letra, tipo, arg = EJERCICIO[self.paso]
        i = self.paso
        self.paso += 1
        self.lista.selection_clear(0, tk.END)
        self.lista.selection_set(i)
        errores_antes = len(self.errores)

        def despues():
            self.lista.itemconfig(i, fg=ROJO if len(self.errores) > errores_antes else VERDE)
            if self.paso == len(EJERCICIO):
                self.resumen()
            if fin:
                fin()

        etq = f"{letra}) "
        if tipo == "insertar":
            self.insertar(arg, etq, despues)
        else:
            self.eliminar(arg, etq, despues)

    def todo(self):
        self.auto = True

        def seguir():
            if self.paso < len(EJERCICIO):
                self.root.after(400, lambda: self.siguiente(seguir))
            else:
                self.auto = False

        if self.paso >= len(EJERCICIO):
            self.auto = False
            return
        self.siguiente(seguir)

    def resumen(self):
        n = self.pila.tope
        self.log("-" * 40, "fin")
        self.log("¿Con cuántos elementos quedó la pila?", "fin")
        self.log(f"  Con {n} elemento(s). TOPE = {n}", "fin")
        self.log("¿Hubo algún error?", "fin")
        if not self.errores:
            self.log("  No hubo errores.", "fin")
        for e in self.errores:
            if "subdesbordamiento" in e:
                expl = "se intentó ELIMINAR con la pila vacía (TOPE = 0)."
            else:
                expl = f"se intentó INSERTAR con la pila llena (TOPE = {CAPACIDAD})."
            self.log(f"  Sí: {e} -> {expl}", "err")

    def reiniciar(self):
        self.pila = Pila()
        self.colores = {}
        self.paso = 0
        self.errores = []
        self.llenar_lista()
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.config(state="disabled")
        self.log("Pila reiniciada (TOPE = 0).", "info")
        self.actualizar()


if __name__ == "__main__":
    ventana = tk.Tk()
    App(ventana)
    ventana.mainloop()