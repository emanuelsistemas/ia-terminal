# Sistema de Memória do Chat IA Terminal

## Visão Geral

O Chat IA Terminal implementa um sistema de memória em três camadas que permite manter um histórico "infinito" de conversas sem comprometer a performance.

```
┌─────────────────┐
│  Cache (RAM)    │ → Últimas 10 mensagens
├─────────────────┤
│  Vector Store   │ → Histórico completo indexado
├─────────────────┤
│  Checkpoints    │ → Snapshots do sistema
└─────────────────┘
```

## Componentes

### 1. Cache em Memória (MessageCache)

- **Localização**: `memory/message_cache.py`
- **Capacidade**: 10 mensagens mais recentes
- **Tipo de Storage**: RAM (memória volátil)
- **Velocidade**: Ultra-rápida
- **Propósito**: Manter contexto imediato da conversa

```python
class MessageCache:
    def __init__(self, max_size=10):
        self.messages = []
        self.max_size = max_size
        self.vector_memory = VectorMemory(CHROMA_DIR)
        
    def add(self, role, content):
        # Adiciona mensagem ao cache
        # Se exceder max_size, move para vector store
        
    def search_context(self, query):
        # Busca contexto relevante no histórico
```

### 2. Vector Store (ChromaDB)

- **Localização**: `memory/vector_store.py`
- **Capacidade**: Ilimitada
- **Tipo de Storage**: Disco (persistente)
- **Velocidade**: Rápida para buscas semânticas
- **Propósito**: Armazenar histórico completo com busca inteligente

```python
class VectorMemory:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.Client(...)
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
    def add_message(self, message):
        # Vetoriza e armazena mensagem
        
    def search_similar(self, query):
        # Busca mensagens semanticamente similares
```

### 3. Sistema de Checkpoints

- **Localização**: `memory/checkpoint_manager.py`
- **Capacidade**: Limitada por espaço em disco
- **Tipo de Storage**: Disco (persistente)
- **Velocidade**: Média
- **Propósito**: Backup e restauração de estados do sistema

```python
class CheckpointManager:
    def __init__(self, checkpoint_dir):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoints = self.load_checkpoints()
        
    def create_checkpoint(self, message, config_store, message_cache):
        # Cria snapshot do estado atual
        # Salva configurações e mensagens
        
    def restore_checkpoint(self, checkpoint_id):
        # Restaura sistema para estado anterior
```

## Fluxo de Dados

1. **Nova Mensagem**
   ```
   Input → Cache → Vector Store (se cache cheio)
   ```

2. **Busca de Contexto**
   ```
   Query → Cache + Vector Store → Resultados Combinados
   ```

3. **Checkpoint**
   ```
   Estado Atual → Snapshot → Arquivo em Disco
   ```

## Configurações

### 1. Cache
- **MAX_CACHE_SIZE**: 10 mensagens
- **CACHE_CLEANUP_INTERVAL**: A cada nova mensagem

### 2. Vector Store
- **CHROMA_DIR**: "./chroma_db"
- **SIMILARITY_THRESHOLD**: 0.7
- **MAX_RESULTS**: 5

### 3. Checkpoints
- **CHECKPOINT_DIR**: "./checkpoints"
- **MAX_CHECKPOINTS**: 100
- **CHECKPOINT_FORMAT**: JSON

## Estrutura de Arquivos

```
memory/
├── message_cache.py     # Cache em memória
├── vector_store.py      # Interface com ChromaDB
├── checkpoint_manager.py # Sistema de checkpoints
└── config_store.py      # Configurações persistentes

chroma_db/              # Base de dados vetorial
└── ...

checkpoints/           # Snapshots do sistema
├── checkpoints.json   # Índice de checkpoints
└── data/
    └── [checkpoint_id]/
        ├── config.json
        └── messages.json
```

## Notas de Implementação

### 1. Segurança
- Backups automáticos a cada N mensagens
- Validação de integridade dos checkpoints
- Sanitização de inputs

### 2. Performance
- Índice vetorial otimizado
- Cache em memória para acesso rápido
- Checkpoints incrementais

### 3. Manutenção
- Rotação de logs
- Limpeza automática de checkpoints antigos
- Compactação periódica do vector store

## Comandos Disponíveis

### Cache
```python
message_cache.add(role, content)
message_cache.get_all()
message_cache.clear()
```

### Vector Store
```python
vector_memory.add_message(message)
vector_memory.search_similar(query)
vector_memory.clear()
```

### Checkpoints
```python
checkpoint_manager.create_checkpoint(message)
checkpoint_manager.restore_checkpoint(id)
checkpoint_manager.list_checkpoints()
```

## Troubleshooting

1. **Cache Overflow**
   - Sintoma: Lentidão em respostas
   - Solução: Ajustar MAX_CACHE_SIZE

2. **Vector Store Lento**
   - Sintoma: Buscas demoradas
   - Solução: Otimizar índice ou reduzir dados

3. **Checkpoints Corrompidos**
   - Sintoma: Erro ao restaurar
   - Solução: Usar backup mais recente

## Próximos Passos

1. Implementar compressão de checkpoints
2. Adicionar suporte a múltiplos vector stores
3. Melhorar algoritmo de busca semântica
4. Implementar cache distribuído
