import json
import os
import urllib.request
import urllib.error
import base64

# --- CONFIGURAÇÃO DO EVOTALKS ---
# A chave API e o Queue ID serão lidos das variáveis de ambiente na Vercel
EVOTALKS_API_KEY = os.environ.get("EVOTALKS_API_KEY")
EVOTALKS_QUEUE_ID = os.environ.get("EVOTALKS_QUEUE_ID")
EVOTALKS_INSTANCE_DOMAIN = os.environ.get("EVOTALKS_INSTANCE_DOMAIN", "ergonaturais.evotalks.com.br")
TEMPLATE_ID = os.environ.get("EVOTALKS_TEMPLATE_ID", "4")

# Endpoint validado pelo usuário: /int/enqueueMessageToSend
EVOTALKS_ENDPOINT = f"https://{EVOTALKS_INSTANCE_DOMAIN}/int/enqueueMessageToSend"


# Função principal que a Vercel espera para Serverless Functions
def handler(event, context):
    # O Vercel/Lambda passa a requisição no dicionário 'event'
    
    # 1. Validar o método da requisição
    if event.get('httpMethod') != 'POST':
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method Not Allowed. Use POST."})
        }

    try:
        # 2. Ler o payload do CartPanda
        body = event.get('body')
        if not body:
            raise ValueError("Payload vazio")
            
        # Decodificar se for base64 (padrão Vercel/Lambda para POST)
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')
        
        cartpanda_payload = json.loads(body)

        print(f"📦 Webhook recebido: {json.dumps(cartpanda_payload, indent=2)}")

        # 3. Validar evento
        if cartpanda_payload.get("event") != "order.paid":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Evento ignorado"})
            }

        # 4. Extrair dados do CartPanda
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

        # 5. Montar payload para EvoTalks
        # O Queue ID deve ser um inteiro, por isso a conversão
        try:
            queue_id_int = int(EVOTALKS_QUEUE_ID)
        except (TypeError, ValueError):
            raise ValueError("EVOTALKS_QUEUE_ID deve ser um número inteiro válido.")

        evotalks_payload = {
            "apiKey": EVOTALKS_API_KEY,
            "queueId": queue_id_int,
            "number": phone_number,
            "templateId": TEMPLATE_ID
        }

        print(f"📤 Enviando para EvoTalks: {json.dumps(evotalks_payload, indent=2)}")

        # 6. Enviar para EvoTalks
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

            # 7. Retornar sucesso
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "status": "success",
                    "message": "Mensagem enviada com sucesso",
                    "sentTo": phone_number,
                    "evotalks_response": evotalks_response
                })
            }

    except urllib.error.HTTPError as e:
        # Captura erros HTTP da EvoTalks (como o 403)
        error_body = e.read().decode('utf-8')
        print(f"❌ Erro HTTP {e.code}: {error_body}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "message": f"Erro ao enviar para EvoTalks: {e.code}",
                "details": error_body
            })
        }

    except Exception as e:
        # Captura erros gerais (como payload vazio, telefone não encontrado, etc.)
        print(f"❌ Erro geral: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }
