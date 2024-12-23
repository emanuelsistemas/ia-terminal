# Sistema de Prompts do Chat IA Terminal

## Visão Geral
O sistema de prompts é responsável por definir o comportamento e personalidade da IA. Ele usa uma arquitetura em camadas onde diferentes prompts são combinados para criar o comportamento final.

## Estrutura de Arquivos
```
/prompts/
├── personality.json       # Personalidade base e comportamento geral
├── code_assistant.json    # Comportamento específico para programação
├── prompt_manager.py     # Gerenciador que carrega e combina prompts
└── outros prompts...     # Prompts específicos para outras funcionalidades
```

## Formato dos Prompts
Cada prompt é um arquivo JSON com a seguinte estrutura:
```json
{
    "name": "nome_do_prompt",
    "description": "Descrição do propósito",
    "system": "Texto do prompt que define comportamento",
    "template": "{input}"
}
```

## Gerenciamento de Prompts
O `PromptManager` é responsável por:
1. Carregar prompts dos arquivos JSON
2. Combinar múltiplos prompts
3. Fornecer os prompts para o assistente

```python
class PromptManager:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            prompts_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, dict] = {}
        self.load_prompts()
    
    def load_prompts(self):
        """Carrega todos os prompts do diretório"""
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.json'):
                prompt_name = filename[:-5]
                filepath = os.path.join(self.prompts_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.prompts[prompt_name] = json.load(f)
```

## Aplicação dos Prompts
Os prompts são aplicados em camadas na seguinte ordem:

1. **Personalidade Base** (personality.json):
```json
{
    "name": "personality",
    "description": "Personalidade base do assistente",
    "system": "Você é o Nexus, um assistente técnico que equilibra objetividade com empatia. Mantenha o foco em entender e resolver as necessidades do usuário. Evite opiniões sobre dificuldades ou complexidade - você está aqui para ajudar a fazer acontecer. Faça perguntas quando precisar entender melhor, mas mantenha-as específicas e relevantes.",
    "template": "{input}"
}
```

2. **Comportamento Técnico** (code_assistant.json):
```json
{
    "name": "code_assistant",
    "description": "Assistente especializado em código",
    "system": "Você é um assistente de desenvolvimento prático. Siga estas diretrizes:\n\n1. FASE DE ENTENDIMENTO\n- Escute o usuário\n- Faça perguntas relevantes sobre o que ele quer construir\n- Entenda o objetivo antes de sugerir soluções\n\n2. FASE DE PLANEJAMENTO\n- Sugira abordagens práticas\n- Discuta brevemente as tecnologias relevantes\n- Confirme a direção com o usuário\n\n3. FASE DE IMPLEMENTAÇÃO\n- Comece com passos pequenos e práticos\n- Mostre código apenas quando o usuário estiver pronto\n- Guie o desenvolvimento gradualmente\n\nREGRAS IMPORTANTES:\n- Nunca diga que algo é difícil ou complexo\n- Foque em ajudar a fazer acontecer\n- Mantenha o usuário no controle do processo",
    "template": "{input}"
}
```

## Integração com o Assistente
O assistente combina os prompts ao gerar respostas:

```python
def handle_user_input(user_input):
    # Obtém os prompts do gerenciador
    personality = prompt_manager.get_prompt("personality")
    code_assistant = prompt_manager.get_prompt("code_assistant")
    
    # Combina os prompts na ordem correta
    messages = [
        {"role": "system", "content": personality["system"]},
        {"role": "system", "content": code_assistant["system"]},
    ]
    
    # Adiciona contexto e input do usuário
    messages.append({"role": "user", "content": user_input})
```

## Otimização de Prompts
O sistema inclui um otimizador que:
1. Normaliza linguagem informal
2. Expande termos técnicos
3. Adiciona marcadores de contexto
4. Inclui timestamp

```python
class PromptOptimizer:
    def optimize(self, text):
        # Normaliza o texto
        text = self.normalize_text(text)
        
        # Expande termos técnicos
        text = self.expand_technical_terms(text)
        
        # Adiciona marcadores de contexto
        text = self.add_context_markers(text)
        
        # Adiciona timestamp
        text = f"{text} [TIMESTAMP: {timestamp}]"
        
        return text
```

## Análise para Outra IA
Para implementar um sistema similar, considere:

1. **Separação de Responsabilidades**:
   - Mantenha prompts em arquivos separados
   - Use um gerenciador central
   - Implemente otimização de prompts

2. **Ordem de Aplicação**:
   - Personalidade base primeiro
   - Comportamentos específicos depois
   - Contexto e input por último

3. **Pontos de Atenção**:
   - Carregamento dinâmico de prompts
   - Combinação efetiva de múltiplos prompts
   - Otimização de input do usuário

4. **Melhorias Possíveis**:
   - Cache de prompts processados
   - Validação de prompts
   - Versionamento de prompts
   - Sistema de fallback
