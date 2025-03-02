import os
import json
import threading
from typing import Dict, List, Any

class SessionManager:
    def __init__(self, base_path: str = "./"):
        # 初始化基础路径
        self.base_path = base_path
        self.sessions_path = os.path.join(base_path, "sessions")
        self.id_file = os.path.join(base_path, "session_id.txt")
        
        # 创建必要的目录
        if not os.path.exists(self.sessions_path):
            os.makedirs(self.sessions_path)
            
        # 初始化session ID计数器
        if os.path.exists(self.id_file):
            with open(self.id_file, 'r') as f:
                self.current_id = int(f.read().strip() or "0")
        else:
            self.current_id = 0
            
        # 初始化会话字典和锁
        self.sessions: Dict[str, int] = {}  # client_id -> session_id
        self.lock = threading.Lock()
        
    def _get_next_session_id(self) -> int:
        """获取下一个可用的session ID"""
        with self.lock:
            self.current_id += 1
            with open(self.id_file, 'w') as f:
                f.write(str(self.current_id))
            return self.current_id
            
    def create_session(self, client_id: str) -> int:
        """创建新的会话"""
        if client_id in self.sessions:
            raise ValueError(f"Client {client_id} already has an active session")
            
        session_id = self._get_next_session_id()
        self.sessions[client_id] = session_id
        
        # 创建session文件
        session_file = os.path.join(self.sessions_path, f"{session_id}.json")
        with open(session_file, 'w') as f:
            json.dump([], f)
            
        return session_id
        
    def close_session(self, client_id: str) -> None:
        """关闭会话"""
        if client_id not in self.sessions:
            raise ValueError(f"No active session for client {client_id}")
            
        del self.sessions[client_id]
            
    def add_record(self, client_id: str, record: Any) -> None:
        """添加记录到会话"""
        if client_id not in self.sessions:
            raise ValueError(f"No active session for client {client_id}")
            
        session_id = self.sessions[client_id]
        session_file = os.path.join(self.sessions_path, f"{session_id}.json")
        
        with self.lock:
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    records = json.load(f)
            else:
                records = []
                
            records.append(record)
            
            with open(session_file, 'w') as f:
                json.dump(records, f)

    def add_record_session(self, session_id: int, record: Any) -> None:
        """添加记录到会话"""
        session_file = os.path.join(self.sessions_path, f"{session_id}.json")
        
        with self.lock:
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    records = json.load(f)
            else:
                records = []
                
            records.append(record)
            
            with open(session_file, 'w') as f:
                json.dump(records, f, indent=4)
                
    def get_records(self, session_id: int) -> List[Any]:
        """获取会话的所有记录"""
        with self.lock:
            session_file = os.path.join(self.sessions_path, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return []
                
            with open(session_file, 'r') as f:
                return json.load(f)
        
    def get_session_id(self, client_id: str) -> int:
        """获取客户端的会话ID"""
        return self.sessions.get(client_id, None)
    
    def get_client_id(self, session_id: int) -> str:
        """获取会话的客户端ID"""
        for client_id, s_id in self.sessions.items():
            if s_id == session_id:
                return client_id
        return None