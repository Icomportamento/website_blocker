import sys

def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)

import tkinter as tk
from tkinter import messagebox
import subprocess
import os


# Paths to your .bat files (update these paths as needed)
BAT_FILE_ATIVAR = resource_path('ativar_bloqueio.bat')
BAT_FILE_DESATIVAR = resource_path('desativar_bloqueio.bat')
BAT_FILE_BLOQUEAR_USB = resource_path('bloquear_usb.bat')
BAT_FILE_DESBLOQUEAR_USB = resource_path('desbloquear_usb.bat')


# State variable to track if bloqueio is active
is_bloqueio_ativo = False

def update_circle():
    color = "green" if is_bloqueio_ativo else "red"
    canvas.itemconfig(circle, fill=color)

def run_bat_file(bat_path, ativar_bloqueio=None):
    global is_bloqueio_ativo
    try:
        # Use 'start' to run the batch file in a new console window
        subprocess.Popen(f'start "" "{bat_path}"', shell=True)
        # If ativar_bloqueio is True, copy whitelist.txt to Desktop
        if ativar_bloqueio:
            src = resource_path('whitelist.txt')
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            dst = os.path.join(desktop_path, 'whitelist.txt')
            try:
                with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                    fdst.write(fsrc.read())
            except Exception as copy_err:
                messagebox.showerror("Erro", f"Erro ao copiar whitelist.txt para a área de trabalho:\n{copy_err}")
        if ativar_bloqueio is not None:
            is_bloqueio_ativo = ativar_bloqueio
            update_circle()
        messagebox.showinfo("Sucesso", f"Arquivo {os.path.basename(bat_path)} foi iniciado em uma nova janela.")
    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Erro ao tentar executar {os.path.basename(bat_path)} em nova janela:\n{e}"
        )

root = tk.Tk()
root.title("Bloqueador GUI")
root.geometry("300x300")

# Canvas for status circle
canvas = tk.Canvas(root, width=50, height=50, highlightthickness=0)
canvas.pack(pady=10)
circle = canvas.create_oval(10, 10, 40, 40, fill="red", outline="black")

btn_ativar = tk.Button(root, text="Ativar Bloqueio", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_ATIVAR, ativar_bloqueio=True))
btn_ativar.pack(pady=10)

btn_desativar = tk.Button(root, text="Desativar Bloqueio", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_DESATIVAR, ativar_bloqueio=False))
btn_desativar.pack(pady=5)

btn_bloquear_usb = tk.Button(root, text="Bloquear Portas USB", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_BLOQUEAR_USB))
btn_bloquear_usb.pack(pady=10)

btn_desbloquear_usb = tk.Button(root, text="Desbloquear Portas USB", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_DESBLOQUEAR_USB))
btn_desbloquear_usb.pack(pady=5)

update_circle()

root.mainloop()
