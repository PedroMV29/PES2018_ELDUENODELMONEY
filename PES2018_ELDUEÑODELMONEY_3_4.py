#!/usr/bin/env python3
"""PES 2018 DueñodelMundo 3.3. Requiere pesXdecrypter 4.0.0."""
import os
import re
import struct
import subprocess
import tempfile
import shutil
import datetime as dt
import json
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

TRANSFER_OFFSET = 10_740_864
SALARY_OFFSET = 10_740_880
SCALE = 100
# Ajuste verificado en la partida ML00000001 del usuario (NO universal).
SALARY_DELTA = -328_361_100
MAX_AMOUNT = (2**32 - 1) * SCALE
AUX = ("data.dat", "description.dat", "encryptHeader.dat",
       "header.dat", "logo.png", "version.txt")

def parse_amount(s):
    s = s.strip().replace("$", "").replace(" ", "").replace(",", "")
    if not re.fullmatch(r"\d+", s):
        raise ValueError("Introduce una cantidad entera en dólares.")
    n = int(s)
    if n > MAX_AMOUNT or n % SCALE:
        raise ValueError(f"El importe debe ser múltiplo de 100 y no superar ${MAX_AMOUNT:,}.")
    return n

def run(exe, *args):
    kwargs = {"capture_output": True, "text": True, "timeout": 150}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    proc = subprocess.run([str(exe), *(str(a) for a in args)], **kwargs)
    if proc.returncode:
        raise RuntimeError(f"{exe.name} falló:\n{proc.stderr or proc.stdout or proc.returncode}")

