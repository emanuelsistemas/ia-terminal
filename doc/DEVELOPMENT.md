# Guia de Desenvolvimento do Chat IA Terminal

## Visão Geral do Sistema
O Chat IA Terminal é um assistente virtual baseado em terminal que utiliza o modelo Mixtral-8x7b da Groq para processamento de linguagem natural. O sistema é projetado com uma arquitetura modular que inclui:

### 1. Sistema de Memória em Camadas
- **Cache em Memória**: Armazena as últimas 10 mensagens para contexto imediato
- **Vector Store**: Armazena todo o histórico com busca semântica
- **Checkpoints**: Sistema de restauração de estado para backup e recuperação

### 2. Componentes Principais

#### 2.1 Assistente Principal (assistant.py)
- Gerencia o loop principal de interação
- Processa entrada do usuário
- Coordena todos os subsistemas
- Formatação e exibição de mensagens

```python
def main():
    # Loop principal do assistente
    while True:
        # Recebe input do usuário
        # Processa com IA
        # Exibe resposta formatada
```

#### 2.2 Sistema de Memória (memory/)
- **vector_store.py**: Implementa busca semântica usando ChromaDB
- **config_store.py**: Gerencia configurações persistentes
- **checkpoint_manager.py**: Sistema de checkpoints para backup/restore

#### 2.3 Cliente IA (Groq)
- Utiliza o modelo Mixtral-8x7b
- Configurado com temperatura 0.7
- Limite de 1000 tokens por resposta

### 3. Formatação e Cores
O sistema usa um esquema de cores consistente para melhor UX:

#### 3.1 Mensagens do Usuário
```
Você: [mensagem]              # Azul (\033[96m) com fundo escuro #12141d (\033[48;5;234m)
[horário]                     # Azul + Itálico + fundo escuro (\033[96m\033[3m\033[48;5;234m)
```

#### 3.2 Mensagens da IA
```
Nexus: [mensagem]             # Verde (\033[92m)
[horário]                     # Verde (\033[92m)
✓ !restore [checkpoint_id]    # Verde (\033[92m)
```

#### 3.3 Espaçamento
- Uma linha em branco entre a mensagem do usuário e a resposta da IA
- Uma linha em branco após o código de restauração da IA

### 4. Sistema de Checkpoints

#### 4.1 Estrutura
```
checkpoints/
├── checkpoints.json          # Índice de checkpoints
└── data/
    └── [checkpoint_id]/
        ├── config.json       # Estado das configurações
        └── messages.json     # Estado das mensagens
```

#### 4.2 Comandos de Checkpoint
- `!checkpoint [mensagem]`: Cria novo checkpoint
- `!restore [id]`: Restaura estado
- `!checkpoints`: Lista checkpoints disponíveis

#### 4.3 Criação Automática
- Checkpoints são criados antes de cada resposta da IA
- IDs são únicos e baseados em hash
- Mensagem automática inclui início da query

### 5. Fluxo de Processamento

1. **Entrada do Usuário**
   ```python
   user_input = input().strip()
   print(f"\033[96m\033[3m\033[48;5;234m{get_br_time()}\033[0m")
   ```

2. **Processamento**
   ```python
   # Cria checkpoint
   checkpoint_id = create_system_checkpoint(message)
   
   # Busca contexto
   context = message_cache.search_context(user_input)
   
   # Gera resposta
   response = groq_client.chat.completions.create(...)
   ```

3. **Saída**
   ```python
   print(f"\033[92mNexus:\033[0m {response}")
   print(f"\033[92m{get_br_time()}")
   print(f"\033[92m✓ !restore {checkpoint_id}\033[0m")
   ```

### 6. Variáveis de Ambiente
```bash
GROQ_API_KEY=***            # Chave API da Groq
TERM=xterm-256color         # Configuração do terminal
```

### 7. Diretórios do Projeto
```
chat-ia-terminal/
├── assistant.py            # Script principal
├── memory/                 # Sistema de memória
├── doc/                    # Documentação
├── prompts/               # Templates de prompts
├── templates/             # Templates HTML
└── workspace/             # Área de trabalho
```

### 8. Dependências Principais
```python
from groq import Groq       # API da Groq
import chromadb            # Vector store
import sqlite3             # Banco de dados local
from dotenv import load_dotenv  # Variáveis de ambiente
```

