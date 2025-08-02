# 🚀 Classificador de Cães e Gatos - AWS Lambda

Deploy do seu modelo ONNX como uma função Lambda usando containers.

## 📋 Pré-requisitos

- **AWS CLI** configurado (`aws configure`)
- **Docker** instalado e rodando
- **IAM Role** para Lambda com permissões básicas
- Arquivo `modelo_opset17.onnx` (seu modelo treinado)

## 🏗️ Estrutura dos Arquivos

```
lambda-projeto/
├── Dockerfile                 # Container para Lambda
├── lambda_app.py             # Handler da função
├── requirements.txt          # Dependências
├── deploy.sh                 # Script de deploy
├── test_lambda.py           # Script de testes
├── modelo_opset17.onnx      # SEU MODELO
└── README_Lambda.md         # Este arquivo
```

## ⚡ Setup Completo

### 1. Configurar AWS CLI

```bash
aws configure
# Inserir: Access Key, Secret Key, Região (ex: us-east-1)
```

### 2. Criar IAM Role (se não tiver)

```bash
# Criar role básica para Lambda
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Anexar política básica
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 3. Executar Deploy

```bash
# Dar permissão de execução
chmod +x deploy.sh

# Executar o script de deploy
./deploy.sh
```

> **📝 Nota para Windows**: Se estiver usando Windows, você pode adaptar o script para PowerShell ou executar os comandos manualmente seguindo a sequência do `deploy.sh`.

> **🍎 Nota para Mac M2**: O script já inclui `--platform linux/amd64` necessário para compatibilidade com Lambda.

### 4. Criar Função Lambda (Manual)

Após o push da imagem, crie a função Lambda manualmente no console AWS ou via CLI:

```bash
# Obter URI da imagem (ajuste o ACCOUNT_ID e REGION)
IMAGE_URI="123456789012.dkr.ecr.us-east-1.amazonaws.com/lambda-onnx-classifier:latest"

# Criar função Lambda
aws lambda create-function \
    --function-name classificador-caes-gatos \
    --package-type Image \
    --code ImageUri=$IMAGE_URI \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
    --timeout 30 \
    --memory-size 1024 \
    --region us-east-1
```

### 5. Configurar API Gateway (Manual)

1. Vá para o **Console AWS → API Gateway**
2. Crie uma **HTTP API**
3. Adicione integração com sua função Lambda
4. Configure rota **POST /predict**
5. Deploy da API

## 🧪 Testando a Função

### Teste via AWS CLI

```bash
# Preparar payload (converta sua imagem para base64)
echo '{"image":"<base64_da_imagem>"}' > test_payload.json

# Invocar função
aws lambda invoke \
  --function-name classificador-caes-gatos \
  --payload fileb://test_payload.json \
  response.json

# Ver resultado
cat response.json
```

### Teste via API Gateway

```bash
# Substitua pela URL da sua API
curl -X POST \
  https://seu-api-id.execute-api.us-east-1.amazonaws.com/predict \
  -H "Content-Type: application/json" \
  -d '{"image":"<base64_da_imagem>"}'
```

### Script de Teste Python

```python
import base64
import json
import requests

# Converter imagem para base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Testar API
image_b64 = image_to_base64("sua_imagem.jpg")
payload = {"image": image_b64}

response = requests.post(
    "https://sua-api.execute-api.us-east-1.amazonaws.com/predict",
    json=payload
)

print(response.json())
```

## 📡 API Specification

### POST /predict

Classifica uma imagem de cão ou gato.

**Request:**

```json
{
  "image": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a..."
}
```

**Response (Sucesso):**

```json
{
  "prediction": "Gato",
  "confidence": 0.95,
  "probabilities": {
    "cat": 0.95,
    "dog": 0.05
  }
}
```

**Response (Erro):**

```json
{
  "error": "Erro ao processar imagem: <detalhes>"
}
```

## ⚙️ Configurações dos Arquivos

### Dockerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.9

RUN yum update -y && \
    yum install -y libgomp && yum clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

COPY lambda_app.py ${LAMBDA_TASK_ROOT}/
COPY modelo_opset17.onnx ${LAMBDA_TASK_ROOT}/

CMD ["lambda_app.lambda_handler"]
```

### requirements.txt

```
onnxruntime==1.16.3
numpy==1.24.3
Pillow==10.0.1
```

### deploy.sh (Simplificado)

```bash
#!/bin/bash

FUNCTION_NAME="classificador-caes-gatos"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPOSITORY_NAME="lambda-onnx-classifier"

# Verificações e setup do ECR
echo "🚀 Deploy do Classificador de Cães e Gatos para AWS Lambda"

# Criar repositório ECR
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION 2>/dev/null || true

# Login no ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build da imagem (com platform para Mac M2)
docker build --platform linux/amd64 -t $REPOSITORY_NAME .

# Tag e push
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest"
docker tag $REPOSITORY_NAME $IMAGE_URI
docker push $IMAGE_URI

echo "✅ Imagem enviada para ECR: $IMAGE_URI"
echo "🔄 Agora crie a função Lambda manualmente com esta imagem"
```

