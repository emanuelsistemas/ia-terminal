# Chat IA Terminal

Um assistente virtual em linha de comando que utiliza modelos de linguagem para ajudar em tarefas de programação.

## Estrutura do Projeto

```
chat-ia-terminal/
├── assistant.py      # Arquivo principal do assistente
├── llm/             # Módulo para integrações com LLMs
│   ├── __init__.py
│   └── groq_client.py
├── prompts/         # Prompts e personalidades do assistente
│   ├── __init__.py
│   ├── prompt_manager.py
│   ├── personality.json
│   ├── file_creator.json
│   └── ...
├── memory/          # Sistema de memória e persistência
│   ├── __init__.py
│   └── vector_store.py
├── workspace/       # Diretório para arquivos gerados
├── chroma_db/       # Banco de dados vetorial
└── doc/            # Documentação
    ├── README.md
    ├── ARCHITECTURE.md
    ├── DEVELOPMENT.md
    └── MEMORY_SYSTEM.md
```

## Funcionalidades

### 1. Sistema de Memória em Camadas
- Cache em RAM para últimas 10 mensagens
- Vector Store (ChromaDB) para histórico completo
- Arquivamento automático de mensagens antigas
- Busca semântica inteligente
- [Documentação Completa](./MEMORY_SYSTEM.md)

### 2. Integração com LLMs
- Suporte ao Groq (mixtral-8x7b-32768)
- Sistema de prompts personalizáveis
- Gerenciamento de personalidade do assistente

### 3. Manipulação de Arquivos
- Criação de arquivos com confirmação
- Deleção de arquivos com confirmação
- Sistema de memória persistente (SQLite)
- Histórico de operações

### 4. Interface
- Interface em linha de comando colorida
- Efeito de digitação para respostas
- Timestamps em formato Brasil/São Paulo
- Sistema de confirmação S/N

## Comandos Disponíveis

1. **Criação de Arquivo**
   ```
   crie um arquivo [nome] com [conteúdo]
   ```

2. **Deleção de Arquivo**
   ```
   delete [nome do arquivo]
   delete este arquivo
   apague o arquivo que criamos
   ```

3. **Comandos do Sistema**
   - `status`: Informações do sistema
   - `hora`: Data e hora atual
   - `memoria`: Uso de memória
   - `disco`: Uso do disco
   - `limpar`: Limpa a tela
   - `processos`: Lista processos ativos
   - `rede`: Informações de rede

4. **Comandos de IA**
   - `codigo <descrição>`: Gera código
   - `explicar <código>`: Explica código
   - `melhorar <código>`: Sugere melhorias
   - `debug <código>`: Ajuda com debugging
   - `projeto <descrição>`: Cria estrutura de projeto
   - `revisar <código>`: Faz revisão de código
   - `arquitetura <descrição>`: Projeta arquitetura
   - `sistema <comando>`: Ajuda com sistema

## Configuração

1. Crie um arquivo `.env` com:
   ```
   GROQ_API_KEY=sua_chave_aqui
   GROQ_MODEL=mixtral-8x7b-32768
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Execute o assistente:
   ```
   ./chat-ia
   ```

## Banco de Dados

O sistema usa SQLite para manter histórico de operações com arquivos:

```sql
CREATE TABLE files (
    filename text,
    action text,
    timestamp text
);
```

## Personalização

Os prompts podem ser personalizados editando os arquivos JSON em `/prompts/`:

- `personality.json`: Personalidade base
- `file_creator.json`: Criação de arquivos
- `code_assistant.json`: Assistência com código
- etc.

## Cores e Estilo

- Usuário: Azul claro/ciano (\033[96m)
- Assistente: Verde matrix (\033[38;5;46m)
- Timestamps: Em itálico
- Uma linha em branco entre mensagens

## Próximos Passos

1. Otimização de performance
2. Suporte a mais modelos de IA
3. Sistema de plugins
4. Interface web opcional
5. Suporte a múltiplos idiomas
