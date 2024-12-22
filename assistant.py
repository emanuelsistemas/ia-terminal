#!/usr/bin/env python3
import sys
import time
from datetime import datetime
import os
import sqlite3
from dotenv import load_dotenv
from llm.groq_client import GroqClient
from prompts.prompt_manager import PromptManager
import pytz
import threading
from memory.vector_store import VectorMemory
import json

# Configura o caminho do .env
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
print(f"🔍 Procurando .env em: {ENV_PATH}")

# Carrega variáveis de ambiente e mostra debug
load_dotenv(dotenv_path=ENV_PATH, verbose=True)
print(f"📁 Diretório atual: {os.getcwd()}")
print(f"🔑 GROQ_API_KEY: {'***' + os.getenv('GROQ_API_KEY')[-4:] if os.getenv('GROQ_API_KEY') else 'não encontrado'}")

# Configurações globais
WORKSPACE_DIR = "/root/projetos/chat-ia-terminal/workspace"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')

class MessageCache:
    def __init__(self, max_size=10):
        self.messages = []
        self.max_size = max_size
        self.vector_memory = VectorMemory(CHROMA_DIR)

    def add(self, role, content):
        """Adiciona mensagem ao cache e arquiva antigas se necessário"""
        self.messages.append((role, content))
        
        # Se excedeu o limite, arquiva as mensagens mais antigas
        if len(self.messages) > self.max_size:
            # Pega as mensagens que serão arquivadas
            to_archive = self.messages[:-self.max_size]
            # Atualiza o cache para manter só as mais recentes
            self.messages = self.messages[-self.max_size:]
            # Arquiva no Chroma
            self.vector_memory.archive_messages(to_archive)

    def get_all(self):
        return self.messages

    def search_context(self, query):
        """Busca contexto relevante no histórico"""
        return self.vector_memory.search_context(query)

    def clear(self):
        self.messages = []
        self.vector_memory.clear()

def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela para operações com arquivos
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (filename text, action text, timestamp text)''')
    
    # Tabela para histórico de conversas
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (role text, content text, timestamp text)''')
    
    conn.commit()
    conn.close()

def add_to_history(filename, action):
    """Adiciona uma ação ao histórico"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO files VALUES (?, ?, ?)", 
              (filename, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_last_file():
    """Retorna o último arquivo manipulado"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filename FROM files ORDER BY timestamp DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_message_to_history(role, content):
    """Adiciona uma mensagem ao histórico e cache"""
    # Adiciona ao cache primeiro (mais rápido)
    message_cache.add(role, content)
    
    # Adiciona ao banco de dados de forma assíncrona
    threading.Thread(target=_async_save_message, 
                    args=(role, content)).start()

