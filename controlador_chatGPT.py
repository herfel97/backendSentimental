import openai
import tiktoken

class controlador_chatgpt():
    def __init__(self):
        openai.api_key = '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'
        
    def enviar_promt(self, mensaje):
        response = openai.Completion.create(
            # model = "gpt-3.5-turbo",
            engine='text-davinci-003',
            prompt=mensaje,
            # messages = {"role":"system", "contente":mensaje},
            max_tokens=500
        )
    
        return response.choices[0].text.strip()
    
    def tokenizar_texto(self, texto):
        encoding = tiktoken.encoding_for_model("text-davinci-003")                
        numero_tokens = len( encoding.encode(texto) )
        return numero_tokens
        