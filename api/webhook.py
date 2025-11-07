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


# A Vercel espera uma função chamada 'handler' (ou 'vercel_handler' em alguns casos)
# que recebe 'request' e 'response' ou 'event' e 'context'.
# O código original usava BaseHTTPRequestHandler, que é para um servidor local, não para Vercel.
# Para Vercel, precisamos de uma função simples que receba o request.

def handler(request, response):
    try:
        # 1. Ler o payload do CartPanda
        # Na Vercel, o payload POST vem no corpo da requisição.
        # Como o código original usava BaseHTTPRequestHandler, a leitura do corpo
        # precisa ser adaptada para o ambiente Vercel.
        # No entanto, como o código original não está usando um framework como Flask ou FastAPI,
        # e está usando a classe `handler(BaseHTTPRequestHandler)`, a Vercel pode estar
        # tentando emular o ambiente, mas falhando.

        # A solução mais robusta é usar um framework simples como Flask ou FastAPI,
        # mas para manter a simplicidade e a estrutura do código original,
        # vamos tentar a abordagem mais simples que a Vercel costuma suportar
        # para funções Python puras, que é a função `handler(event, context)`.
        # No entanto, o código original está estritamente acoplado a `BaseHTTPRequestHandler`.

        # **CORREÇÃO CRÍTICA:**
        # O erro 404 é de ROTEAMENTO. O código Python não está sendo executado.
        # O erro de `BaseHTTPRequestHandler` só ocorreria se o código fosse executado.
        # A Vercel, ao usar `@vercel/python`, espera que o arquivo `api/webhook.py`
        # exporte uma função chamada `handler` (ou `vercel_handler`).
        # O código original define uma CLASSE chamada `handler`, o que é INCORRETO para a Vercel.

        # Para corrigir o erro de roteamento (404), o `vercel.json` deve ser corrigido.
        # Para corrigir o erro de execução (se o 404 for resolvido), o código Python deve ser adaptado.

        # **Adaptando o código para Vercel (sem BaseHTTPRequestHandler):**
        # A Vercel passa o corpo da requisição no `event` (que é um dicionário).
        # Como o código original é complexo, a melhor abordagem é usar um framework.
        # No entanto, se o usuário quer manter o código simples, vamos tentar a adaptação.

        # **Revertendo para a estrutura original, mas corrigindo o `vercel.json`:**
        # O código original está correto para um servidor HTTP, mas não para o Vercel Serverless Function padrão.
        # O erro 404 é o mais urgente.

        # **Voltando ao plano:** O erro 404 é de roteamento. O código Python não está sendo executado.
        # O erro de `BaseHTTPRequestHandler` só ocorreria se o código fosse executado.
        # A Vercel, ao usar `@vercel/python`, espera que o arquivo `api/webhook.py`
        # exporte uma função chamada `handler` (ou `vercel_handler`).
        # O código original define uma CLASSE chamada `handler`, o que é INCORRETO para a Vercel.

        # **A solução mais simples e direta é usar a função `handler(request, response)` e adaptar o código.**
        # Como o código original é complexo, a melhor abordagem é usar um framework.
        # Mas, para manter a simplicidade, vamos adaptar a lógica para a função `handler(event, context)`
        # que é o padrão para AWS Lambda/Vercel.

        # **Vou reescrever o código para usar o padrão Vercel/Lambda.**

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "OK"})
        }

    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)})
        }

# **O código completo reescrito será fornecido na fase 3.**
# Por enquanto, vou apenas criar o arquivo para a próxima fase.
# O código original será usado como base para a reescrita.

# **O erro de `BaseHTTPRequestHandler` é o segundo problema. O primeiro é o 404.**
# O 404 é resolvido com o `vercel.json` que criei.
# O segundo problema é que o código Python não é compatível com o ambiente Vercel.

# **Vou reescrever o código para ser compatível com Vercel (padrão Lambda/Serverless Function).**

def handler(event, context):
    try:
        # 1. Ler o payload do CartPanda
        # O corpo da requisição está em 'body' e precisa ser decodificado se for base64
        body = event.get('body')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        cartpanda_payload = json.loads(body)

        print(f"📦 Webhook recebido: {json.dumps(cartpanda_payload, indent=2)}")

        # 2. Validar evento
        if cartpanda_payload.get("event") != "order.paid":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Evento ignorado"})
            }

        # 3. Extrair dados do CartPanda
        customer = cartpanda_payload.get("customer", {})
        customer_name = customer.get("name", "Cliente")
        customer_phone = customer.get("phone", "")

        order_data = cartpanda_payload.get("order", {})
        total_price = order_data.get("total", 0.00)
        order_id = order_data.get("order_number", "N/A") # Usando order_number para o ID do pedido

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
        evotalks_payload = {
            "apiKey": EVOTALKS_API_KEY,
            "queueId": EVOTALKS_QUEUE_ID,
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

        with urllib.request.urlopen(req) as response:
            evotalks_response = json.loads(response.read().decode('utf-8'))
            print(f"✅ Sucesso: {json.dumps(evotalks_response, indent=2)}")

            # 6. Retornar sucesso
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
        print(f"❌ Erro geral: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }

# O código original será usado como base para a reescrita.
# O código reescrito está no arquivo /home/ubuntu/webhook.py
# O usuário precisará colocar este código dentro de `api/webhook.py` no seu repositório.
# O arquivo `vercel.json` que criei deve estar na raiz do repositório.
