import requests
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import ttkbootstrap as ttkb
import webbrowser
import threading
import os
import sys
import json
import subprocess
from packaging.version import parse as parse_version

try:
    from core_components import get_application_path
except (ImportError, ModuleNotFoundError):
    def get_application_path():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

# --- Constantes ---
GITHUB_API_URL = "https://api.github.com/repos/PauloBennertz/MonitorCriptomoedas3.2/releases/latest"
CONFIG_FILE_NAME = "config.json"
UPDATER_SCRIPT_NAME = "updater.bat"
DOWNLOADED_FILE_NAME = "update.exe"

# --- UI Classes ---
class UpdateNotificationWindow(tk.Toplevel):
    # ... (código existente, sem alterações) ...
    """ Janela que notifica o usuário sobre uma nova atualização. """
    def __init__(self, parent, version, notes, assets):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.notes = notes
        self.assets = assets
        self.result = "later"
        self.title("Nova Versão Disponível!")
        self.geometry("600x550")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.create_widgets()
        self.center_on_parent()

    def create_widgets(self):
        main_frame = ttkb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        ttkb.Label(main_frame, text=f"🎉 Atualização para a v{self.version}", font=("Segoe UI", 16, "bold"), bootstyle="info").pack(anchor="w")
        ttkb.Label(main_frame, text="Novidades da versão:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(15, 5))

        notes_frame = ttkb.Frame(main_frame, bootstyle="secondary", padding=2)
        notes_frame.pack(fill="both", expand=True)
        text_widget = scrolledtext.ScrolledText(notes_frame, wrap="word", relief="flat", font=("Segoe UI", 10))
        text_widget.insert("1.0", self.notes)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)

        button_frame = ttkb.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        ttkb.Button(button_frame, text="🚀 Atualizar Agora", command=self._update_now, bootstyle="success", width=20).pack(side="right", padx=(10, 0))
        ttkb.Button(button_frame, text="🔄 Atualizar ao Reiniciar", command=self._update_on_startup, bootstyle="primary-outline", width=22).pack(side="right", padx=(10, 0))
        ttkb.Button(button_frame, text="Lembrar Depois", command=self._on_closing, bootstyle="secondary", width=18).pack(side="left")

    def _update_now(self): self.result = "now"; self.destroy()
    def _update_on_startup(self): self.result = "startup"; self.destroy()
    def _on_closing(self): self.result = "later"; self.destroy()

    def center_on_parent(self):
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class DownloadProgressWindow(tk.Toplevel):
    """ Janela para mostrar o progresso do download. """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Baixando Atualização...")
        self.geometry("500x200")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None) # Impede o fechamento

        main_frame = ttkb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        self.status_label = ttkb.Label(main_frame, text="Iniciando download...", font=("Segoe UI", 11))
        self.status_label.pack(pady=(10, 5))

        self.progress = ttkb.Progressbar(main_frame, mode='determinate', length=350)
        self.progress.pack(pady=10, fill="x", expand=True)

        self.percent_label = ttkb.Label(main_frame, text="0%", font=("Segoe UI", 10))
        self.percent_label.pack()

        self.center_on_parent()

    def update_progress(self, value, total):
        percent = int((value / total) * 100)
        self.progress['value'] = percent
        self.percent_label.config(text=f"{percent}%")
        self.status_label.config(text=f"Baixando... ({value/1024/1024:.2f} MB / {total/1024/1024:.2f} MB)")

    def center_on_parent(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - self.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

# --- Lógica de Atualização ---

def check_for_updates(root, current_version, on_startup=False, manual_check=False):
    """ Verifica atualizações. Se on_startup for True, força a atualização se a flag estiver ativa. """
    # Lógica para atualização automática na inicialização
    if on_startup and not manual_check:
        config_path = _get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                if config.get('update_on_startup'):
                    print("Flag 'update_on_startup' encontrada. Tentando atualizar...")
                    # Força a atualização sem ser um 'manual_check'
                    threading.Thread(target=_perform_check, args=(root, current_version, True, False), daemon=True).start()
                    return  # Impede a verificação dupla
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erro ao ler o arquivo de configuração durante a verificação de atualização: {e}")

    # Para verificações manuais ou a verificação silenciosa padrão na inicialização
    threading.Thread(target=_perform_check, args=(root, current_version, False, manual_check), daemon=True).start()

def _perform_check(root, current_version, force_update=False, manual_check=False):
    """ Realiza a chamada à API, compara as versões e notifica o usuário conforme necessário. """
    try:
        response = requests.get(GITHUB_API_URL, timeout=15)
        response.raise_for_status()
        latest_release = response.json()
        tag_name = latest_release.get("tag_name", "0.0.0")
        latest_version_str = tag_name.lstrip('v')

        is_newer_version = parse_version(latest_version_str) > parse_version(current_version)

        if force_update or is_newer_version:
            assets = latest_release.get("assets", [])
            release_notes = latest_release.get("body", "Nenhuma nota de versão encontrada.")

            # A notificação só deve aparecer se não for uma atualização forçada (que é silenciosa até o download)
            if not force_update:
                 root.after(0, show_update_notification, root, latest_version_str, release_notes, assets)
            else: # Se for forçada, vai direto para o download
                 root.after(0, download_and_install, root, assets)
                 _set_update_on_startup_flag(False) # Reseta a flag

        elif manual_check:
            # Se a verificação foi manual e não há novas versões, informa o usuário.
            root.after(0, lambda: messagebox.showinfo(
                "Tudo Certo!",
                f"Você já está com a versão mais recente do aplicativo (v{current_version})."
            ))

    except requests.exceptions.RequestException as e:
        # Erros de conexão ou timeout
        error_message = f"Não foi possível verificar as atualizações. Verifique sua conexão com a internet.\n\nDetalhes: {e}"
        print(error_message)
        if manual_check:
            root.after(0, lambda: messagebox.showerror("Erro de Conexão", error_message))
    except Exception as e:
        # Outros erros (ex: parsing do JSON, etc.)
        error_message = f"Ocorreu um erro inesperado ao verificar atualizações: {e}"
        print(error_message)
        if manual_check:
            root.after(0, lambda: messagebox.showerror("Erro de Atualização", error_message))

def show_update_notification(root, version, notes, assets):
    """ Mostra a janela de notificação e processa a escolha do usuário. """
    alert_consolidator = getattr(getattr(root, 'app', None), 'alert_consolidator', None)

    if alert_consolidator:
        alert_consolidator.suppress_alerts = True

    win = UpdateNotificationWindow(root, version, notes, assets)
    root.wait_window(win)

    if alert_consolidator:
        alert_consolidator.suppress_alerts = False

    if win.result == "now":
        download_and_install(root, assets)
    elif win.result == "startup":
        _set_update_on_startup_flag(True)

def _get_config_path():
    return os.path.join(get_application_path(), CONFIG_FILE_NAME)

def _set_update_on_startup_flag(status: bool):
    """ Define a flag no config.json. """
    config_path = _get_config_path()
    try:
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f: config = json.load(f)
        config['update_on_startup'] = status
        with open(config_path, 'w') as f: json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar flag de atualização: {e}")

# --- Lógica de Download e Instalação ---

def download_and_install(root, assets):
    """ Encontra o asset .exe, baixa e inicia o processo de atualização. """
    exe_asset = None
    for asset in assets:
        if asset.get('name', '').lower().endswith('.exe'):
            exe_asset = asset
            break

    if not exe_asset:
        messagebox.showerror("Erro de Atualização", "Nenhum arquivo .exe encontrado na nova versão.")
        return

    download_url = exe_asset.get('browser_download_url')
    if not download_url:
        messagebox.showerror("Erro de Atualização", "URL para download não encontrada.")
        return

    progress_window = DownloadProgressWindow(root)

    def download_thread():
        try:
            download_path = os.path.join(get_application_path(), DOWNLOADED_FILE_NAME)
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0

            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    progress_window.update_progress(bytes_downloaded, total_size)

            progress_window.destroy()
            root.after(0, launch_updater_and_exit, root)

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Erro no Download", f"Falha ao baixar a atualização: {e}")

    threading.Thread(target=download_thread, daemon=True).start()

def create_updater_script():
    """ Cria o script .bat que substituirá o executável. """
    app_path = get_application_path()
    current_exe_path = sys.executable
    current_exe_name = os.path.basename(current_exe_path)
    downloaded_exe_path = os.path.join(app_path, DOWNLOADED_FILE_NAME)
    old_exe_path = os.path.join(app_path, f"{os.path.splitext(current_exe_name)[0]}.old")

    script_content = f"""
@echo off
echo Aguardando o aplicativo fechar...
taskkill /F /PID {os.getpid()} > nul 2>&1
timeout /t 2 /nobreak > nul

echo Substituindo arquivos...
move /Y "{current_exe_path}" "{old_exe_path}"
move /Y "{downloaded_exe_path}" "{current_exe_path}"

echo Limpando...
del "{old_exe_path}" > nul 2>&1

echo Reiniciando o aplicativo...
start "" "{current_exe_path}"

(goto) 2>nul & del "%~f0"
"""
    script_path = os.path.join(app_path, UPDATER_SCRIPT_NAME)
    with open(script_path, 'w') as f:
        f.write(script_content)
    return script_path

def launch_updater_and_exit(root):
    """ Cria e executa o script de atualização, depois fecha a aplicação. """
    messagebox.showinfo("Atualização Concluída", "Download concluido, o programa sera reiniciado.")

    try:
        updater_script_path = create_updater_script()
        # Usar DETACHED_PROCESS para que o script não seja filho do processo principal
        subprocess.Popen([updater_script_path], creationflags=subprocess.DETACHED_PROCESS, shell=True)
        # Força o fechamento da aplicação
        root.destroy()
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Erro Crítico", f"Nao foi possível iniciar o atualizador: {e}")
