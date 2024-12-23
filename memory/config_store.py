import json
import os
import socket
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

class ConfigStore:
    def __init__(self, persist_directory: str = "./config_db"):
        """
        Inicializa o armazenamento de configurações
        
        Args:
            persist_directory: Diretório para armazenar as configurações
        """
        self.persist_directory = persist_directory
        self.config_file = os.path.join(persist_directory, "system_config.json")
        self._ensure_directory()
        self.config = self._load_config()
        
    def _ensure_directory(self):
        """Garante que o diretório de persistência existe"""
        os.makedirs(self.persist_directory, exist_ok=True)
        
    def _load_config(self) -> Dict:
        """Carrega configurações do arquivo"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "services": {},
            "ports": {},
            "dependencies": {},
            "environment": {},
            "metadata": {
                "last_updated": None,
                "version": "1.0"
            }
        }
        
    def _save_config(self):
        """Salva configurações no arquivo"""
        self.config["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def _check_port_in_use_system(self, port: int) -> bool:
        """
        Verifica se a porta está em uso no sistema operacional
        
        Args:
            port: Número da porta a verificar
            
        Returns:
            bool: True se a porta está em uso
        """
        try:
            # Tenta criar um socket TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            # Se result for 0, porta está em uso
            if result == 0:
                return True
                
            # Tenta criar um socket UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            return result == 0
        except:
            # Em caso de erro, assume que a porta pode estar em uso
            return True
            
    def is_port_available(self, port: int, check_system: bool = True) -> Tuple[bool, str]:
        """
        Verifica se uma porta está disponível, tanto no registro quanto no sistema
        
        Args:
            port: Número da porta
            check_system: Se deve verificar também no sistema operacional
            
        Returns:
            tuple: (disponível, motivo)
        """
        # Verifica no registro
        if str(port) in self.config["ports"]:
            service = self.config["ports"][str(port)]["service"]
            return False, f"Porta {port} já registrada para o serviço '{service}'"
            
        # Verifica no sistema se solicitado
        if check_system and self._check_port_in_use_system(port):
            return False, f"Porta {port} está em uso no sistema operacional"
            
        return True, "Porta disponível"
        
    def register_port(self, port: int, service: str, protocol: str = "tcp", force: bool = False) -> Tuple[bool, str]:
        """
        Registra uma porta em uso, com verificações de segurança
        
        Args:
            port: Número da porta
            service: Nome do serviço
            protocol: Protocolo (tcp/udp)
            force: Se deve forçar o registro mesmo se a porta estiver em uso
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        # Verifica disponibilidade
        available, reason = self.is_port_available(port)
        
        if not available and not force:
            return False, f"Não foi possível registrar a porta: {reason}"
            
        # Registra a porta
        self.config["ports"][str(port)] = {
            "service": service,
            "protocol": protocol,
            "registered_at": datetime.now().isoformat(),
            "status": "in_use",
            "last_verified": datetime.now().isoformat()
        }
        self._save_config()
        
        return True, f"Porta {port} registrada com sucesso para '{service}'"
        
    def verify_service_exists(self, name: str) -> Tuple[bool, str]:
        """
        Verifica se um serviço já existe
        
        Args:
            name: Nome do serviço
            
        Returns:
            tuple: (existe, mensagem)
        """
        if name in self.config["services"]:
            return True, f"Serviço '{name}' já existe"
        return False, "Serviço não encontrado"
        
    def register_service(self, name: str, config: Dict, force: bool = False) -> Tuple[bool, str]:
        """
        Registra um serviço com verificações de segurança
        
        Args:
            name: Nome do serviço
            config: Configurações
            force: Se deve forçar o registro mesmo se já existir
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        # Verifica se já existe
        exists, msg = self.verify_service_exists(name)
        if exists and not force:
            return False, f"Não foi possível registrar: {msg}"
            
        # Verifica porta se especificada
        if "port" in config:
            available, reason = self.is_port_available(config["port"])
            if not available and not force:
                return False, f"Não foi possível registrar: {reason}"
                
        # Registra o serviço
        self.config["services"][name] = {
            "config": config,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "last_verified": datetime.now().isoformat()
        }
        self._save_config()
        
        return True, f"Serviço '{name}' registrado com sucesso"
        
    def stop_service(self, name: str) -> Tuple[bool, str]:
        """
        NUNCA para um serviço automaticamente, apenas marca para revisão
        
        Args:
            name: Nome do serviço
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if name not in self.config["services"]:
            return False, f"Serviço '{name}' não encontrado"
            
        # Marca para revisão em vez de parar
        self.config["services"][name]["status"] = "needs_review"
        self.config["services"][name]["review_reason"] = "Solicitada parada do serviço"
        self._save_config()
        
        return False, f"ATENÇÃO: Serviço '{name}' marcado para revisão. Por favor, verifique manualmente se é seguro parar este serviço."
        
    def get_next_available_port(self, start_port: int = 3000, preferred_ports: Optional[List[int]] = None) -> Tuple[Optional[int], str]:
        """
        Encontra próxima porta disponível com verificações de segurança
        
        Args:
            start_port: Porta inicial para busca
            preferred_ports: Lista de portas preferenciais para tentar primeiro
            
        Returns:
            tuple: (porta ou None, mensagem)
        """
        # Tenta primeiro as portas preferenciais
        if preferred_ports:
            for port in preferred_ports:
                available, reason = self.is_port_available(port)
                if available:
                    return port, f"Porta preferencial {port} está disponível"
                    
        # Busca a próxima porta disponível
        current_port = start_port
        while current_port < 65535:
            available, reason = self.is_port_available(current_port)
            if available:
                return current_port, f"Próxima porta disponível: {current_port}"
            current_port += 1
            
        return None, "Não foi possível encontrar uma porta disponível"
        
    def verify_system_ports(self) -> List[Dict]:
        """
        Verifica o estado atual de todas as portas registradas
        
        Returns:
            List[Dict]: Lista de portas que precisam de atenção
        """
        needs_attention = []
        
        for port, info in self.config["ports"].items():
            if info["status"] != "in_use":
                continue
                
            # Verifica se a porta ainda está em uso no sistema
            system_check = self._check_port_in_use_system(int(port))
            
            if not system_check:
                needs_attention.append({
                    "port": port,
                    "service": info["service"],
                    "issue": "Porta registrada mas não está em uso no sistema"
                })
                
        return needs_attention
        
    def register_dependency(self, name: str, version: str, service: str) -> None:
        """
        Registra uma dependência
        
        Args:
            name: Nome da dependência
            version: Versão
            service: Serviço que usa esta dependência
        """
        if name not in self.config["dependencies"]:
            self.config["dependencies"][name] = []
            
        self.config["dependencies"][name].append({
            "version": version,
            "service": service,
            "registered_at": datetime.now().isoformat()
        })
        self._save_config()
        
    def set_env_var(self, name: str, description: str, service: str) -> None:
        """
        Registra uma variável de ambiente (sem o valor por segurança)
        
        Args:
            name: Nome da variável
            description: Descrição do propósito
            service: Serviço que usa esta variável
        """
        self.config["environment"][name] = {
            "description": description,
            "service": service,
            "registered_at": datetime.now().isoformat()
        }
        self._save_config()
        
    def get_service_config(self, name: str) -> Optional[Dict]:
        """Obtém configuração de um serviço"""
        return self.config["services"].get(name)
        
    def get_service_ports(self, service: str) -> List[int]:
        """Lista todas as portas usadas por um serviço"""
        return [
            int(port) for port, info in self.config["ports"].items()
            if info["service"] == service and info["status"] == "in_use"
        ]
        
    def get_service_dependencies(self, service: str) -> List[Dict]:
        """Lista todas as dependências de um serviço"""
        deps = []
        for dep_name, versions in self.config["dependencies"].items():
            for version in versions:
                if version["service"] == service:
                    deps.append({
                        "name": dep_name,
                        "version": version["version"]
                    })
        return deps
        
    def get_system_overview(self) -> Dict:
        """Retorna visão geral do sistema"""
        return {
            "active_services": len(self.config["services"]),
            "ports_in_use": len([p for p, info in self.config["ports"].items() 
                                if info["status"] == "in_use"]),
            "total_dependencies": len(self.config["dependencies"]),
            "environment_vars": len(self.config["environment"]),
            "last_updated": self.config["metadata"]["last_updated"]
        }
