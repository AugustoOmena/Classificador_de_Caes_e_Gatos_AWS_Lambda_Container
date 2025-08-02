#!/bin/bash

# Configurações
FUNCTION_NAME="classificador-caes-gatos"
REGION="us-east-1"  # Altere conforme necessário
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPOSITORY_NAME="lambda-onnx-classifier"

echo "🚀 Deploy do Classificador de Cães e Gatos para AWS Lambda"
echo "========================================================"

# Verificar se AWS CLI está configurado
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI não configurado!"
    echo "Configure com: aws configure"
    exit 1
fi

echo "✅ AWS CLI configurado"
echo "📍 Região: $REGION"
echo "🏢 Account ID: $ACCOUNT_ID"

# Verificar se o modelo existe
if [ ! -f "modelo_opset17.onnx" ]; then
    echo "❌ Arquivo 'modelo_opset17.onnx' não encontrado!"
    exit 1
fi

echo "✅ Modelo encontrado"

# Criar repositório ECR se não existir
echo "🐳 Criando repositório ECR..."
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION 2>/dev/null || true

# Fazer login no ECR
echo "🔑 Fazendo login no ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Construir imagem Docker
echo "🔨 Construindo imagem Docker..."
docker build --platform linux/amd64 -t $REPOSITORY_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Erro ao construir imagem Docker"
    exit 1
fi

# Tag da imagem
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest"
docker tag $REPOSITORY_NAME $IMAGE_URI

# Push da imagem
echo "⬆️ Fazendo push da imagem..."
docker push $IMAGE_URI

if [ $? -ne 0 ]; then
    echo "❌ Erro ao fazer push da imagem"
    exit 1
fi





# # Criar função Lambda se não existir
# # echo "⚡ Criando função Lambda..."
# # aws lambda create-function \
# #     --function-name $FUNCTION_NAME \
# #     --package-type Image \
# #     --code ImageUri=$IMAGE_URI \
# #     --role arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role \
# #     --timeout 30 \
# #     --memory-size 1024 \
# #     --region $REGION 2>/dev/null

# # if [ $? -eq 0 ]; then
# #     echo "✅ Função Lambda criada"
# # else
# #     # Se já existe, apenas atualizar
# #     echo "🔄 Atualizando função Lambda existente..."
# #     aws lambda update-function-code \
# #         --function-name $FUNCTION_NAME \
# #         --image-uri $IMAGE_URI \
# #         --region $REGION
    
# #     if [ $? -eq 0 ]; then
# #         echo "✅ Função Lambda atualizada"
# #     else
# #         echo "❌ Erro ao atualizar função Lambda"
# #         exit 1
# #     fi
# # fi
# echo "🔎 Verificando se a função Lambda '$FUNCTION_NAME' já existe..."
# aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null

# # $? -eq 0 significa que o comando acima foi bem-sucedido, ou seja, a função EXISTE
# if [ $? -eq 0 ]; then
#     # A função existe, então vamos atualizá-la
#     echo "🔄 Função encontrada. Atualizando o código..."
#     aws lambda update-function-code \
#         --function-name $FUNCTION_NAME \
#         --image-uri $IMAGE_URI \
#         --region $REGION
    
#     if [ $? -eq 0 ]; then
#         echo "✅ Função Lambda atualizada com sucesso!"
#     else
#         echo "❌ Erro ao atualizar a função Lambda."
#         exit 1
#     fi
# else
#     # A função não existe, então vamos criá-la
#     echo "⚡ Função não encontrada. Criando uma nova função Lambda..."
#     aws lambda create-function \
#         --function-name $FUNCTION_NAME \
#         --package-type Image \
#         --code ImageUri=$IMAGE_URI \
#         --role arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role \
#         --timeout 30 \
#         --memory-size 1024 \
#         --region $REGION

#     if [ $? -eq 0 ]; then
#         echo "✅ Função Lambda criada com sucesso!"
#     else
#         echo "❌ Erro ao criar a função Lambda. Verifique se a role 'lambda-execution-role' existe e tem as permissões corretas."
#         exit 1
#     fi
# fi



# # Criar API Gateway (opcional)
# echo "🌐 Configurando API Gateway..."
# API_ID=$(aws apigatewayv2 create-api \
#     --name "$FUNCTION_NAME-api" \
#     --protocol-type HTTP \
#     --target arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME \
#     --region $REGION \
#     --query 'ApiId' \
#     --output text 2>/dev/null)

# if [ ! -z "$API_ID" ]; then
#     # Adicionar permissão para API Gateway invocar Lambda
#     aws lambda add-permission \
#         --function-name $FUNCTION_NAME \
#         --statement-id api-gateway-invoke \
#         --action lambda:InvokeFunction \
#         --principal apigateway.amazonaws.com \
#         --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*" \
#         --region $REGION 2>/dev/null

#     API_ENDPOINT="https://$API_ID.execute-api.$REGION.amazonaws.com"
#     echo "✅ API Gateway configurado"
#     echo "🔗 Endpoint: $API_ENDPOINT"
# else
#     echo "⚠️ API Gateway não foi criado (pode já existir)"
# fi

# echo ""
# echo "🎉 Deploy concluído com sucesso!"
# echo "📋 Informações da função:"
# echo "   Nome: $FUNCTION_NAME"
# echo "   Região: $REGION"
# echo "   Imagem: $IMAGE_URI"
# if [ ! -z "$API_ENDPOINT" ]; then
#     echo "   API: $API_ENDPOINT"
# fi
# echo ""
# echo "🧪 Teste a função com:"
# echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"image\":\"<base64_image>\"}' response.json"