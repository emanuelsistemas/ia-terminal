import os
import sys
import json
import sqlite3
import time
from datetime import datetime
import pytz
import openai
from groq import Groq
from dotenv import load_dotenv
import threading
from memory.vector_store import VectorMemory
from memory.config_store import ConfigStore
from memory.checkpoint_manager import CheckpointManager
from prompt_optimizer import PromptOptimizer
from prompts.prompt_manager import PromptManager
import shutil  # Para obter o tamanho do terminal

# Configurações globais
base_dir = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(base_dir, 'workspace')
DB_PATH = os.path.join(base_dir, 'chat_history.db')
CONFIG_DIR = os.path.join(base_dir, 'config')
CHECKPOINT_DIR = os.path.join(base_dir, 'checkpoints')
CHROMA_DIR = os.path.join(base_dir, 'chroma_db')

# Garante que os diretórios existem
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Inicializa o banco de dados
def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Inicializa o banco de dados no início
init_db()

# Variáveis globais
message_cache = None
config_store = None
checkpoint_manager = None
groq_client = None
personality = None
prompt_optimizer = None
prompt_manager = None

class MessageCache:
    def __init__(self, max_size=10):
        self.messages = []
        self.max_size = max_size
        self.vector_memory = VectorMemory(CHROMA_DIR)

    def add(self, role, content):
        """Adiciona mensagem ao cache e ao ChromaDB"""
        # Adiciona ao cache local
        self.messages.append((role, content))
        
        # Se excedeu o limite, remove as mensagens mais antigas do cache
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]
        
        # Sempre adiciona ao ChromaDB para persistência
        self.vector_memory.add_message(role, content)

    def get_all(self):
        """Retorna todas as mensagens do cache"""
        return self.messages

    def search_context(self, query):
        """Busca contexto relevante primeiro no ChromaDB, depois no cache local"""
        # Primeiro busca no ChromaDB
        chroma_results = self.vector_memory.search_context(query)
        if chroma_results:
            return chroma_results
        
        # Se não encontrou nada no ChromaDB, usa o cache local
        if self.messages:
            context = []
            for role, content in self.messages[-3:]:  # Últimas 3 mensagens
                prefix = "Usuário: " if role == "user" else "Assistente: "
                context.append(f"{prefix}{content}")
            return context
        
        return []

    def clear(self):
        """Limpa o cache e o ChromaDB"""
        self.messages = []
        self.vector_memory.clear()

class FileState:
    def __init__(self):
        self.current_file = None
        self.open_files = set()

def get_br_time():
    """
    Retorna a hora atual no fuso horário do Brasil formatada
    
    Returns:
        str: Hora atual no formato HH:MM:SS
    """
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    return now.strftime("%H:%M:%S")

def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_with_typing(text: str, delay: float = 0.01):
    """
    Imprime texto com efeito de digitação
    
    Args:
        text: Texto a ser impresso
        delay: Atraso entre cada caractere
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write('\n')
    sys.stdout.flush()

def initialize_systems():
    """Inicializa todos os sistemas necessários"""
    global message_cache, config_store, checkpoint_manager, prompt_optimizer, prompt_manager
    
    # Inicializa sistemas
    message_cache = MessageCache()
    config_store = ConfigStore(CONFIG_DIR)
    checkpoint_manager = CheckpointManager(CHECKPOINT_DIR)
    prompt_optimizer = PromptOptimizer()
    prompt_manager = PromptManager()

def add_message_to_history(role, content):
    """Adiciona mensagem ao histórico"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)",
              (role, content))
    conn.commit()
    conn.close()
    
    # Adiciona ao cache de memória também
    message_cache.add(role, content)