def app_dir():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def config_file():
    # Configuracion por usuario, independiente de la carpeta de instalacion.
    root = Path(os.environ.get("APPDATA", str(Path.home()))) / "PES2018_Budget_Editor"
    return root / "config.json"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PES2018_ELDUEÑODELMONEY | 3.4")
        self.geometry("670x620")
        self.minsize(620, 570)
        self.save = tk.StringVar()
        self.tools = tk.StringVar(value=str(Path.home() / "Downloads" / "pesXdecrypter4.0.0"))
        self.output = tk.StringVar(value=str(Path.home() / "Downloads" / "PES2018_Trabajo" / "Editor_Salidas"))
        self.transfer = tk.StringVar(value="")
        self.salary = tk.StringVar(value="")
        self.salary_mode = tk.StringVar(value="base")
        self.loaded_save = None
        self.loaded_values = None
        self.loaded_signature = None
        self.reading = False
        self.current_values = tk.StringVar(value="Selecciona una partida y pulsa Leer presupuestos.")
        self.status = tk.StringVar(value="Selecciona una partida y genera una copia modificada.")
        self.auto_save_dir = Path.home() / "OneDrive" / "Documentos" / "KONAMI" / "PRO EVOLUTION SOCCER 2018" / "save"
        self.found = []
        self.load_config()
        self.build()
        self.detect()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="PES 2018 DueñodelMundo", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(root, text="Editor de presupuestos de Liga Máster · v3.4", foreground="#555").pack(anchor="w", pady=(0, 9))

        group = ttk.LabelFrame(root, text="Partida de Liga Máster", padding=9)
        group.pack(fill="x")
        select = ttk.Frame(group)
        select.pack(fill="x")
        self.save_combo = ttk.Combobox(select, state="readonly", width=27)
        self.save_combo.pack(side="left", fill="x", expand=True)
        self.save_combo.bind("<<ComboboxSelected>>", self.choose_save)
        ttk.Button(select, text="Actualizar", command=self.detect).pack(side="left", padx=(6, 0))
        ttk.Button(select, text="Buscar", command=self.pick_file).pack(side="left", padx=(6, 0))
        ttk.Button(group, text="LEER PRESUPUESTOS", command=self.read_budgets).pack(anchor="w", pady=(7, 0))

        budget = ttk.LabelFrame(root, text="Presupuestos en dólares", padding=9)
        budget.pack(fill="x", pady=9)
        budget.columnconfigure(1, weight=1)
        budget.columnconfigure(2, weight=1)
        ttk.Label(budget, text="Concepto").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(budget, text="Actual (leído)").grid(row=0, column=1, sticky="w", padx=8)
        ttk.Label(budget, text="Nuevo (editable)").grid(row=0, column=2, sticky="w", padx=8)
        self.original_transfer = tk.StringVar(value="Sin leer")
        self.original_salary = tk.StringVar(value="Sin leer")
        ttk.Label(budget, text="Fichajes:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(budget, textvariable=self.original_transfer).grid(row=1, column=1, sticky="w", padx=8)
        ttk.Entry(budget, textvariable=self.transfer, width=19).grid(row=1, column=2, sticky="ew", padx=8)
        ttk.Label(budget, text="Salarios (base):").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(budget, textvariable=self.original_salary).grid(row=2, column=1, sticky="w", padx=8)
        ttk.Entry(budget, textvariable=self.salary, width=19).grid(row=2, column=2, sticky="ew", padx=8)
        ttk.Button(budget, text="Restaurar valores leídos", command=self.restore_values).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 5))
        self.visible_radio = ttk.Radiobutton(budget, text="Saldo visible estimado (solo ML00000001 calibrada)", variable=self.salary_mode, value="visible")
        self.visible_radio.grid(row=4, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(budget, text="Presupuesto salarial base almacenado (recomendado)", variable=self.salary_mode, value="base").grid(row=5, column=0, columnspan=3, sticky="w")

        actions = ttk.LabelFrame(root, text="Acciones", padding=9)
        actions.pack(fill="x")
        ttk.Button(actions, text="GENERAR ARCHIVO MODIFICADO", command=self.generate).pack(fill="x", pady=(0, 5))
        ttk.Button(actions, text="APLICAR DIRECTAMENTE A LA PARTIDA", command=self.apply_direct).pack(fill="x")
        links = ttk.Frame(actions)
        links.pack(fill="x", pady=(7, 0))
        ttk.Button(links, text="Configuración de carpetas", command=self.show_settings).pack(side="left")
        ttk.Button(links, text="Abrir salida", command=self.open_output).pack(side="left", padx=6)
        ttk.Button(links, text="Acerca del proyecto", command=self.show_about).pack(side="right")
        ttk.Label(root, text="Aviso: el saldo salarial visible puede diferir del valor base.\nPara aplicar directamente, cierra PES 2018. Se crea respaldo antes de reemplazar.", foreground="#555", wraplength=620).pack(anchor="w", pady=(10, 5))
        ttk.Separator(root).pack(fill="x", pady=(3, 5))
        ttk.Label(root, textvariable=self.status, wraplength=620).pack(anchor="w")

    def show_settings(self):
        window = tk.Toplevel(self)
        window.title("Configuración de carpetas")
        window.geometry("670x215")
        window.resizable(True, False)
        window.transient(self)
        panel = ttk.Frame(window, padding=12)
        panel.pack(fill="both", expand=True)
        self.path_row(panel, "Partida ML:", self.save, self.pick_file)
        self.path_row(panel, "pesXdecrypter:", self.tools, self.pick_tools)
        self.path_row(panel, "Carpeta de salida:", self.output, self.pick_output)
        ttk.Button(panel, text="Añadir carpeta de partidas", command=self.pick_save_folder).pack(anchor="w", pady=8)
        ttk.Button(panel, text="Guardar y cerrar", command=lambda: (self.save_config(), window.destroy())).pack(anchor="e")

    def show_about(self):
        messagebox.showinfo("Acerca del proyecto",
            "PES 2018 DueñodelMundo\nPES2018_ELDUEÑODELMONEY · Versión 3.4\n\n"
            "Editor no oficial de presupuestos de Liga Máster para PES 2018 (PC).\n"
            "Permite generar una copia o aplicar cambios con respaldo.\n\n"
            "Proyecto independiente; no afiliado a KONAMI.\n"
            "Repositorio: pendiente de publicar.\n"
            "Requiere pesXdecrypter 4.0.0 instalado por separado.")

    def path_row(self, parent, label, variable, callback):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=label, width=19).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Buscar", command=callback).pack(side="left")

    def load_config(self):
        try:
            data = json.loads(config_file().read_text(encoding="utf-8"))
            for key, var in (("tools", self.tools), ("output", self.output)):
                if isinstance(data.get(key), str):
                    var.set(data[key])
            if isinstance(data.get("save_folder"), str):
                self.auto_save_dir = Path(data["save_folder"])
        except (OSError, ValueError, TypeError):
            pass

    def save_config(self):
        try:
            p = config_file()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"tools": self.tools.get(), "output": self.output.get(),
                                     "save_folder": str(self.auto_save_dir)}, indent=2), encoding="utf-8")
        except OSError:
            pass

    def on_close(self):
        self.save_config()
        self.destroy()

    def candidate_folders(self):
        # Rutas tipicas de Windows, incluyendo Documentos redirigidos a OneDrive.
        home = Path.home()
        roots = [home / "Documents", home / "Documentos",
                 home / "OneDrive" / "Documents", home / "OneDrive" / "Documentos"]
        for item in home.glob("OneDrive*"):
            if item.is_dir():
                roots.extend((item / "Documents", item / "Documentos"))
        paths = [self.auto_save_dir]
        paths.extend(root / "KONAMI" / "PRO EVOLUTION SOCCER 2018" / "save" for root in roots)
        unique = []
        seen = set()
        for path in paths:
            key = os.path.normcase(os.path.abspath(str(path)))
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    def detect(self):
        previous = self.save.get()
        found = {}
        for folder in self.candidate_folders():
            if not folder.is_dir():
                continue
            try:
                for p in folder.iterdir():
                    if p.is_file() and re.fullmatch(r"ML\d{8}", p.name, re.IGNORECASE):
                        found[os.path.normcase(str(p.resolve()))] = p
            except OSError:
                continue
        self.found = sorted(found.values(), key=lambda p: (p.name.lower(), str(p.parent).lower()))
        self.save_combo["values"] = [f"{p.name}  |  {p.parent}" for p in self.found]
        if not self.found:
            self.status.set("No se encontraron partidas. Usa 'Añadir carpeta de partidas'.")
            return
        idx = next((i for i, p in enumerate(self.found) if str(p) == previous), 0)
        self.save_combo.current(idx)
        self.set_selected_save(self.found[idx])
        self.status.set(f"{len(self.found)} partida(s) detectada(s). Selecciona la que quieras editar.")

    def choose_save(self, event=None):
        idx = self.save_combo.current()
        if 0 <= idx < len(self.found):
            self.set_selected_save(self.found[idx])

    def set_selected_save(self, path):
        path = Path(path)
        changed = str(path) != self.save.get()
        self.save.set(str(path))
        if changed:
            self.loaded_save = None
            self.loaded_values = None
            self.loaded_signature = None
            self.original_transfer.set("Sin leer")
            self.original_salary.set("Sin leer")
            self.transfer.set("")
            self.salary.set("")
            self.salary_mode.set("base")
            self.current_values.set("Sin leer. Pulsa LEER PRESUPUESTOS DE LA PARTIDA.")
        # La calibración visible fue validada únicamente para ML00000001.
        self.visible_radio.configure(state="normal" if path.name.upper() == "ML00000001" else "disabled")

    def read_budgets(self):
        if self.reading:
            return
        try:
            src = Path(self.save.get().strip())
            tools = Path(self.tools.get().strip())
            if not src.is_file() or not re.fullmatch(r"ML\d{8}", src.name, re.I):
                raise ValueError("Selecciona una partida ML válida.")
            if not (tools / "decrypter18.exe").is_file():
                raise ValueError("No se encuentra decrypter18.exe. Revisa la carpeta pesXdecrypter.")
            self.reading = True
            self.status.set("Leyendo presupuestos de la partida... espera.")
            self.update_idletasks()
            with tempfile.TemporaryDirectory(prefix="pes2018_read_") as td:
                extracted = Path(td) / "data"
                extracted.mkdir()
                run(tools / "decrypter18.exe", src, extracted)
                dat = extracted / "data.dat"
                if not dat.is_file() or dat.stat().st_size < SALARY_OFFSET + 4:
                    raise RuntimeError("No se pudo leer data.dat o el formato es incompatible.")
                with dat.open("rb") as f:
                    f.seek(TRANSFER_OFFSET)
                    transfer = struct.unpack("<I", f.read(4))[0] * SCALE
                    f.seek(SALARY_OFFSET)
                    salary = struct.unpack("<I", f.read(4))[0] * SCALE
            self.loaded_save = str(src)
            self.loaded_values = (transfer, salary)
            self.loaded_signature = (src.stat().st_size, src.stat().st_mtime_ns)
            self.original_transfer.set(f"${transfer:,}")
            self.original_salary.set(f"${salary:,}")
            self.transfer.set(str(transfer))
            self.salary.set(str(salary))
            self.salary_mode.set("base")
            self.current_values.set(f"LEÍDO: Fichajes base ${transfer:,} | Salarios base ${salary:,} (no es el saldo visible del juego)")
            self.status.set(f"Presupuestos cargados de {src.name}. Puedes editar los campos y generar una copia.")
        except Exception as exc:
            self.loaded_save = None
            self.loaded_values = None
            self.loaded_signature = None
            self.original_transfer.set("Sin leer")
            self.original_salary.set("Sin leer")
            self.transfer.set("")
            self.salary.set("")
            self.current_values.set("No se pudieron leer los presupuestos.")
            self.status.set("Error: " + str(exc))
            messagebox.showerror("Lectura fallida", str(exc))
        finally:
            self.reading = False

    def restore_values(self):
        if self.loaded_values is None or self.loaded_save != self.save.get().strip():
            messagebox.showinfo("Sin lectura", "Primero selecciona una partida y pulsa LEER PRESUPUESTOS DE LA PARTIDA.")
            return
        transfer, salary = self.loaded_values
        self.salary_mode.set("base")
        self.transfer.set(str(transfer))
        self.salary.set(str(salary))
        self.status.set("Valores originales restaurados en los campos. No se ha modificado ningún archivo.")

    def pick_save_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta save de PES 2018",
                                         initialdir=str(self.auto_save_dir) if self.auto_save_dir.is_dir() else str(Path.home()))
        if folder:
            self.auto_save_dir = Path(folder)
            self.save_config()
            self.detect()

    def pick_file(self):
        path = filedialog.askopenfilename(title="Selecciona una partida ML00000000 o ML00000001",
                                          initialdir=str(self.auto_save_dir) if self.auto_save_dir.exists() else str(Path.home()))
        if path:
            self.save.set(path)
            self.auto_save_dir = Path(path).parent
            self.detect()

    def pick_tools(self):
        path = filedialog.askdirectory(title="Carpeta de pesXdecrypter")
        if path:
            self.tools.set(path)
            self.save_config()

    def pick_output(self):
        path = filedialog.askdirectory(title="Carpeta de salida")
        if path:
            self.output.set(path)
            self.save_config()

    def open_output(self):
        p = Path(self.output.get())
        if not p.is_dir():
            messagebox.showinfo("Carpeta", "La carpeta aún no existe.")
            return
        if os.name == "nt":
            os.startfile(str(p))
        else:
            messagebox.showinfo("Carpeta de salida", str(p))

    def game_is_running(self):
        """Comprobación preventiva en Windows; no sustituye cerrar el juego."""
        if os.name != "nt":
            return False
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq PES2018.exe", "/FO", "CSV", "/NH"],
                                capture_output=True, text=True, timeout=15,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 0:
            raise RuntimeError("No se pudo comprobar si PES 2018 está abierto. Cierra el juego y reintenta.")
        return any(line.lstrip().lower().startswith('"pes2018.exe"') for line in result.stdout.splitlines())

    def verify_generated(self, outfile, tools, transfer, salary_base):
        """Comprueba los dos campos tras volver a descifrar el archivo generado."""
        with tempfile.TemporaryDirectory(prefix="pes2018_verify_") as td:
            extracted = Path(td) / "data"
            extracted.mkdir()
            run(tools / "decrypter18.exe", outfile, extracted)
            dat = extracted / "data.dat"
            if not dat.is_file() or dat.stat().st_size < SALARY_OFFSET + 4:
                raise RuntimeError("No se pudo verificar el archivo generado.")
            with dat.open("rb") as f:
                f.seek(TRANSFER_OFFSET)
                actual_transfer = struct.unpack("<I", f.read(4))[0] * SCALE
                f.seek(SALARY_OFFSET)
                actual_salary = struct.unpack("<I", f.read(4))[0] * SCALE
            if (actual_transfer, actual_salary) != (transfer, salary_base):
                raise RuntimeError("La verificación del archivo generado no coincide con los importes solicitados.")

    def apply_generated(self, src, outfile, tools, transfer, salary_base):
        """Respalda la partida y reemplaza el archivo solo tras verificarlo."""
        if self.game_is_running():
            raise RuntimeError("PES 2018 está abierto. No se aplicaron cambios.")
        self.verify_generated(outfile, tools, transfer, salary_base)
        if self.loaded_signature != (src.stat().st_size, src.stat().st_mtime_ns):
            raise RuntimeError("La partida cambió mientras se generaba el archivo. No se aplicaron cambios.")
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = src.with_name(f"{src.name}.BACKUP_{stamp}")
        shutil.copy2(src, backup)
        if not backup.is_file() or backup.stat().st_size != src.stat().st_size:
            raise RuntimeError("No se pudo verificar la copia de seguridad. No se aplicaron cambios.")
        temp_target = src.with_name(f"{src.name}.PENDIENTE_{stamp}")
        try:
            shutil.copy2(outfile, temp_target)
            if temp_target.stat().st_size != outfile.stat().st_size:
                raise RuntimeError("La copia temporal no coincide con el archivo generado.")
            if self.game_is_running():
                raise RuntimeError("Se detectó PES 2018 abierto. No se aplicaron cambios.")
            if self.loaded_signature != (src.stat().st_size, src.stat().st_mtime_ns):
                raise RuntimeError("La partida original cambió. No se aplicaron cambios.")
            os.replace(temp_target, src)
        finally:
            if temp_target.exists():
                temp_target.unlink()

    def apply_direct(self):
        self.generate(apply=True)

    def generate(self, apply=False):
        try:
            src = Path(self.save.get().strip())
            tools = Path(self.tools.get().strip())
            outdir = Path(self.output.get().strip())
            if not src.is_file() or not re.fullmatch(r"ML\d{8}", src.name, re.I):
                raise ValueError("Selecciona un archivo de partida válido (por ejemplo ML00000001).")
            if not (tools / "decrypter18.exe").is_file() or not (tools / "encrypter18.exe").is_file():
                raise ValueError("No se encuentran decrypter18.exe y encrypter18.exe.")
            if self.loaded_save != str(src) or self.loaded_values is None:
                raise ValueError("Primero pulsa LEER PRESUPUESTOS DE LA PARTIDA seleccionada.")
            if self.loaded_signature != (src.stat().st_size, src.stat().st_mtime_ns):
                raise ValueError("La partida cambió desde la última lectura. Vuelve a leer los presupuestos.")
            if self.salary_mode.get() == "visible" and src.name.upper() != "ML00000001":
                raise ValueError("La calibración de saldo visible solo se probó en ML00000001.")
            transfer = parse_amount(self.transfer.get())
            salary = parse_amount(self.salary.get())
            salary_base = salary - SALARY_DELTA if self.salary_mode.get() == "visible" else salary
            if salary_base < 0 or salary_base > MAX_AMOUNT or salary_base % SCALE:
                raise ValueError("El salario base calculado no cabe en el campo del juego.")
            if apply and self.game_is_running():
                raise RuntimeError("PES 2018 parece estar abierto. Ciérralo completamente antes de aplicar cambios.")
            outdir.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile = outdir / f"{src.name}_EDITADO_{stamp}"
            if outfile.exists():
                raise ValueError("Ya existe un archivo con ese nombre. Inténtalo de nuevo.")
            self.status.set("Procesando partida... espera.")
            self.update_idletasks()
            with tempfile.TemporaryDirectory(prefix="pes2018_v31_") as td:
                extracted = Path(td) / "data"
                extracted.mkdir()
                run(tools / "decrypter18.exe", src, extracted)
                missing = [name for name in AUX if not (extracted / name).is_file()]
                if missing:
                    raise RuntimeError("Faltan archivos descifrados: " + ", ".join(missing))
                dat = extracted / "data.dat"
                with dat.open("r+b") as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() < SALARY_OFFSET + 4:
                        raise RuntimeError("Formato de data.dat no compatible.")
                    f.seek(TRANSFER_OFFSET)
                    old_transfer = struct.unpack("<I", f.read(4))[0] * SCALE
                    f.seek(SALARY_OFFSET)
                    old_salary = struct.unpack("<I", f.read(4))[0] * SCALE
                    if not messagebox.askyesno("Confirmar edición",
                        f"Partida: {src.name}\n\n"
                        f"Fichajes base: ${old_transfer:,} → ${transfer:,}\n"
                        f"Salarios base: ${old_salary:,} → ${salary_base:,}\n\n"
                        + ("Se generará y aplicará al archivo original, con copia de seguridad. ¿Continuar?"
                         if apply else "Se generará una copia independiente. ¿Continuar?")):
                        self.status.set("Operación cancelada.")
                        return
                    f.seek(TRANSFER_OFFSET)
                    f.write(struct.pack("<I", transfer // SCALE))
                    f.seek(SALARY_OFFSET)
                    f.write(struct.pack("<I", salary_base // SCALE))
                run(tools / "encrypter18.exe", extracted, outfile)
                if not outfile.is_file() or outfile.stat().st_size < 1000:
                    raise RuntimeError("El archivo cifrado no se generó correctamente.")
            if apply:
                self.apply_generated(src, outfile, tools, transfer, salary_base)
                self.loaded_signature = None  # Obliga a volver a leer tras reemplazar.
                self.loaded_values = None
                self.status.set(f"Cambios aplicados a {src.name}. Copia adicional: {outfile}")
                messagebox.showinfo("Cambios aplicados",
                    f"Se actualizó {src.name} con respaldo previo.\n\n"
                    f"La copia generada también está en:\n{outfile}\n\n"
                    "Vuelve a leer los presupuestos antes de realizar otra edición.")
                self.save_config()
                return
            self.save_config()
            self.status.set(f"Partida generada: {outfile}")
            messagebox.showinfo("Partida generada",
                f"Se creó:\n{outfile}\n\n"
                "Para probarla: cierra PES 2018, respalda tu partida y copia el archivo\n"
                f"al directorio save con el nombre {src.name}.\n\n"
                "La partida original no se ha modificado.")
        except Exception as exc:
            self.status.set("Error: " + str(exc))
            messagebox.showerror("No se pudo generar", str(exc))

if __name__ == "__main__":
    App().mainloop()
