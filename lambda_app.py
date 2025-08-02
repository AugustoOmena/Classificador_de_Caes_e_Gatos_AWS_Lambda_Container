import os
import json
import base64
import numpy as np
import onnxruntime as ort
from PIL import Image
import io

# Configuração global do modelo
MODEL_PATH = "modelo_opset17.onnx"

class ONNXPredictor:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        # Configurar para usar CPU (Lambda usa CPU)
        providers = ['CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Obter informações do modelo
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        # Detectar automaticamente o tamanho esperado da imagem
        input_shape = self.session.get_inputs()[0].shape
        if len(input_shape) >= 3:
            if input_shape[1] == input_shape[2]:  # height == width (imagem quadrada)
                self.img_size = (input_shape[1], input_shape[2])
            elif input_shape[2] == input_shape[3]:  # formato [batch, channels, height, width]
                self.img_size = (input_shape[2], input_shape[3])
            else:
                self.img_size = (180, 180)  # fallback
        else:
            self.img_size = (180, 180)
        
        print(f"Modelo carregado com sucesso!")
        print(f"Input shape: {input_shape}")
        print(f"Tamanho da imagem detectado: {self.img_size}")
    
    def preprocess_image(self, image):
        """Preprocessa a imagem para o formato esperado pelo modelo"""
        # Redimensionar para o tamanho detectado do modelo
        image = image.resize(self.img_size)
        
        # Converter para array numpy
        img_array = np.array(image)
        
        # Se a imagem for RGB, manter; se for RGBA, converter para RGB
        if img_array.shape[-1] == 4:
            img_array = img_array[:, :, :3]
        elif len(img_array.shape) == 2:  # Grayscale
            img_array = np.stack([img_array] * 3, axis=-1)
        
        # Normalizar para [0, 1] (sem dividir por 255 conforme seu código)
        img_array = img_array.astype(np.float32)
        
        # Adicionar dimensão do batch
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def predict(self, image):
        """Faz a predição na imagem"""
        # Preprocessar a imagem
        input_data = self.preprocess_image(image)
        
        # Fazer a inferência
        outputs = self.session.run([self.output_name], {self.input_name: input_data})
        
        # Obter probabilidades
        probabilities = outputs[0][0]
        
        return probabilities

def sigmoid(x):
    """Calcula a função sigmoide para converter um logit em probabilidade."""
    return 1 / (1 + np.exp(-x))

# Inicializar o modelo globalmente (fora do handler)
predictor = None

def init_model():
    """Inicializa o modelo se ainda não foi inicializado"""
    global predictor
    if predictor is None:
        try:
            predictor = ONNXPredictor(MODEL_PATH)
            print("Modelo inicializado com sucesso!")
        except Exception as e:
            print(f"Erro ao inicializar modelo: {e}")
            raise e

def lambda_handler(event, context):
    """Handler principal da Lambda function - VERSÃO CORRETA"""
    
    # Adicionamos um print para depuração, caso precise no futuro
    print(f"EVENTO RECEBIDO: {json.dumps(event)}")
    
    try:
        # Inicializar modelo se necessário
        init_model()

        # Acessa o método e o caminho da forma correta para este tipo de evento
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        request_path = event.get('requestContext', {}).get('http', {}).get('path')
        
        if http_method == 'POST' and request_path is not None and request_path.endswith('/predict'):
            
            # Parse do body
            body_json = json.loads(event['body'])
            
            # Decodificar imagem base64
            image_data = base64.b64decode(body_json['image'])
            image = Image.open(io.BytesIO(image_data))
            
            # Fazer a predição
            output_logit_array = predictor.predict(image)
            logit_cao = output_logit_array[0]
            prob_cao = sigmoid(logit_cao)
            prob_gato = 1 - prob_cao
            
            if prob_gato > prob_cao:
                prediction = "Gato"
                confidence = prob_gato
            else:
                prediction = "Cão"
                confidence = prob_cao
            
            response_body = {
                'prediction': prediction,
                'confidence': float(confidence),
                'probabilities': {
                    'cat': float(prob_gato),
                    'dog': float(prob_cao)
                }
            }
            
            return {
                'statusCode': 200,
                'headers': { 'Content-Type': 'application/json' },
                'body': json.dumps(response_body)
            }

        # Se a rota/método não for o esperado
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Endpoint não encontrado'})
        }

    except Exception as e:
        print(f"Erro geral: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Erro interno: {str(e)}'})
        }