import json
import os
import urllib.request
import urllib.error
from flask import Flask, request, jsonify

# --- CONFIGURAÇÃO DO EVOTALKS ---
# A chave API e o Queue ID serão lidos das variáveis de ambiente na Vercel
EVOTALKS_API_KEY = os.environ.get("EVOTALKS_API_KEY")
EVOTALKS_QUEUE_ID = os.environ.get("EVOTALKS_QUEUE_ID")
EVOTALKS_INSTANCE_DOMAIN = os.environ.get("EVOTALKS_INSTANCE_DOMAIN", "ergonaturais.evotalks.com.br")
TEMPLATE_ID = os.environ.get("EVOTALKS_TEMPLATE_ID", "4")

# Endpoint validado pelo usuário: /int/enqueueMessageToSend
EVOTALKS_ENDPOINT = f"https://{EVOTALKS_INSTANCE_DOMAIN}/int/enqueueMessageToSend"

# Inicializa o aplicativo Flask
app = Flask(__name__)

# A Vercel espera que o arquivo exporte o objeto 'app' ou 'application'
# para que o servidor Gunicorn possa iniciá-lo.

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    try:
        # 1. Ler o payload do CartPanda
        cartpanda_payload = request.get_json(silent=True)
        
        if not cartpanda_payload:
            return jsonify({"status": "error", "message": "Payload vazio ou inválido"}), 400

        print(f"📦 Webhook recebido: {json.dumps(cartpanda_payload, indent=2)}")

        # 2. Validar evento
        if cartpanda_payload.get("event") != "order.paid":
            return jsonify({"message": "Evento ignorado"}), 200

        # 3. Extrair dados do CartPanda
        customer = cartpanda_payload.get("customer", {})
        customer_name = customer.get("name", "Cliente")
        customer_phone = customer.get("phone", "")

        order_data = cartpanda_payload.get("order", {})
        total_price = order_data.get("total", 0.00)
        order_id = order_data.get("order_number", "N/A")

        line_items = order_data.get("line_items", [])
        product_name = line_items[0].get("name", "seu pedido") if line_items else "seu pedido"

        # Validar telefone
        if not customer_phone:
            raise ValueError("Telefone do cliente não encontrado")

        # Formatar telefone (remover caracteres especiais)
        phone_number = ''.join(filter(str.isdigit, customer_phone))
        if not phone_number.startswith('55'):
            phone_number = f"55{phone_number}"

        # 4. Montar payload para EvoTalks
        # Conversão para inteiro (CRUCIAL)
        try:
            queue_id_int = int(EVOTALKS_QUEUE_ID)
        except (TypeError, ValueError):
            # Se a variável de ambiente não estiver configurada, falha com 500
            return jsonify({"status": "error", "message": "Variável de ambiente EVOTALKS_QUEUE_ID não configurada ou inválida (deve ser um número)"}), 500

        evotalks_payload = {
            "apiKey": EVOTALKS_API_KEY,
            "queueId": queue_id_int,
            "number": phone_number,
            "templateId": TEMPLATE_ID
        }

        print(f"📤 Enviando para EvoTalks: {json.dumps(evotalks_payload, indent=2)}")

        # 5. Enviar para EvoTalks
        req = urllib.request.Request(
            EVOTALKS_ENDPOINT,
            data=json.dumps(evotalks_payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            evotalks_response = json.loads(response.read().decode('utf-8'))
            print(f"✅ Sucesso: {json.dumps(evotalks_response, indent=2)}")

            # 6. Retornar sucesso
            return jsonify({
                "status": "success",
                "message": "Mensagem enviada com sucesso",
                "sentTo": phone_number,
                "evotalks_response": evotalks_response
            }), 200

    except urllib.error.HTTPError as e:
        # Captura erros HTTP da EvoTalks (como o 403)
        error_body = e.read().decode('utf-8')
        print(f"❌ Erro HTTP {e.code}: {error_body}")
        return jsonify({
            "status": "error",
            "message": f"Erro ao enviar para EvoTalks: {e.code}",
            "details": error_body
        }), 500

    except Exception as e:
        # Captura erros gerais (como telefone não encontrado, etc.)
        print(f"❌ Erro geral: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# O Vercel usa o objeto 'app' para iniciar o servidor.
application = app