def register_service_config(name, config_data):
    """Registra configuração de um novo serviço com verificações de segurança"""
    try:
        # Verifica se o serviço já existe
        exists, msg = config_store.verify_service_exists(name)
        if exists:
            print(f"\033[93mAtenção: {msg}\033[0m")
            return False
            
        # Se tiver porta especificada, verifica disponibilidade
        if "port" in config_data:
            available, reason = config_store.is_port_available(config_data["port"])
            if not available:
                print(f"\033[93mAtenção: {reason}\033[0m")
                # Tenta encontrar uma porta alternativa
                next_port, msg = config_store.get_next_available_port(
                    start_port=3000,
                    preferred_ports=[8000, 8080, 8888, 9000]
                )
                if next_port:
                    print(f"\033[92mSugestão: Use a porta {next_port} que está disponível\033[0m")
                return False
        
        # Registra o serviço
        success, msg = config_store.register_service(name, config_data)
        if not success:
            print(f"\033[91mErro: {msg}\033[0m")
            return False
            
        # Se tiver porta, registra
        if "port" in config_data:
            success, msg = config_store.register_port(config_data["port"], name)
            if not success:
                print(f"\033[91mErro ao registrar porta: {msg}\033[0m")
                return False
            
        # Registra dependências
        if "dependencies" in config_data:
            for dep_name, version in config_data["dependencies"].items():
                config_store.register_dependency(dep_name, version, name)
                
        # Registra variáveis de ambiente
        if "environment" in config_data:
            for env_name, env_desc in config_data["environment"].items():
                config_store.set_env_var(env_name, env_desc, name)
                
        print(f"\033[92mServiço '{name}' registrado com sucesso!\033[0m")
        return True
        
    except Exception as e:
        print(f"\033[91mErro ao registrar configuração: {str(e)}\033[0m")
        return False

def get_next_available_port():
    """Obtém próxima porta disponível com verificações de segurança"""
    port, msg = config_store.get_next_available_port()
    if port:
        return port
    print(f"\033[91mErro: {msg}\033[0m")
    return None

def stop_service(name):
    """Nunca para um serviço diretamente, apenas marca para revisão"""
    success, msg = config_store.stop_service(name)
    print(f"\033[93m{msg}\033[0m")
    return success

def verify_system_status():
    """Verifica estado atual do sistema"""
    # Verifica portas que precisam de atenção
    attention = config_store.verify_system_ports()
    if attention:
        print("\n\033[93mPortas que precisam de atenção:\033[0m")
        for item in attention:
            print(f"- Porta {item['port']} ({item['service']}): {item['issue']}")
    
    # Obtém visão geral
    overview = config_store.get_system_overview()
    print("\n\033[92mVisão Geral do Sistema:\033[0m")
    print(f"- Serviços Ativos: {overview['active_services']}")
    print(f"- Portas em Uso: {overview['ports_in_use']}")
    print(f"- Total de Dependências: {overview['total_dependencies']}")
    print(f"- Variáveis de Ambiente: {overview['environment_vars']}")
    print(f"- Última Atualização: {overview['last_updated']}")

def create_system_checkpoint(message):
    """Cria um checkpoint do sistema"""
    try:
        checkpoint_id = checkpoint_manager.create_checkpoint(
            message=message,
            config_store=config_store,
            message_cache=message_cache
        )
        return checkpoint_id
    except Exception as e:
        print(f"\033[91mErro ao criar checkpoint: {str(e)}\033[0m")
        return None

def create_file(filename, content):
    """Cria um arquivo com o conteúdo especificado no diretório workspace"""
    try:
        # Streaming state 1: Iniciando
        print_with_typing("⚡ Iniciando criação do arquivo...", delay=0.02)
        
        # Garante que o nome do arquivo é seguro
        safe_filename = os.path.basename(filename)
        print_with_typing("🔍 Validando nome do arquivo...", delay=0.02)
        
        # Garante que o diretório workspace existe
        if not os.path.exists(WORKSPACE_DIR):
            print_with_typing("📁 Criando diretório workspace...", delay=0.02)
            os.makedirs(WORKSPACE_DIR)
            
        # Caminho completo do arquivo
        filepath = os.path.join(WORKSPACE_DIR, safe_filename)
        print_with_typing("📝 Preparando para escrever...", delay=0.02)
        
        # Cria o arquivo com o conteúdo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_with_typing("✅ Arquivo criado com sucesso!", delay=0.02)
        return True, f"Arquivo '{safe_filename}' criado com sucesso em {WORKSPACE_DIR}"
    except Exception as e:
        print_with_typing("❌ Erro ao criar arquivo!", delay=0.02)
        return False, f"Erro ao criar arquivo: {str(e)}"

