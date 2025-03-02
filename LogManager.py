import csv
import os
import time
import base64
from typing import Dict, Any
from pathlib import Path
import re

class LogManager:
    def __init__(self, log_file: str):
        """
        初始化日志管理器
        
        Args:
            log_file: CSV日志文件路径
        """
        self.log_file = Path(log_file)
        self.photos_dir = self.log_file.parent / 'photos'
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保日志文件存在并包含表头
        self.fields = ['id', 'timestamp', 'session_id', 'client_id', 'operation', 'data']
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()
        
        # 获取当前最大id
        self.current_id = self._get_max_id()
    
    def _get_max_id(self) -> int:
        """获取当前最大id"""
        try:
            if not self.log_file.exists():
                return 0
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                max_id = 0
                for row in reader:
                    if row['id'].isdigit():
                        max_id = max(max_id, int(row['id']))
                return max_id
        except Exception:
            return 0
    
    def _is_base64_image(self, data: str) -> bool:
        """
        检查字符串是否为base64编码的图片
        """
        try:
            # 检查是否符合base64格式
            if not re.match('^data:image/jpeg;base64,', data):
                return False
            
            # 尝试解码
            image_data = base64.b64decode(data.split(',')[1])
            # 检查JPG文件头
            return image_data.startswith(b'\xff\xd8')
        except Exception:
            return False
    
    def _save_photo(self, photo_id: int, base64_data: str) -> None:
        """
        保存base64图片到文件
        
        Args:
            photo_id: 图片ID（同日志ID）
            base64_data: base64编码的图片数据
        """
        try:
            # 移除base64头部
            image_data = base64.b64decode(base64_data.split(',')[1])
            
            # 保存文件
            photo_path = self.photos_dir / f"{photo_id}.jpg"
            with open(photo_path, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            raise Exception(f"Failed to save photo: {e}")
    
    def insert(self, session_id: int, client_id: str, operation: str, data: str) -> int:
        """
        插入一条日志记录
        
        Args:
            session_id: 会话ID
            client_id: 客户端ID
            operation: 操作类型
            data: 数据内容（文本或base64图片）
        
        Returns:
            插入记录的ID
        """
        try:
            # 生成新ID
            self.current_id += 1
            
            # 处理图片数据
            if self._is_base64_image(data):
                self._save_photo(self.current_id, data)
                data = "@photo"  # 替换为标识符
            
            # 准备日志记录
            log_entry = {
                'id': self.current_id,
                'timestamp': int(time.time() * 1000),  # 毫秒级时间戳
                'session_id': session_id,
                'client_id': client_id,
                'operation': operation,
                'data': data
            }
            
            # 写入CSV文件
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writerow(log_entry)
            
            return self.current_id
            
        except Exception as e:
            raise Exception(f"Failed to insert log: {e}")