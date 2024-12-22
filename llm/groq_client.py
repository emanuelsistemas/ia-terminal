import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import groq

class GroqClient:
    def __init__(self):
        """Inicializa o cliente Groq"""
        load_dotenv()
        
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env")
            
        self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        self.client = groq.Client(api_key=self.api_key)
        
        print(f"✨ Groq inicializado com modelo {self.model}")
        
    def _generate_response(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Gera uma resposta usando o Groq"""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Erro ao gerar resposta via Groq: {str(e)}")
            raise
            
    def generate_code(self, instruction: str, max_tokens: int = 1024) -> str:
        """Gera código baseado na instrução fornecida"""
        system = "You are an expert programmer. Write clean, efficient, and well-documented code."
        return self._generate_response(instruction, system, max_tokens)
        
    def explain_code(self, code: str, max_tokens: int = 1024) -> str:
        """Explica o código fornecido"""
        system = "You are a programming teacher. Explain code clearly and thoroughly."
        prompt = f"Explain this code:\n```\n{code}\n```"
        return self._generate_response(prompt, system, max_tokens)
        
    def improve_code(self, code: str, max_tokens: int = 1024) -> str:
        """Sugere melhorias para o código"""
        system = "You are a code reviewer. Suggest improvements focusing on efficiency, readability, and best practices."
        prompt = f"Suggest improvements for:\n```\n{code}\n```"
        return self._generate_response(prompt, system, max_tokens)
        
    def debug_code(self, code: str, error: Optional[str] = None, max_tokens: int = 1024) -> str:
        """Debug o código fornecido"""
        system = "You are a debugging expert. Find and fix code issues efficiently."
        prompt = f"Debug this code:\n```\n{code}\n```"
        if error:
            prompt += f"\nError message:\n{error}"
        return self._generate_response(prompt, system, max_tokens)

if __name__ == "__main__":
    # Teste rápido
    try:
        groq = GroqClient()
        result = groq.generate_code("Create a simple Hello World in Python")
        print(f"Resultado do teste:\n{result}")
    except Exception as e:
        print(f"Erro no teste: {e}")
