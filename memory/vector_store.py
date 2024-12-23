import chromadb
from chromadb.config import Settings
import os
from datetime import datetime
import json

class VectorMemory:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Inicializa o cliente Chroma com persistência
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            chroma_db_impl="duckdb+parquet",
            anonymized_telemetry=False
        ))
        
        # Cria ou recupera a coleção de mensagens
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Debug: lista todas as mensagens ao inicializar
        try:
            all_messages = self.collection.get()
            with open("chroma_debug.log", "a") as f:
                f.write(f"\n=== Inicializando VectorMemory ===\n")
                f.write(f"Diretório: {persist_directory}\n")
                f.write(f"Total de mensagens: {len(all_messages['ids']) if all_messages['ids'] else 0}\n")
                if all_messages['ids']:
                    for i, (doc, meta, id) in enumerate(zip(all_messages['documents'], all_messages['metadatas'], all_messages['ids'])):
                        f.write(f"{i+1}. ID: {id}, Role: {meta['role']}, Content: {doc}\n")
                f.write("\n---\n")
        except Exception as e:
            with open("chroma_errors.log", "a") as f:
                f.write(f"{datetime.now()}: Erro ao inicializar: {str(e)}\n")

    def add_message(self, role, content, metadata=None):
        """Adiciona uma mensagem ao Chroma"""
        try:
            if metadata is None:
                metadata = {}
                
            # Adiciona timestamp e role aos metadados
            metadata.update({
                "timestamp": datetime.now().isoformat(),
                "role": role
            })
            
            # Adiciona ao Chroma
            msg_id = f"msg_{datetime.now().timestamp()}"
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[msg_id]
            )
            
            # Debug: verifica se a mensagem foi salva
            with open("chroma_debug.log", "a") as f:
                f.write(f"\nAdicionando mensagem: {msg_id}\n")
                f.write(f"Role: {role}\n")
                f.write(f"Content: {content}\n")
                
                # Lista todas as mensagens
                all_messages = self.collection.get()
                f.write(f"\nTotal de mensagens: {len(all_messages['ids']) if all_messages['ids'] else 0}\n")
                if all_messages['ids']:
                    for i, (doc, meta, id) in enumerate(zip(all_messages['documents'], all_messages['metadatas'], all_messages['ids'])):
                        f.write(f"{i+1}. ID: {id}, Role: {meta['role']}, Content: {doc}\n")
                f.write("\n---\n")
                
        except Exception as e:
            with open("chroma_errors.log", "a") as f:
                f.write(f"{datetime.now()}: Erro ao adicionar mensagem: {str(e)}\n")

    def search_context(self, query, n_results=5):
        """Busca mensagens relevantes para o contexto atual"""
        try:
            # Debug: lista todas as mensagens antes da busca
            with open("chroma_debug.log", "a") as f:
                f.write(f"\nBuscando contexto para: {query}\n")
                all_messages = self.collection.get()
                f.write(f"Total de mensagens antes da busca: {len(all_messages['ids']) if all_messages['ids'] else 0}\n")
            
            # Primeiro tenta buscar mensagens semanticamente similares
            similar_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, max(1, len(all_messages['ids']) if all_messages['ids'] else 0))
            )
            
            # Debug: resultados da busca
            with open("chroma_debug.log", "a") as f:
                f.write(f"Resultados encontrados: {len(similar_results['documents'][0]) if similar_results['documents'] and similar_results['documents'][0] else 0}\n")
            
            # Formata as mensagens encontradas
            messages = []
            if similar_results['documents'] and similar_results['documents'][0]:
                for doc, meta in zip(similar_results['documents'][0], similar_results['metadatas'][0]):
                    role = meta['role']
                    prefix = "Usuário: " if role == "user" else "Assistente: "
                    messages.append(f"{prefix}{doc}")
            
            # Debug: mensagens retornadas
            with open("chroma_debug.log", "a") as f:
                f.write(f"Mensagens retornadas: {len(messages)}\n")
                for msg in messages:
                    f.write(f"  {msg}\n")
                f.write("\n---\n")
            
            return messages
            
        except Exception as e:
            with open("chroma_errors.log", "a") as f:
                f.write(f"{datetime.now()}: Erro na busca: {str(e)}\n")
            return []
    
    def archive_messages(self, messages):
        """Arquiva mensagens antigas no Chroma"""
        for role, content in messages:
            self.add_message(role, content)
    
    def clear(self):
        """Limpa todas as mensagens do Chroma"""
        self.client.delete_collection("chat_memory")
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"hnsw:space": "cosine"}
        )