## Notas de Desenvolvimento
1. **Segurança**
   - Nunca expor a API key
   - Validar inputs do usuário
   - Confirmar antes de restaurar checkpoints

2. **Performance**
   - Cache em memória para respostas rápidas
   - Vector store para histórico longo
   - Checkpoints incrementais

3. **Manutenção**
   - Documentar alterações
   - Seguir padrão de commits
   - Manter backups regulares

## Próximos Passos
1. Implementar testes automatizados
2. Adicionar mais opções de personalização
3. Melhorar sistema de busca semântica
4. Implementar compressão de checkpoints

## Troubleshooting
1. **Erro de API**: Verificar GROQ_API_KEY
2. **Erro de Checkpoint**: Verificar permissões
3. **Erro de Vector Store**: Verificar ChromaDB

## Ambiente de Desenvolvimento

1. **Requisitos**
   - Python 3.8+
   - pip
   - virtualenv (recomendado)
   - SQLite3

2. **Setup**
   ```bash
   # Clone o repositório
   git clone [repo]
   cd chat-ia-terminal

   # Crie e ative o ambiente virtual
   python -m venv venv
   source venv/bin/activate

   # Instale as dependências
   pip install -r requirements.txt

   # Configure as variáveis de ambiente
   cp .env.example .env
   # Edite .env com suas chaves
   ```

## Estrutura de Código

### 1. Assistant Principal (assistant.py)
```python
class FileState:
    def __init__(self):
        self.filename = None
        self.content = None
        self.state = "idle"
        self.action = None

def handle_file_operation(text):
    # Lógica de manipulação de arquivos
    pass

def main():
    # Loop principal do assistente
    pass
```

### 2. Cliente Groq (llm/groq_client.py)
```python
class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL")

    def generate_response(self, prompt, system=""):
        # Lógica de geração de resposta
        pass
```

### 3. Gerenciador de Prompts (prompts/prompt_manager.py)
```python
class PromptManager:
    def __init__(self):
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        # Carrega prompts do diretório
        pass
```

## Database Schema

```sql
-- Tabela de arquivos
CREATE TABLE files (
    filename TEXT,    -- Nome do arquivo
    action TEXT,      -- create/delete
    timestamp TEXT    -- ISO format
);

-- Índices
CREATE INDEX idx_files_timestamp ON files(timestamp);
```

## Fluxo de Trabalho

1. **Criação de Feature**
   ```bash
   # Crie um branch
   git checkout -b feature/nome

   # Desenvolva a feature
   # Teste localmente
   # Atualize documentação

   # Commit e push
   git add .
   git commit -m "Descrição clara da feature"
   git push origin feature/nome
   ```

2. **Code Review**
   - Verifique style guide
   - Teste todas as funcionalidades
   - Atualize documentação
   - Solicite review

3. **Merge**
   - Resolva conflitos
   - Atualize dependências
   - Merge para main

## Testes

1. **Unit Tests**
   ```python
   def test_file_creation():
       # Setup
       state = FileState()
       
       # Test
       result = handle_file_operation(
           "crie um arquivo test.txt com hello"
       )
       
       # Assert
       assert result.startswith("📝")
   ```

2. **Integration Tests**
   ```python
   def test_groq_integration():
       client = GroqClient()
       response = client.generate_response("Hello")
       assert response is not None
   ```

## Style Guide

1. **Python**
   - PEP 8
   - Type hints
   - Docstrings
   - 80 caracteres por linha

2. **Commits**
   - Mensagens claras
   - Uma feature por commit
   - Referência issues

3. **Documentação**
   - README atualizado
   - Docstrings
   - Comentários quando necessário

## CI/CD

1. **GitHub Actions**
   ```yaml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: python -m pytest
   ```

2. **Deployment**
   ```bash
   # Build
   python setup.py build

   # Deploy
   python setup.py install
   ```

## Troubleshooting

1. **Logs**
   - Verifique chat_history.db
   - Consulte logs do sistema
   - Debug prints

2. **Erros Comuns**
   - API Key inválida
   - Permissões de arquivo
   - SQLite locked

3. **Performance**
   - Monitore uso de memória
   - Profile código lento
   - Otimize queries
