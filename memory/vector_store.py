import chromadb
from chromadb.config import Settings
import os
from datetime import datetime
import json

class VectorMemory:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Inicializa o cliente Chroma
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Cria ou recupera a coleção de mensagens
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_message(self, role, content, metadata=None):
        """Adiciona uma mensagem ao Chroma"""
        if metadata is None:
            metadata = {}
            
        # Adiciona timestamp e role aos metadados
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "role": role
        })
        
        # Adiciona ao Chroma
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[f"msg_{datetime.now().timestamp()}"]
        )
    
    def search_context(self, query, n_results=5):
        """Busca mensagens relevantes para o contexto atual"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Formata as mensagens encontradas
        messages = []
        if results and results['documents']:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                role = meta['role']
                prefix = "Usuário: " if role == "user" else "Assistente: "
                messages.append(f"{prefix}{doc}")
        
        return messages
    
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
