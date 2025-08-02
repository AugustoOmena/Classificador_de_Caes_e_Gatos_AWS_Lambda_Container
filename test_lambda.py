#!/usr/bin/env python3
"""
Script para testar a função Lambda localmente ou na AWS
"""

import json
import base64
import requests
import boto3
from PIL import Image
import io

def image_to_base64(image_path):
    """Converte uma imagem para base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_local_lambda():
    """Testa a função Lambda localmente"""
    print("🧪 Testando função Lambda localmente...")
    
    try:
        # Importar o handler local
        from lambda_app import lambda_handler
        
        # Criar evento de teste (substitua por sua imagem)
        # Você pode usar qualquer imagem de cão ou gato
        test_image_path = "test_cat.jpg"  # Coloque uma imagem de teste
        
        try:
            image_base64 = image_to_base64(test_image_path)
        except FileNotFoundError:
            print(f"❌ Imagem de teste não encontrada: {test_image_path}")
            print("💡 Coloque uma imagem de teste na pasta e atualize o caminho")
            return
        
        # Evento direto (sem API Gateway)
        event = {
            "image": image_base64
        }
        
        # Executar handler
        response = lambda_handler(event, {})
        
        print("✅ Teste local concluído!")
        print(f"📊 Resposta: {json.dumps(response, indent=2, ensure_ascii=False)}")
        
    except ImportError:
        print("❌ Não foi possível importar lambda_app.py")
        print("💡 Certifique-se de que o arquivo está na mesma pasta")
    except Exception as e:
        print(f"❌ Erro no teste local: {e}")

def test_aws_lambda(function_name, region="us-east-1"):
    """Testa a função Lambda na AWS"""
    print(f"☁️ Testando função Lambda na AWS: {function_name}")
    
    try:
        # Cliente Lambda
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Imagem de teste
        test_image_path = "test_cat.jpg"
        
        try:
            image_base64 = image_to_base64(test_image_path)
        except FileNotFoundError:
            print(f"❌ Imagem de teste não encontrada: {test_image_path}")
            return
        
        # Payload
        payload = {
            "image": image_base64
        }
        
        # Invocar função
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )
        
        # Ler resposta
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        print("✅ Teste AWS concluído!")
        print(f"📊 Resposta: {json.dumps(response_payload, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ Erro no teste AWS: {e}")

def test_api_gateway(api_endpoint):
    """Testa via API Gateway"""
    print(f"🌐 Testando via API Gateway: {api_endpoint}")
    
    try:
        # Health check
        health_response = requests.get(f"{api_endpoint}/health")
        print(f"❤️ Health check: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print(f"📊 Health: {health_response.json()}")
        
        # Teste de predição
        test_image_path = "test_cat.jpg"
        
        try:
            image_base64 = image_to_base64(test_image_path)
        except FileNotFoundError:
            print(f"❌ Imagem de teste não encontrada: {test_image_path}")
            return
        
        # Payload
        payload = {
            "image": image_base64
        }
        
        # POST para /predict
        predict_response = requests.post(
            f"{api_endpoint}/predict",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"🔮 Predição: {predict_response.status_code}")
        
        if predict_response.status_code == 200:
            result = predict_response.json()
            print(f"📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Erro: {predict_response.text}")
            
    except Exception as e:
        print(f"❌ Erro no teste API Gateway: {e}")

def create_test_image():
    """Cria uma imagem de teste simples se não existir"""
    try:
        # Tentar abrir imagem existente
        Image.open("test_cat.jpg")
        print("✅ Imagem de teste já existe")
    except FileNotFoundError:
        print("🎨 Criando imagem de teste simples...")
        
        # Criar uma imagem simples de teste
        img = Image.new('RGB', (180, 180), color='lightblue')
        img.save("test_cat.jpg")
        print("✅ Imagem de teste criada: test_cat.jpg")
        print("💡 Substitua por uma imagem real de cão ou gato para testes melhores")

if __name__ == "__main__":
    print("🐱🐶 Testador da Função Lambda - Classificador de Cães e Gatos")
    print("==============================================================")
    
    # Criar imagem de teste se necessário
    create_test_image()
    
    print("\n📋 Opções de teste:")
    print("1. Teste local")
    print("2. Teste AWS Lambda")
    print("3. Teste API Gateway")
    print("4. Todos os testes")
    
    choice = input("\n🤔 Escolha uma opção (1-4): ")
    
    if choice == "1":
        test_local_lambda()
    elif choice == "2":
        function_name = input("📝 Nome da função Lambda: ") or "classificador-caes-gatos"
        region = input("🌍 Região AWS: ") or "us-east-1"
        test_aws_lambda(function_name, region)
    elif choice == "3":
        api_endpoint = input("🔗 Endpoint da API Gateway: ")
        if api_endpoint:
            test_api_gateway(api_endpoint)
        else:
            print("❌ Endpoint é obrigatório")
    elif choice == "4":
        test_local_lambda()
        print("\n" + "="*50 + "\n")
        
        function_name = input("📝 Nome da função Lambda (Enter para pular): ")
        if function_name:
            region = input("🌍 Região AWS: ") or "us-east-1"
            test_aws_lambda(function_name, region)
        
        print("\n" + "="*50 + "\n")
        
        api_endpoint = input("🔗 Endpoint da API Gateway (Enter para pular): ")
        if api_endpoint:
            test_api_gateway(api_endpoint)
    else:
        print("❌ Opção inválida")
    
    print("\n🎉 Testes concluídos!")