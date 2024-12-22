# Guia de Desenvolvimento

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