def handle_user_input(user_input):
    """Processa entrada do usuário com sistema de memória em camadas"""
    try:
        # Otimiza o prompt do usuário
        optimized_input = prompt_optimizer.optimize(user_input)
        
        # Extrai palavras-chave para busca semântica
        search_keywords = prompt_optimizer.get_semantic_keywords(user_input)
        
        # Busca contexto usando as palavras-chave
        context = message_cache.search_context(search_keywords)
        
        # Gera resposta com IA
        if groq_client:
            # Obtém os prompts do gerenciador
            personality = prompt_manager.get_prompt("personality")
            code_assistant = prompt_manager.get_prompt("code_assistant")
            
            messages = [
                {"role": "system", "content": personality["system"]},
                {"role": "system", "content": code_assistant["system"]},
            ]
            
            # Adiciona o prompt otimizado como contexto
            messages.append({"role": "system", "content": f"Prompt otimizado do usuário: {optimized_input}"})
            
            # Adiciona contexto histórico se disponível
            if context:
                context_str = "\n".join(context)
                context_prompt = f"Histórico relevante da conversa:\n{context_str}\n\nUse estas informações para responder ao usuário de forma precisa sobre o que foi discutido anteriormente."
                messages.append({"role": "system", "content": context_prompt})
            
            # Adiciona histórico recente do cache
            recent_messages = message_cache.get_all()[-5:]  # Últimas 5 mensagens
            for msg in recent_messages:
                messages.append({"role": msg[0], "content": msg[1]})
            
            # Adiciona a mensagem original do usuário
            messages.append({"role": "user", "content": user_input})
            
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            response = completion.choices[0].message.content
            add_message_to_history("assistant", response)
            
            # Retorna a resposta com a cor verde
            response = f"\033[92m{response}\033[0m"
            return response, None
        else:
            return "Desculpe, o suporte a IA não está disponível no momento.", None
            
    except Exception as e:
        print(f"\033[91mErro ao processar mensagem: {str(e)}\033[0m")
        return "Desculpe, ocorreu um erro ao processar sua mensagem.", None

def restore_system_checkpoint(checkpoint_id):
    """Restaura o sistema para um checkpoint específico"""
    try:
        # Obtém info do checkpoint
        checkpoint = checkpoint_manager.get_checkpoint_info(checkpoint_id)
        if not checkpoint:
            print(f"\033[91mCheckpoint '{checkpoint_id}' não encontrado\033[0m")
            return False
            
        print(f"\n\033[93mRestaurando sistema para checkpoint: {checkpoint_id}\033[0m")
        print(f"Mensagem: {checkpoint['message']}")
        print(f"Criado em: {checkpoint['timestamp']}")
        
        # Confirma com usuário
        confirm = input("\nTem certeza? Todas as alterações após este ponto serão perdidas [s/N]: ")
        if confirm.lower() != 's':
            print("\033[93mOperação cancelada pelo usuário\033[0m")
            return False
            
        # Restaura
        success = checkpoint_manager.restore_checkpoint(checkpoint_id)
        
        if success:
            print("\n\033[92m✓ Sistema restaurado com sucesso!\033[0m")
            verify_system_status()  # Mostra estado atual
        else:
            print("\033[91mErro ao restaurar sistema\033[0m")
            
        return success
        
    except Exception as e:
        print(f"\033[91mErro ao restaurar checkpoint: {str(e)}\033[0m")
        return False

def list_system_checkpoints():
    """Lista checkpoints disponíveis"""
    try:
        checkpoints = checkpoint_manager.list_checkpoints()
        if not checkpoints:
            print("\n\033[93mNenhum checkpoint encontrado\033[0m")
            return
            
        print("\n\033[92mCheckpoints Disponíveis:\033[0m")
        for cp in checkpoints:
            # Formata timestamp
            ts = datetime.fromisoformat(cp["timestamp"])
            ts_str = ts.strftime("%d/%m/%Y %H:%M:%S")
            
            print(f"\nID: \033[96m{cp['id']}\033[0m")
            print(f"Mensagem: {cp['message']}")
            print(f"Criado em: {ts_str}")
            
            # Marca checkpoint atual
            if cp["id"] == checkpoint_manager.checkpoints["current"]:
                print("\033[92m✓ Checkpoint Atual\033[0m")
                
    except Exception as e:
        print(f"\033[91mErro ao listar checkpoints: {str(e)}\033[0m")

