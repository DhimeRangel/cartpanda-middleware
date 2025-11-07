import json
import os
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error

# --- CONFIGURAÇÃO DO EVOTALKS ---
# A chave API e o Queue ID serão lidos das variáveis de ambiente na Vercel
EVOTALKS_API_KEY = os.environ.get("EVOTALKS_API_KEY", "SUA_API_KEY")
EVOTALKS_QUEUE_ID = os.environ.get("EVOTALKS_QUEUE_ID", "SEU_QUEUE_ID")
EVOTALKS_INSTANCE_DOMAIN = os.environ.get("EVOTALKS_INSTANCE_DOMAIN", "ergonaturais.evotalks.com.br") # Ex: ergonaturais.evotalks.com.br

# Endpoint validado pelo usuário: /int/enqueueMessageToSend
EVOTALKS_ENDPOINT = f"https://{EVOTALKS_INSTANCE_DOMAIN}/int/enqueueMessageToSend"

# O templateId deve ser configurado no painel da EvoTalks para a mensagem de confirmação de pedido.
# O usuário validou o templateId "3" em seus testes.
TEMPLATE_ID = os.environ.get("EVOTALKS_TEMPLATE_ID", "3")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Ler o payload do CartPanda
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            cartpanda_payload = json.loads(post_data.decode('utf-8'))

            print(f"📦 Webhook recebido: {json.dumps(cartpanda_payload, indent=2)}")

            # 2. Validar evento
            if cartpanda_payload.get("event") != "order.paid":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Evento ignorado"}).encode())
                return

            # 3. Extrair dados do CartPanda
            customer = cartpanda_payload.get("customer", {})
            customer_name = customer.get("name", "Cliente")
            customer_phone = customer.get("phone", "")

            order_data = cartpanda_payload.get("order", {})
            total_price = order_data.get("total", 0.00)
            order_id = order_data.get("order_number", "N/A") # Usando order_number para o ID do pedido

            line_items = order_data.get("line_items", []) # Ajustado para line_items, conforme payload real
            # Pega o nome do primeiro item
            product_name = line_items[0].get("name", "seu pedido") if line_items else "seu pedido"

            # Validar telefone
            if not customer_phone:
                raise ValueError("Telefone do cliente não encontrado")

            # Formatar telefone (remover caracteres especiais)
            phone_number = ''.join(filter(str.isdigit, customer_phone))
            # O payload real já veio com +55, mas a validação garante o formato E.164 (55XX...)
            if not phone_number.startswith('55'):
                phone_number = f"55{phone_number}"

            # Formatar valor (não é mais necessário para o template, mas mantido para referência)
            # total_formatted = f"{total_price:.2f}".replace('.', ',')

            # 4. Montar payload para EvoTalks (Formato validado pelo usuário)
            # Este formato usa o templateId e envia os dados como variáveis do template.
            # O template deve ser configurado no painel da EvoTalks para usar as variáveis:
            # - {{1}} para o nome do cliente
            # - {{2}} para o nome do produto
            # - {{3}} para o valor total
            # - {{4}} para o ID do pedido
            
            # **ATENÇÃO:** Como o endpoint validado usa `templateId`, o corpo da mensagem
            # não é enviado diretamente. O template deve ser configurado no painel da EvoTalks.
            # O payload deve conter as variáveis que o template espera.
            
            # Como o teste do usuário usou apenas templateId, vou assumir que o template
            # já contém a mensagem completa e que as variáveis não são estritamente necessárias
            # no payload, a menos que o template as exija.
            # No entanto, para o caso de templates que exigem variáveis, o formato seria:
            
            # evotalks_payload = {
            #     "apiKey": EVOTALKS_API_KEY,
            #     "queueId": EVOTALKS_QUEUE_ID,
            #     "number": phone_number,
            #     "templateId": TEMPLATE_ID,
            #     "variables": [
            #         {"key": "nome_cliente", "value": customer_name},
            #         {"key": "nome_produto", "value": product_name},
            #         {"key": "valor_total", "value": f"{total_price:.2f}"},
            #         {"key": "id_pedido", "value": order_id}
            #     ]
            # }
            
            # **VERSÃO MAIS SIMPLES (baseada nos testes do usuário):**
            # O usuário não enviou variáveis nos testes, apenas templateId.
            # Vou usar a estrutura mais simples que funcionou, mas com as variáveis de ambiente.
            
            evotalks_payload = {
                "apiKey": EVOTALKS_API_KEY,
                "queueId": EVOTALKS_QUEUE_ID,
                "number": phone_number,
                "templateId": TEMPLATE_ID
            }
            
            # **NOTA:** Se o template precisar de variáveis, o usuário precisará descomentar
            # a versão mais complexa acima e configurar as variáveis no painel da EvoTalks.

            print(f"📤 Enviando para EvoTalks: {json.dumps(evotalks_payload, indent=2)}")

            # 5. Enviar para EvoTalks (com autenticação no BODY)
            # O endpoint /int/enqueueMessageToSend usa a apiKey no body, conforme validado.
            req = urllib.request.Request(
                EVOTALKS_ENDPOINT,
                data=json.dumps(evotalks_payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json'
                }
            )

            with urllib.request.urlopen(req) as response:
                evotalks_response = json.loads(response.read().decode('utf-8'))
                print(f"✅ Sucesso: {json.dumps(evotalks_response, indent=2)}")

                # 6. Retornar sucesso
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Mensagem enviada com sucesso",
                    "sentTo": phone_number,
                    "evotalks_response": evotalks_response
                }).encode())

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ Erro HTTP {e.code}: {error_body}")

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Erro ao enviar para EvoTalks: {e.code}",
                "details": error_body
            }).encode())

        except Exception as e:
            print(f"❌ Erro geral: {str(e)}")

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode())
