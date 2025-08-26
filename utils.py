import os
import sys

def get_application_path():
    """Retorna o caminho do diretório da aplicação, compatível com PyInstaller."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS  # Modo --onefile
        else:
            return os.path.dirname(sys.executable)  # Modo --onedir
    return os.path.dirname(os.path.abspath(__file__))