def get_terminal_width():
    """Retorna a largura do terminal"""
    terminal_size = shutil.get_terminal_size()
    return terminal_size.columns

def print_user_message(message, timestamp=None):
    """Imprime mensagem do usuário com fundo preenchendo a linha toda"""
    width = get_terminal_width()
    
    # Imprime linha em branco com fundo
    print(f"\033[48;5;234m{' ' * width}\033[0m")
    
    if message:
        # Imprime mensagem com fundo
        print(f"\033[48;5;234m \033[96mVocê:\033[0m\033[96m {message}\033[48;5;234m{' ' * (width - len(message) - 8)}\033[0m")
    
    if timestamp:
        # Imprime timestamp com fundo
        print(f"\033[48;5;234m \033[96m{timestamp}\033[48;5;234m{' ' * (width - len(timestamp) - 2)}\033[0m")
    
    # Imprime linha em branco com fundo
    print(f"\033[48;5;234m{' ' * width}\033[0m")

def main():
    """Função principal do assistente"""
    global groq_client, personality
    
    try:
        # Inicializa sistemas
        initialize_systems()
        
        # Configura o caminho do .env
        ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        print(f"🔍 Procurando .env em: {ENV_PATH}")
        
        # Carrega variáveis de ambiente e mostra debug
        load_dotenv(dotenv_path=ENV_PATH, verbose=True)
        print(f"📁 Diretório atual: {os.getcwd()}")
        print(f"🔑 GROQ_API_KEY: {'***' + os.getenv('GROQ_API_KEY')[-4:] if os.getenv('GROQ_API_KEY') else 'não encontrado'}")
        
        # Interface inicial
        clear_screen()
        print_with_typing("👋 Olá! Eu sou o Nexus, seu assistente virtual com IA!")
        print_with_typing("Estou aqui para ajudar você com qualquer tarefa de programação ou sistema.")
        print_with_typing("Usando Groq com modelo Mixtral-8x7b")
        print_with_typing("Pode me dizer naturalmente o que precisa, ou digite 'ajuda' para ver comandos específicos.")
        print()
        
        # Cria pasta workspace se não existir
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        
        try:
            print_with_typing("🔄 Inicializando Groq...")
            groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            print_with_typing("✨ Groq inicializado com modelo mixtral-8x7b-32768")
        except Exception as e:
            print(f"\033[91mErro ao inicializar IA:\033[0m {str(e)}")
            print("Continuando sem suporte a IA...")
        
        while True:
            try:
                print()  # Linha extra antes do input para manter espaçamento
                print("Você: ", end="", flush=True)  # Input sem formatação
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Move o cursor duas linhas para cima para sobrescrever a linha vazia e o input
                print("\033[2A", end="")
                
                # Imprime a mensagem e o timestamp juntos
                print_user_message(user_input, get_br_time())
                
                if user_input.lower() == 'sair':
                    print("\n\033[92mNexus:\033[0m Até logo! Foi um prazer ajudar!")
                    break
                
                result = handle_user_input(user_input)
                if isinstance(result, tuple):
                    response, checkpoint_id = result
                else:
                    response, checkpoint_id = result, None
                    
                if response:
                    print()  # Uma linha entre usuário e IA
                    print(f"\033[92mNexus:\033[0m {response}")
                    # Horário e código de restauração em verde e itálico
                    print(f"\033[92m\033[3m{get_br_time()}")
                    if checkpoint_id:
                        print(f"\033[92m\033[3m✓ !restore {checkpoint_id}\033[0m")
                        print()  # Linha extra após o restore
                
            except EOFError:
                print("\n\033[92mNexus:\033[0m Até logo! Foi um prazer ajudar!")
                break
            except KeyboardInterrupt:
                print("\n\033[92mNexus:\033[0m Até logo! Foi um prazer ajudar!")
                break
            except Exception as e:
                print(f"\033[91mErro:\033[0m {str(e)}")
    
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro fatal: {e}")
