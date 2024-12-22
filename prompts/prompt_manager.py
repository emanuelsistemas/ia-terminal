import os
import json
from typing import Dict, Optional

class PromptManager:
    def __init__(self, prompts_dir: str = None):
        """Inicializa o gerenciador de prompts"""
        if prompts_dir is None:
            prompts_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, dict] = {}
        self.load_prompts()
    
    def load_prompts(self):
        """Carrega todos os prompts do diretório"""
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.json'):
                prompt_name = filename[:-5]  # Remove .json
                filepath = os.path.join(self.prompts_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.prompts[prompt_name] = json.load(f)
    
    def get_prompt(self, name: str, **kwargs) -> Optional[str]:
        """Obtém um prompt específico e formata com os argumentos fornecidos"""
        if name not in self.prompts:
            return None
        
        prompt_data = self.prompts[name]
        system = prompt_data.get('system', '')
        template = prompt_data.get('template', '')
        
        # Formata o template com os argumentos fornecidos
        if kwargs:
            try:
                template = template.format(**kwargs)
            except KeyError as e:
                print(f"Erro: Argumento {e} necessário para o prompt '{name}'")
                return None
        
        return {
            'system': system,
            'template': template
        }
    
    def list_prompts(self) -> list:
        """Lista todos os prompts disponíveis"""
        return list(self.prompts.keys())

# Exemplo de uso
if __name__ == "__main__":
    pm = PromptManager()
    print("Prompts disponíveis:", pm.list_prompts())
