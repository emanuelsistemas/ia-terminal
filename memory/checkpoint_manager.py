import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class CheckpointManager:
    def __init__(self, base_directory: str = "./checkpoints"):
        """
        Gerencia checkpoints do sistema
        
        Args:
            base_directory: Diretório base para armazenar checkpoints
        """
        self.base_directory = base_directory
        self.checkpoints_file = os.path.join(base_directory, "checkpoints.json")
        self.data_directory = os.path.join(base_directory, "data")
        self._ensure_directories()
        self.checkpoints = self._load_checkpoints()
        
    def _ensure_directories(self):
        """Garante que os diretórios necessários existem"""
        os.makedirs(self.base_directory, exist_ok=True)
        os.makedirs(self.data_directory, exist_ok=True)
        
    def _load_checkpoints(self) -> Dict:
        """Carrega registro de checkpoints"""
        if os.path.exists(self.checkpoints_file):
            with open(self.checkpoints_file, 'r') as f:
                return json.load(f)
        return {
            "checkpoints": [],
            "current": None,
            "metadata": {
                "last_checkpoint": None,
                "version": "1.0"
            }
        }
        
    def _save_checkpoints(self):
        """Salva registro de checkpoints"""
        with open(self.checkpoints_file, 'w') as f:
            json.dump(self.checkpoints, f, indent=2)
            
    def _generate_checkpoint_id(self, message: str) -> str:
        """Gera ID único para o checkpoint"""
        timestamp = datetime.now().isoformat()
        content = f"{timestamp}-{message}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
        
    def create_checkpoint(self, message: str, config_store: object, 
                         message_cache: object) -> str:
        """
        Cria um novo checkpoint do sistema
        
        Args:
            message: Mensagem descritiva do checkpoint
            config_store: Instância do ConfigStore
            message_cache: Instância do MessageCache
            
        Returns:
            str: ID do checkpoint criado
        """
        checkpoint_id = self._generate_checkpoint_id(message)
        checkpoint_dir = os.path.join(self.data_directory, checkpoint_id)
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Salva configurações
        config_file = os.path.join(checkpoint_dir, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config_store.config, f, indent=2)
            
        # Salva cache de mensagens
        messages_file = os.path.join(checkpoint_dir, "messages.json")
        with open(messages_file, 'w') as f:
            json.dump([
                {"role": role, "content": content}
                for role, content in message_cache.messages
            ], f, indent=2)
            
        # Copia banco de dados Chroma
        if os.path.exists(config_store.persist_directory):
            chroma_backup = os.path.join(checkpoint_dir, "chroma_db")
            shutil.copytree(config_store.persist_directory, chroma_backup)
            
        # Registra checkpoint
        checkpoint_data = {
            "id": checkpoint_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "files": {
                "config": "config.json",
                "messages": "messages.json",
                "chroma": "chroma_db"
            }
        }
        
        self.checkpoints["checkpoints"].append(checkpoint_data)
        self.checkpoints["current"] = checkpoint_id
        self.checkpoints["metadata"]["last_checkpoint"] = datetime.now().isoformat()
        self._save_checkpoints()
        
        return checkpoint_id
        
    def restore_checkpoint(self, checkpoint_id: str, config_store: object,
                          message_cache: object) -> bool:
        """
        Restaura o sistema para um checkpoint específico
        
        Args:
            checkpoint_id: ID do checkpoint
            config_store: Instância do ConfigStore
            message_cache: Instância do MessageCache
            
        Returns:
            bool: True se restaurado com sucesso
        """
        # Verifica se checkpoint existe
        checkpoint_dir = os.path.join(self.data_directory, checkpoint_id)
        if not os.path.exists(checkpoint_dir):
            return False
            
        try:
            # Restaura configurações
            config_file = os.path.join(checkpoint_dir, "config.json")
            with open(config_file, 'r') as f:
                config_store.config = json.load(f)
            config_store._save_config()
            
            # Restaura cache de mensagens
            messages_file = os.path.join(checkpoint_dir, "messages.json")
            with open(messages_file, 'r') as f:
                messages = json.load(f)
                message_cache.messages = [
                    (msg["role"], msg["content"])
                    for msg in messages
                ]
                
            # Restaura banco de dados Chroma
            chroma_backup = os.path.join(checkpoint_dir, "chroma_db")
            if os.path.exists(chroma_backup):
                if os.path.exists(config_store.persist_directory):
                    shutil.rmtree(config_store.persist_directory)
                shutil.copytree(chroma_backup, config_store.persist_directory)
                
            # Atualiza checkpoint atual
            self.checkpoints["current"] = checkpoint_id
            self._save_checkpoints()
            
            return True
            
        except Exception as e:
            print(f"Erro ao restaurar checkpoint: {str(e)}")
            return False
            
    def list_checkpoints(self, limit: int = 10) -> List[Dict]:
        """
        Lista checkpoints disponíveis
        
        Args:
            limit: Número máximo de checkpoints para retornar
            
        Returns:
            List[Dict]: Lista de checkpoints
        """
        checkpoints = self.checkpoints["checkpoints"]
        # Ordena por timestamp, mais recente primeiro
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        return checkpoints[:limit]
        
    def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict]:
        """Obtém informações de um checkpoint específico"""
        for checkpoint in self.checkpoints["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                return checkpoint
        return None
        
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Remove um checkpoint
        
        Args:
            checkpoint_id: ID do checkpoint
            
        Returns:
            bool: True se removido com sucesso
        """
        checkpoint_dir = os.path.join(self.data_directory, checkpoint_id)
        if os.path.exists(checkpoint_dir):
            shutil.rmtree(checkpoint_dir)
            
        # Remove do registro
        self.checkpoints["checkpoints"] = [
            cp for cp in self.checkpoints["checkpoints"]
            if cp["id"] != checkpoint_id
        ]
        
        if self.checkpoints["current"] == checkpoint_id:
            self.checkpoints["current"] = None
            
        self._save_checkpoints()
        return True
        
    def cleanup_old_checkpoints(self, max_checkpoints: int = 50):
        """
        Remove checkpoints antigos mantendo apenas os mais recentes
        
        Args:
            max_checkpoints: Número máximo de checkpoints para manter
        """
        checkpoints = self.checkpoints["checkpoints"]
        if len(checkpoints) <= max_checkpoints:
            return
            
        # Ordena por timestamp
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Remove os mais antigos
        for checkpoint in checkpoints[max_checkpoints:]:
            self.delete_checkpoint(checkpoint["id"])