## 🛠️ Configurações Recomendadas

### Função Lambda

- **Memory**: 1024 MB (ajuste conforme necessário)
- **Timeout**: 30 segundos
- **Architecture**: x86_64
- **Runtime**: Container Image

### Performance

- **Provisioned Concurrency**: Configure se precisar de latência consistente
- **Dead Letter Queue**: Para capturar erros de processamento
- **CloudWatch Logs**: Já configurado automaticamente

## 💰 Estimativa de Custos

Para **1.000 classificações/mês**:

- **Lambda (1024MB, 30s)**: ~$1.00
- **ECR Storage**: ~$0.10
- **API Gateway**: ~$3.50 (1M requests)
- **CloudWatch Logs**: ~$0.50
- **Total**: ~$5.10/mês

## 🔧 Troubleshooting

### Erro: "modelo_opset17.onnx not found"

- Verifique se o arquivo está na pasta raiz do projeto
- Confirme o nome exato do arquivo no Dockerfile

### Build falha no Mac M2

- Certifique-se de usar `--platform linux/amd64`
- Pode ser necessário habilitar emulação: `docker buildx create --use`

### Timeout na Lambda

```bash
# Aumentar timeout (máximo 15 minutos)
aws lambda update-function-configuration \
  --function-name classificador-caes-gatos \
  --timeout 60
```

### Imagem muito grande

- Use `.dockerignore` para excluir arquivos desnecessários
- Considere multi-stage build para reduzir tamanho

### Cold Start lento

- Configure **Provisioned Concurrency** para APIs críticas
- Considere usar instâncias menores se o modelo permitir

## 📊 Monitoramento

### CloudWatch Metrics

- **Invocations**: Número de execuções
- **Duration**: Tempo de execução
- **Errors**: Taxa de erros
- **Throttles**: Execuções limitadas

### Logs

```bash
# Ver logs em tempo real
aws logs tail /aws/lambda/classificador-caes-gatos --follow

# Filtrar erros
aws logs filter-log-events \
  --log-group-name /aws/lambda/classificador-caes-gatos \
  --filter-pattern "ERROR"
```

## 🌐 Integração Frontend

### JavaScript (Vanilla)

```javascript
async function classifyImage(imageFile) {
  // Converter para base64
  const base64 = await new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.readAsDataURL(imageFile);
  });

  // Chamar API
  const response = await fetch(
    "https://sua-api.execute-api.us-east-1.amazonaws.com/predict",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: base64 }),
    }
  );

  return await response.json();
}
```

### React

```jsx
import { useState } from "react";

function ImageClassifier() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    try {
      const result = await classifyImage(file);
      setResult(result);
    } catch (error) {
      console.error("Erro:", error);
    }
    setLoading(false);
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleImageUpload} />
      {loading && <p>Classificando...</p>}
      {result && (
        <div>
          <h3>Resultado: {result.prediction}</h3>
          <p>Confiança: {(result.confidence * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}
```

## 📚 Comandos Úteis

```bash
# Listar funções Lambda
aws lambda list-functions

# Ver detalhes da função
aws lambda get-function --function-name classificador-caes-gatos

# Atualizar código da função
aws lambda update-function-code \
  --function-name classificador-caes-gatos \
  --image-uri NOVA_IMAGE_URI

# Deletar função
aws lambda delete-function --function-name classificador-caes-gatos

# Listar repositórios ECR
aws ecr describe-repositories

# Ver logs de build
docker logs CONTAINER_ID
```

## 🚀 Deploy Automatizado (Opcional)

Para automatizar todo o processo, você pode criar um script completo:

```bash
#!/bin/bash
# deploy_completo.sh

# 1. Build e push da imagem
./deploy.sh

# 2. Criar/atualizar função
aws lambda create-function \
  --function-name classificador-caes-gatos \
  --package-type Image \
  --code ImageUri=$IMAGE_URI \
  --role arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role \
  --timeout 30 \
  --memory-size 1024 \
  --region $REGION

# 3. Criar API Gateway via CLI (se desejar)
# ... comandos para criar API Gateway
```

## 🎯 Próximos Passos

1. **✅ Deploy básico funcionando**
2. **📊 Configurar monitoramento detalhado**
3. **🔄 Implementar CI/CD com GitHub Actions**
4. **🌍 Multi-região para alta disponibilidade**
5. **⚡ Otimizar performance (Provisioned Concurrency)**
6. **🔒 Implementar autenticação (API Keys/Cognito)**

## 🏆 Conclusão

Sua função Lambda está pronta para produção!

**✨ Características da implementação:**

- ✅ **Compatível com Mac M2** (`--platform linux/amd64`)
- ✅ **Deploy simplificado** (só até push da imagem)
- ✅ **Modelo otimizado** (`modelo_opset17.onnx`)
- ✅ **Handler robusto** (tratamento de erros aprimorado)
- ✅ **Serverless** (escalabilidade automática)
- ✅ **Cost-effective** (pague apenas pelo uso)

🚀 **Sua API de classificação está pronta para o mundo!**
