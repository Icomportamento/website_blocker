# ------------------- IMPORTS -------------------
import sys
import os
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import importlib
import importlib.util
import runpy
from db import get_conn

# ------------------- UTILITY FUNCTIONS -------------------
def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# ------------------- MAIN APP -------------------
def main():
    # State variable to track if bloqueio is active
    global is_bloqueio_ativo, canvas, circle
    is_bloqueio_ativo = False

    def update_circle():
        color = "green" if is_bloqueio_ativo else "red"
        canvas.itemconfig(circle, fill=color)

    def run_bat_file(bat_path, ativar_bloqueio=None):
        global is_bloqueio_ativo
        try:
            # Run the batch file without opening a command prompt window
            subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            # If ativar_bloqueio is True, copy whitelist.txt to Desktop
            if ativar_bloqueio:
                src = resource_path('options.txt')
                desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                dst = os.path.join(desktop_path, 'options.txt')
                try:
                    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                        fdst.write(fsrc.read())
                except Exception as copy_err:
                    messagebox.showerror("Erro", f"Erro ao copiar options.txt para a área de trabalho:\n{copy_err}")
            if ativar_bloqueio is not None:
                is_bloqueio_ativo = ativar_bloqueio
                update_circle()
            messagebox.showinfo("Sucesso", f"Arquivo {os.path.basename(bat_path)} foi iniciado em segundo plano.")
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao tentar executar {os.path.basename(bat_path)} em segundo plano:\n{e}"
            )

    def run_config_module():
        """Try to import and run the `config` module in a background thread.

        This prefers a callable `main()` or `run()` inside `config.py`. Running
        in a separate thread avoids blocking the Tkinter mainloop.
        """
        def _runner():
            try:
                # import or reload the module so changes are picked up during dev
                if 'config' in sys.modules:
                    mod = importlib.reload(sys.modules['config'])
                else:
                    mod = importlib.import_module('config')

                # prefer common entrypoints
                if hasattr(mod, 'main') and callable(mod.main):
                    mod.main()
                elif hasattr(mod, 'run') and callable(mod.run):
                    mod.run()
                elif hasattr(mod, 'run_sequence') and callable(mod.run_sequence):
                    mod.run_sequence()
                else:
                    # fallback: execute module as script so __main__ code runs
                    try:
                        runpy.run_module('config', run_name='__main__')
                    except Exception:
                        try:
                            messagebox.showinfo('Config', 'Módulo `config` importado, porém não contém um entrypoint executável (main/run/run_sequence).')
                        except Exception:
                            pass

            except Exception as ex:
                try:
                    messagebox.showerror('Erro ao executar config', str(ex))
                except Exception:
                    pass

        threading.Thread(target=_runner, daemon=True).start()

    BAT_FILE_ATIVAR = resource_path('ativar_bloqueio.bat')
    BAT_FILE_DESATIVAR = resource_path('desativar_bloqueio.bat')
    BAT_FILE_BLOQUEAR_USB = resource_path('bloquear_usb.bat')
    BAT_FILE_DESBLOQUEAR_USB = resource_path('desbloquear_usb.bat')

    # Main window
    global root
    root = tk.Tk()
    root.title("SmartSecurity")
    center_window(root, 300, 300)
    # Require DB login at startup (handled below) — no fixed startup password

    # Per-session auth state (in-memory only, no persistence)
    auth_state = {
        'authenticated': False,
        'user_id': None,
        'username': None,
        'empresa_id': None,
        'empresa_unico': None,
    }

    def perform_login(nome, senha):
        """Authenticate against DB. Returns (user_id, empresa_id, empresa_unico) or None."""
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id_usuario, id_empresa, password_hash, role FROM usuario WHERE username=%s", (nome,))
            user_row = cur.fetchone()
            if not user_row:
                cur.close()
                conn.close()
                return None
            from werkzeug.security import check_password_hash
            if user_row[2] and check_password_hash(user_row[2], senha):
                # fetch empresa unique code
                cur.execute("SELECT id_unico FROM empresa WHERE id_empresa=%s", (user_row[1],))
                row2 = cur.fetchone()
                empresa_unico = row2[0] if row2 and row2[0] is not None else None
                uid = user_row[0]
                emp_id = user_row[1]
                cur.close()
                conn.close()
                return (uid, emp_id, empresa_unico)
            cur.close()
            conn.close()
            return None
        except Exception:
            return None

    def initial_login_prompt():
        """Show a modal login at app start. If login fails or canceled, close app."""
        login_win = tk.Toplevel(root)
        login_win.title("Conectar à base de dados")
        center_window(login_win, 340, 170)
        login_win.transient(root)
        login_win.grab_set()

        tk.Label(login_win, text="Nome da empresa:").pack(pady=(10, 0))
        empresa_var = tk.StringVar()
        tk.Entry(login_win, textvariable=empresa_var).pack(pady=5)

        tk.Label(login_win, text="Senha:").pack(pady=(4,0))
        senha_var = tk.StringVar()
        tk.Entry(login_win, textvariable=senha_var, show="*").pack(pady=5)

        def on_login_start():
            nome = empresa_var.get().strip()
            senha = senha_var.get().strip()
            if not nome or not senha:
                messagebox.showwarning("Atenção", "Preencha os campos nome da empresa e senha.")
                return
            res = perform_login(nome, senha)
            if not res:
                messagebox.showerror("Falha", "Credenciais inválidas.")
                return
            uid, emp_id, emp_unico = res
            auth_state['authenticated'] = True
            auth_state['user_id'] = uid
            auth_state['username'] = nome
            auth_state['empresa_id'] = emp_id
            auth_state['empresa_unico'] = emp_unico
            login_win.destroy()

        def on_cancel():
            login_win.destroy()
            root.destroy()

        tk.Button(login_win, text='Conectar', command=on_login_start).pack(pady=8)
        tk.Button(login_win, text='Cancelar', command=on_cancel).pack()
        root.wait_window(login_win)

    # Require login at startup (modal) — must succeed to continue
    initial_login_prompt()
    if not auth_state['authenticated']:
        return

    # Canvas for status circle
    canvas = tk.Canvas(root, width=50, height=50, highlightthickness=0)
    canvas.pack(pady=10)
    circle = canvas.create_oval(10, 10, 40, 40, fill="red", outline="black")

    btn_ativar = tk.Button(root, text="Ativar Bloqueio de Websites", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_ATIVAR, ativar_bloqueio=True))
    btn_ativar.pack(pady=10)

    btn_desativar = tk.Button(root, text="Desativar Bloqueio de Websites", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_DESATIVAR, ativar_bloqueio=False))
    btn_desativar.pack(pady=5)

    btn_bloquear_usb = tk.Button(root, text="Bloquear Portas USB", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_BLOQUEAR_USB))
    btn_bloquear_usb.pack(pady=10)

    btn_desbloquear_usb = tk.Button(root, text="Desbloquear Portas USB", font=("Arial", 12), width=25, command=lambda: run_bat_file(BAT_FILE_DESBLOQUEAR_USB))
    btn_desbloquear_usb.pack(pady=5)

    # Button to connect to DB (restored near other action buttons)

    # Button to run config.py (non-blocking)
    # Check for optional automation dependencies first to avoid ImportError
    def show_install_instructions():
        msg = (
            "O módulo 'pygetwindow' e/ou 'pyautogui' não estão instalados.\n"
            "Instale-os no ambiente Python usado para rodar este app:\n\n"
            "pip install pygetwindow pyautogui\n\n"
            "Depois reinicie o aplicativo.")
        messagebox.showwarning("Dependências ausentes", msg)

    spec_gw = importlib.util.find_spec('pygetwindow')
    spec_pa = importlib.util.find_spec('pyautogui')
    if spec_gw is None or spec_pa is None:
        btn_run_config = tk.Button(root, text="Executar Config (dependências faltando)", font=("Arial", 12), width=25, command=show_install_instructions, state='normal')
        btn_run_config.pack(pady=8)
    else:
        btn_run_config = tk.Button(root, text="Executar Config", font=("Arial", 12), width=25, command=run_config_module)
        btn_run_config.pack(pady=8)

    # Database connection / choose whitelist flow
    def db_connect_flow():
        def setor_selection_flow(empresa_id, empresa_unico):
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id_setor, nome_setor, id_unico FROM setor ORDER BY nome_setor")
                setores = cur.fetchall()
                cur.close()
                conn.close()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar setores: {e}")
                return

            if not setores:
                messagebox.showinfo("Vazio", "Nenhum setor encontrado na base de dados.")
                return

            setor_win = tk.Toplevel(root)
            setor_win.title("Escolher setor")
            center_window(setor_win, 360, 300)
            setor_win.transient(root)
            setor_win.grab_set()

            tk.Label(setor_win, text="Selecione um setor:").pack(pady=8)
            lb = tk.Listbox(setor_win, width=50, height=8)
            for s in setores:
                lb.insert(tk.END, f"{s[0]} - {s[1]} (code: {s[2]})")
            lb.pack(padx=10)

            def on_choose_setor():
                sel = lb.curselection()
                if not sel:
                    messagebox.showwarning("Atenção", "Selecione um setor.")
                    return
                index = sel[0]
                id_setor, nome_setor, setor_unico = setores[index]
                setor_win.destroy()

                # Step 3 - list whitelists for setor
                try:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("SELECT id_link, nome_link, txt_path, id_unico FROM link WHERE id_setor=%s ORDER BY id_link", (id_setor,))
                    links = cur.fetchall()
                    cur.close()
                    conn.close()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao carregar whitelists: {e}")
                    return

                if not links:
                    messagebox.showinfo("Vazio", "Nenhuma whitelist encontrada para este setor.")
                    return

                links_win = tk.Toplevel(root)
                links_win.title("Escolher whitelist")
                center_window(links_win, 420, 320)
                links_win.transient(root)
                links_win.grab_set()

                tk.Label(links_win, text=f"Whitelists em: {nome_setor}").pack(pady=8)
                lb2 = tk.Listbox(links_win, width=70, height=10)
                for lk in links:
                    lb2.insert(tk.END, f"{lk[0]} - {lk[1]} -> {lk[2]} (code: {lk[3]})")
                lb2.pack(padx=10)

                def on_choose_link():
                    sel = lb2.curselection()
                    if not sel:
                        messagebox.showwarning("Atenção", "Selecione uma whitelist.")
                        return
                    idx = sel[0]
                    id_link, nome_link, txt_path, link_unico = links[idx]
                    links_win.destroy()

                    # Step 4 - update options.txt line
                    try:
                        opts_path = resource_path('options.txt')
                        with open(opts_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        new_lines = []
                        replaced = False
                        for line in lines:
                            if line.strip().startswith('sitesURL1='):
                                new_val = txt_path.replace('\\', '/')
                                new_lines.append(f"sitesURL1={new_val}\n")
                                replaced = True
                            else:
                                new_lines.append(line)

                        if not replaced:
                            new_lines.append(f"sitesURL1={txt_path}\n")

                        with open(opts_path, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)

                        messagebox.showinfo("Sucesso", f"options.txt atualizado com: {txt_path}")
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao atualizar options.txt: {e}")

                btn_select_link = tk.Button(links_win, text='Selecionar', command=on_choose_link)
                btn_select_link.pack(pady=10)

            btn_choose_setor = tk.Button(setor_win, text='Selecionar setor', command=on_choose_setor)
            btn_choose_setor.pack(pady=8)

        # If we're already authenticated at app-level, skip login and go to setor selection
        if auth_state.get('authenticated'):
            setor_selection_flow(auth_state.get('empresa_id'), auth_state.get('empresa_unico'))
            return

        # Not authenticated yet: show login modal then proceed to setor_selection_flow on success
        login_win = tk.Toplevel(root)
        login_win.title("Conectar à base de dados")
        center_window(login_win, 340, 170)
        login_win.transient(root)
        login_win.grab_set()

        tk.Label(login_win, text="Nome da empresa:").pack(pady=(10, 0))
        empresa_var = tk.StringVar()
        tk.Entry(login_win, textvariable=empresa_var).pack(pady=5)

        tk.Label(login_win, text="Senha:").pack(pady=(4,0))
        senha_var = tk.StringVar()
        tk.Entry(login_win, textvariable=senha_var, show="*").pack(pady=5)

        def on_login():
            nome = empresa_var.get().strip()
            senha = senha_var.get().strip()
            if not nome or not senha:
                messagebox.showwarning("Atenção", "Preencha os campos nome da empresa e senha.")
                return

            res = perform_login(nome, senha)
            if not res:
                messagebox.showerror("Falha", "Credenciais inválidas.")
                return

            uid, empresa_id, empresa_unico = res
            # store session-only auth state so later presses skip the login step
            auth_state['authenticated'] = True
            auth_state['user_id'] = uid
            auth_state['username'] = nome
            auth_state['empresa_id'] = empresa_id
            auth_state['empresa_unico'] = empresa_unico
            login_win.destroy()

            setor_selection_flow(empresa_id, empresa_unico)

        tk.Button(login_win, text='Conectar', command=on_login).pack(pady=8)

    btn_db_connect = tk.Button(root, text="Conectar à base de dados", font=("Arial", 10), width=25, command=db_connect_flow)
    btn_db_connect.pack(pady=8)

    update_circle()
    root.mainloop()

# ------------------- ENTRY POINT -------------------
if __name__ == "__main__":
    main()