def _async_save_message(role, content):
    """Salva mensagem no banco de dados de forma assíncrona"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO messages VALUES (?, ?, ?)",
                  (role, content, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"\033[91mErro ao salvar mensagem: {str(e)}\033[0m")

def get_conversation_context(max_messages=10):
    """Retorna contexto primeiro do cache, depois do banco"""
    # Tenta pegar do cache primeiro
    cached = message_cache.get_all()
    if len(cached) >= max_messages:
        messages = cached[-max_messages:]
    else:
        # Se precisar mais mensagens, busca do banco
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                SELECT role, content 
                FROM messages 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (max_messages - len(cached),))
            db_messages = c.fetchall()
            conn.close()
            
            # Combina mensagens do banco com cache
            messages = db_messages + cached
        except Exception as e:
            print(f"\033[91mErro ao buscar mensagens: {str(e)}\033[0m")
            messages = cached

    # Formata o contexto
    context = []
    for role, content in messages:
        if role == "user":
            context.append(f"Usuário: {content}")
        else:
            context.append(f"Assistente: {content}")
    
    return "\n".join(context)

def get_chat_context(user_input):
    """Retorna contexto inteligente combinando cache e vector store"""
    # Sempre inclui as últimas mensagens do cache
    recent = get_conversation_context(max_messages=5)
    
    # Busca mensagens relevantes no histórico
    historical = message_cache.search_context(user_input)
    
    # Se encontrou contexto histórico relevante
    if historical:
        context = "Contexto histórico relevante:\n"
        context += "\n".join(historical)
        context += "\n\nConversa atual:\n"
        context += recent
    else:
        context = recent
    
    return context if context else ""

def handle_file_operation(text):
    global file_state
    
    if file_state.state == "idle":
        if "crie um arquivo" in text.lower():
            parts = text.lower().split("com")
            if len(parts) >= 2:
                # Remove "crie um arquivo" e espaços extras
                raw_filename = parts[0].replace("crie um arquivo", "").strip()
                
                try:
                    filepath = get_safe_filepath(raw_filename)
                    file_state.filename = filepath  # Guarda o caminho completo
                    file_state.content = parts[1].strip().strip('.')
                    file_state.state = "waiting_confirmation"
                    file_state.action = "create"
                    
                    # Indica se está usando o workspace ou caminho personalizado
                    if filepath.startswith(WORKSPACE_DIR):
                        location_msg = f"Local (workspace): {filepath}"
                    else:
                        location_msg = f"Local: {filepath}"
                    
                    return f"📝 Criar arquivo:\n{location_msg}\nConteúdo: {file_state.content}\nConfirma? (S/N): "
                except ValueError as e:
                    file_state.state = "idle"
                    return f"❌ {str(e)}"
        
        elif any(word in text.lower() for word in ["delete", "apague", "remova"]):
            # Tenta identificar o arquivo no comando
            filename = None
            if "este arquivo" in text.lower() or "arquivo que criamos" in text.lower():
                filename = get_last_file()
                if not filename:
                    return "❌ Não encontrei nenhum arquivo no histórico recente."
            else:
                # Tenta extrair o nome do arquivo do comando
                words = text.lower().split()
                try:
                    idx = next(i for i, word in enumerate(words) 
                             if word in ["arquivo", "file"])
                    if idx + 1 < len(words):
                        filename = words[idx + 1]
                except StopIteration:
                    return "❌ Não consegui identificar qual arquivo você quer deletar."

            if filename:
                file_state.filename = filename
                file_state.state = "waiting_confirmation"
                file_state.action = "delete"
                filepath = get_safe_filepath(filename)
                if os.path.exists(filepath):
                    return f"🗑️ Deletar arquivo:\nLocal: {filepath}\nConfirma? (S/N): "
                else:
                    file_state.state = "idle"
                    return f"❌ Arquivo não encontrado em:\n{filepath}"
    
    elif file_state.state == "waiting_confirmation":
        file_state.state = "idle"
        if text.lower().strip() == "s":
            if file_state.action == "create":
                success, filepath = create_file(file_state.filename, file_state.content)
                if success:
                    return f"✅ Arquivo criado com sucesso!\nLocal: {filepath}"
                else:
                    return f"❌ Erro ao criar o arquivo '{file_state.filename}'."
            elif file_state.action == "delete":
                success = delete_file(file_state.filename)
                if success:
                    return f"✅ Arquivo deletado com sucesso!"
                else:
                    return f"❌ Erro ao deletar o arquivo '{file_state.filename}'."
        else:
            return "❌ Operação cancelada."
    
    return None

def handle_user_input(user_input):
    """Processa entrada do usuário com sistema de memória em camadas"""
    global groq_client, personality
    
    try:
        # Adiciona mensagem do usuário ao histórico
        add_message_to_history("user", user_input)
        
        # Verifica operações de arquivo (não precisa de IA)
        file_response = handle_file_operation(user_input)
        if file_response:
            add_message_to_history("assistant", file_response)
            return file_response
            
        # Processa com o modelo mantendo contexto inteligente
        if groq_client and personality:
            # Obtém contexto combinado (recente + histórico relevante)
            context = get_chat_context(user_input)
            
            # Se for comando simples, não precisa de contexto
            simple_commands = ["ajuda", "status", "limpar", "sair"]
            if any(cmd in user_input.lower() for cmd in simple_commands):
                prompt = user_input
            else:
                prompt = f"{context}\n\nUsuário: {user_input}" if context else user_input
            
            response = groq_client.generate_response(
                prompt=prompt,
                system=personality
            )
            
            # Adiciona resposta ao histórico de forma assíncrona
            threading.Thread(target=add_message_to_history,
                           args=("assistant", response)).start()
            
            return response
            
    except Exception as e:
        print(f"\033[91mErro ao processar mensagem: {str(e)}\033[0m")
        return "Desculpe, ocorreu um erro ao processar sua mensagem."

def main():
    init_db()  # Inicializa o banco de dados
    clear_screen()
    print_with_typing("👋 Olá! Eu sou o Nexus, seu assistente virtual com IA!")
    print_with_typing("Estou aqui para ajudar você com qualquer tarefa de programação ou sistema.")
    print_with_typing("Usando Groq com modelo Mixtral-8x7b")
    print_with_typing("Pode me dizer naturalmente o que precisa, ou digite 'ajuda' para ver comandos específicos.")
    print()

    # Cria pasta workspace se não existir
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    # Inicializa os clientes de IA
    groq_client = None
    prompt_manager = None
    personality = None

    try:
        print_with_typing("🔄 Inicializando Groq...")
        groq_client = GroqClient()
        prompt_manager = PromptManager()
        personality = prompt_manager.get_prompt('personality')
        if not personality:
            print("⚠️ Aviso: Personalidade não encontrada, usando padrão")
            personality = {
                "system": "Você é o Nexus, um assistente virtual amigável e proativo.",
                "template": "{input}"
            }
    except Exception as e:
        print(f"\033[91mErro ao inicializar IA:\033[0m {str(e)}")
        print("Continuando sem suporte a IA...")

    while True:
        try:
            print()  # Linha extra antes da entrada do usuário
            print("\033[96mVocê: ", end="")
            user_input = input().strip()  # Remove a cor do input
            print(f"\033[96m\033[3m{get_br_time()}\033[0m")  # Horário em itálico

            if not user_input:
                continue

            if user_input.lower() == 'sair':
                print()  # Linha extra antes da resposta
                print("\033[38;5;46mNexus: Até logo! Foi um prazer ajudar!")
                print(f"\033[38;5;46m\033[3m{get_br_time()}\033[0m")  # Horário em itálico
                break

            # Mostra "Nexus está digitando..." com animação
            print()  # Linha extra antes do "está digitando"
            print("\033[93mNexus está digitando\033[0m", end="")
            for _ in range(3):
                time.sleep(0.5)
                print(".", end="", flush=True)
            print("\r" + " "*30 + "\r", end="")

            response = ""
            if user_input.lower() == 'ajuda':
                response = (
                    "Estou aqui para ajudar! Você pode:\n\n"
                    "1. Falar naturalmente comigo sobre qualquer tarefa\n"
                    "2. Usar comandos específicos:\n\n"
                    "Comandos do Sistema:\n"
                    "- status: Mostra informações do sistema\n"
                    "- hora: Mostra a data e hora atual\n"
                    "- memoria: Mostra o uso de memória\n"
                    "- disco: Mostra o uso do disco\n"
                    "- limpar: Limpa a tela\n"
                    "- processos: Lista os processos ativos\n"
                    "- rede: Mostra informações de rede\n\n"
                    "Comandos de IA:\n"
                    "- codigo <descrição>: Gera código baseado na descrição\n"
                    "- explicar <código>: Explica o código fornecido\n"
                    "- melhorar <código>: Sugere melhorias para o código\n"
                    "- debug <código>: Ajuda a encontrar problemas no código\n"
                    "- projeto <descrição>: Cria estrutura de projeto\n"
                    "- revisar <código>: Faz revisão detalhada do código\n"
                    "- arquitetura <descrição>: Projeta arquitetura de sistema\n"
                    "- sistema <comando>: Ajuda com administração do sistema\n\n"
                    "Mas não se preocupe em decorar comandos, pode simplesmente\n"
                    "me dizer o que precisa que eu vou entender! 😊"
                )
            elif user_input.lower() == 'status':
                response = f"Sistema: {os.uname().sysname} {os.uname().release}\nHostname: {os.uname().nodename}"
            elif user_input.lower() == 'hora':
                now = datetime.now()
                response = f"Agora são {now.strftime('%H:%M:%S do dia %d/%m/%Y')}"
            elif user_input.lower() == 'memoria':
                with os.popen('free -h') as f:
                    response = f.read()
            elif user_input.lower() == 'disco':
                with os.popen('df -h /') as f:
                    response = f.read()
            elif user_input.lower() == 'limpar':
                clear_screen()
                continue
            elif user_input.lower() == 'processos':
                with os.popen('ps aux | head -6') as f:
                    response = f.read()
            elif user_input.lower() == 'rede':
                with os.popen('ip addr show') as f:
                    response = f.read()
            # Comandos de IA
            elif user_input.lower().startswith(('codigo ', 'projeto ', 'revisar ', 'arquitetura ', 'sistema ', 'explicar ', 'melhorar ', 'debug ')):
                if groq_client:
                    # Identifica o comando e obtém o prompt apropriado
                    cmd = user_input.split(' ')[0].lower()
                    content = user_input[len(cmd)+1:].strip()
                    
                    prompt_map = {
                        'codigo': 'code_assistant',
                        'projeto': 'file_creator',
                        'revisar': 'code_reviewer',
                        'arquitetura': 'project_architect',
                        'sistema': 'system_admin'
                    }
                    
                    if cmd in prompt_map:
                        prompt_name = prompt_map[cmd]
                        prompt = prompt_manager.get_prompt(prompt_name)
                        if prompt:
                            # Combina a personalidade com o prompt específico
                            system = personality['system'] + "\n\n" + prompt['system']
                            response = groq_client._generate_response(
                                prompt['template'].format(**{
                                    'instruction': content,
                                    'code': content,
                                    'project_description': content,
                                    'task': content
                                }),
                                system=system
                            )
                        else:
                            response = groq_client._generate_response(content, system=personality['system'])
                    else:
                        # Para comandos que não precisam de prompt específico
                        if cmd == 'explicar':
                            response = groq_client.explain_code(content)
                        elif cmd == 'melhorar':
                            response = groq_client.improve_code(content)
                        elif cmd == 'debug':
                            response = groq_client.debug_code(content)
                else:
                    response = "Desculpe, o suporte a IA não está disponível no momento."
            else:
                response = handle_user_input(user_input)
                
            # Mostra a resposta com efeito de digitação
            print(f"\033[38;5;46mNexus: ", end="")
            for char in response:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(0.01)
            print()  # Nova linha após a resposta
            print(f"\033[38;5;46m\033[3m{get_br_time()}\033[0m")  # Horário em itálico

        except KeyboardInterrupt:
            print("\n\033[92mNexus:\033[0m Até logo! Foi um prazer ajudar!")
            break
        except Exception as e:
            print(f"\033[91mErro:\033[0m {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro fatal: {e}")

class FileState:
    def __init__(self):
        self.filename = None
        self.content = None
        self.state = "idle"
        self.action = None

file_state = FileState()

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_with_typing(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def get_br_time():
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    return now.strftime("%H:%M:%S")

def is_safe_path(path):
    """Verifica se o caminho é seguro para escrita"""
    # Converte para caminho absoluto
    abs_path = os.path.abspath(path)
    # Verifica se não está tentando acessar diretório pai
    if '..' in path:
        return False
    # Verifica se o diretório pai existe
    parent_dir = os.path.dirname(abs_path)
    if not os.path.exists(parent_dir):
        return False
    # Verifica permissões de escrita
    return os.access(parent_dir, os.W_OK)

def get_safe_filepath(filename):
    """Retorna um caminho seguro para o arquivo"""
    # Se o caminho é absoluto ou relativo com diretórios
    if filename.startswith('/') or '/' in filename:
        abs_path = os.path.abspath(filename)
        if is_safe_path(abs_path):
            return abs_path
        else:
            raise ValueError(f"Caminho inválido ou sem permissão: {abs_path}")
    # Se é apenas um nome de arquivo, usa o workspace
    return os.path.join(WORKSPACE_DIR, filename)

def create_file(filename, content):
    try:
        filepath = get_safe_filepath(filename)
        # Cria diretórios se necessário
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        add_to_history(filepath, 'create')
        return True, filepath
    except Exception as e:
        print(f"\033[91mErro ao criar arquivo: {str(e)}\033[0m")
        return False, None

def delete_file(filename):
    try:
        filepath = get_safe_filepath(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            add_to_history(filepath, 'delete')
            return True
        return False
    except Exception as e:
        print(f"\033[91mErro ao deletar arquivo: {str(e)}\033[0m")
        return False

message_cache = MessageCache()
