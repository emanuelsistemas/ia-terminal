import re
from datetime import datetime

class PromptOptimizer:
    def __init__(self):
        # Padrões comuns de linguagem informal
        self.informal_patterns = {
            r'\b(vc|voce)\b': 'você',
            r'\b(ta|tá)\b': 'está',
            r'\b(pq|por q)\b': 'por que',
            r'\b(tb|tbm)\b': 'também',
            r'\b(agnt|agente)\b': 'a gente',
            r'\b(q|ke)\b': 'que',
            r'\bcha\b': 'acha',
            r'\bpra\b': 'para'
        }
        
        # Termos técnicos e suas expansões
        self.technical_terms = {
            'ia': 'Inteligência Artificial',
            'api': 'API (Interface de Programação de Aplicações)',
            'db': 'banco de dados',
            'ui': 'interface do usuário',
            'ux': 'experiência do usuário'
        }
    
    def normalize_text(self, text):
        """Normaliza o texto corrigindo linguagem informal"""
        text = text.lower()
        for pattern, replacement in self.informal_patterns.items():
            text = re.sub(pattern, replacement, text)
        return text
    
    def expand_technical_terms(self, text):
        """Expande termos técnicos com suas definições completas"""
        text = text.lower()
        for term, expansion in self.technical_terms.items():
            pattern = r'\b' + term + r'\b'
            text = re.sub(pattern, expansion, text)
        return text
    
    def add_context_markers(self, text):
        """Adiciona marcadores de contexto ao texto"""
        # Identifica o tipo de consulta
        if any(q in text.lower() for q in ['?', 'como', 'qual', 'quem', 'onde', 'quando', 'por que']):
            text = f"[PERGUNTA] {text}"
        elif any(cmd in text.lower() for cmd in ['crie', 'faça', 'implemente', 'adicione', 'remova', 'altere']):
            text = f"[COMANDO] {text}"
        else:
            text = f"[DECLARAÇÃO] {text}"
        return text
    
    def optimize(self, text):
        """Otimiza o prompt do usuário"""
        # Normaliza o texto
        text = self.normalize_text(text)
        
        # Expande termos técnicos
        text = self.expand_technical_terms(text)
        
        # Adiciona marcadores de contexto
        text = self.add_context_markers(text)
        
        # Adiciona timestamp
        timestamp = datetime.now().isoformat()
        text = f"{text} [TIMESTAMP: {timestamp}]"
        
        return text
    
    def get_semantic_keywords(self, text):
        """Extrai palavras-chave semânticas para melhorar a busca no ChromaDB"""
        # Remove palavras comuns e mantém termos significativos
        common_words = {'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'do', 'da', 'dos', 'das'}
        words = text.lower().split()
        keywords = [word for word in words if word not in common_words]
        return ' '.join(keywords)
