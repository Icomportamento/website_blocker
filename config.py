import time
import pygetwindow as gw
import pyautogui
import subprocess
import os

# --- OFFSETS (COORDENADAS RELATIVAS À JANELA DO CHROME) ---
CLICK1_OFFSET = (1819, 67)
CLICK2_OFFSET = (1635, 221)
CLICK3_OFFSET = (1692, 173)
CLICK4_OFFSET = (1223, 161)

# Clique final → abre janela de upload
CLICK_FINAL_OFFSET = (1073, 783)

CLICK_EXTRA1_OFFSET = (904, 781)
CLICK_EXTRA2_OFFSET = (1218, 649)
# Clique após upload
CLICK_AFTER_UPLOAD_OFFSET = (1006, 1017)


def abrir_novo_chrome():
    """Abre uma nova janela do Google Chrome."""
    print("Abrindo nova janela do Chrome...")

    # Caminho padrão do Chrome (Windows)
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    # Abre Chrome limpo
    subprocess.Popen([chrome_path])

    # Espera carregar
    time.sleep(5)

    # Procura a janela nova
    for _ in range(20):  # tenta por até 10 segundos
        for w in gw.getWindowsWithTitle("Google Chrome"):
            try:
                w.restore()
                w.activate()
                w.maximize()
                time.sleep(1)
                return w
            except:
                pass
        time.sleep(0.5)

    print("ERRO: Chrome não foi encontrado após abrir!")
    return None


def click_in_window(window, offset):
    """Clica em coordenadas relativas à janela ativa."""
    x_abs = window.left + offset[0]
    y_abs = window.top + offset[1]
    pyautogui.moveTo(x_abs, y_abs, duration=0.2)
    pyautogui.click()


def run_sequence():
    """Executa toda a automação, incluindo upload do options.txt."""
    win = abrir_novo_chrome()
    if not win:
        return

    print("Chrome ativado!")
    time.sleep(1)

    # -------------------------
    # 1. Cliques iniciais
    # -------------------------
    click_in_window(win, CLICK1_OFFSET); time.sleep(1)
    click_in_window(win, CLICK2_OFFSET); time.sleep(1)
    click_in_window(win, CLICK3_OFFSET); time.sleep(1)
    click_in_window(win, CLICK4_OFFSET); time.sleep(1)

    # -------------------------
    # 2. Scroll da página
    # -------------------------
    for _ in range(20):
        pyautogui.scroll(-200)
        time.sleep(0.05)

    # -------------------------
    # 3. Novos cliques ANTES do final
    # -------------------------

    # -------------------------
    # 4. Clique final → abre upload
    # -------------------------
    click_in_window(win, CLICK_FINAL_OFFSET)
    time.sleep(1)

    # -------------------------
    # 5. Upload do arquivo options.txt
    # -------------------------
    usuario = os.getlogin()
    options_path = fr"C:\Users\{usuario}\Desktop\options.txt"

    print(f"Enviando arquivo: {options_path}")

    pyautogui.write(options_path, interval=0.01)
    pyautogui.press("enter")
    time.sleep(2)

    click_in_window(win, CLICK_EXTRA1_OFFSET); time.sleep(1)
    click_in_window(win, CLICK_EXTRA2_OFFSET); time.sleep(1)

    # -------------------------
    # 6. Clique após o upload
    # -------------------------
    click_in_window(win, CLICK_AFTER_UPLOAD_OFFSET)
    time.sleep(1)

    print("Processo completo!")


if __name__ == "__main__":
    run_sequence()
