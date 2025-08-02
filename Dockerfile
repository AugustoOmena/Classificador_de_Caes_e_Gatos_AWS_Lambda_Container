# Use a imagem base oficial do AWS Lambda para Python
FROM public.ecr.aws/lambda/python:3.9

# Instalar dependências do sistema
RUN yum update -y && \
    yum install -y \
    libgomp \
    && yum clean all

# Copiar requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY lambda_app.py ${LAMBDA_TASK_ROOT}/

# Criar diretório para o modelo
RUN mkdir -p /opt/ml/model

# Copiar o modelo ONNX
COPY modelo_opset17.onnx ${LAMBDA_TASK_ROOT}/

# Definir o handler
CMD ["lambda_app.lambda_handler"]