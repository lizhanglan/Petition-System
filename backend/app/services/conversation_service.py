"""
对话上下文管理服务

功能：
1. 管理用户的对话历史
2. 存储和检索对话上下文
3. 支持对话清除
4. 支持文件引用
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class ConversationService:
    """对话上下文管理服务"""
    
    def __init__(self):
        # 使用内存存储（生产环境应使用 Redis）
        self._conversations: Dict[str, List[Dict]] = {}
        self._file_references: Dict[str, List[int]] = {}  # 对话ID -> 文件ID列表
        self._last_activity: Dict[str, datetime] = {}
        
        # 配置
        self.max_history_length = 50  # 最多保留50轮对话
        self.context_window = 20  # 发送给 AI 的上下文窗口（最近20轮）
        self.session_timeout = timedelta(hours=2)  # 2小时无活动自动清除
    
    def _get_conversation_key(self, user_id: int, session_id: Optional[str] = None) -> str:
        """生成对话键"""
        if session_id:
            return f"conv:{user_id}:{session_id}"
        return f"conv:{user_id}:default"
    
    def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        添加消息到对话历史
        
        Args:
            user_id: 用户ID
            role: 角色（user/assistant/system）
            content: 消息内容
            session_id: 会话ID（可选）
            metadata: 元数据（可选）
            
        Returns:
            消息对象
        """
        key = self._get_conversation_key(user_id, session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        if key not in self._conversations:
            self._conversations[key] = []
        
        self._conversations[key].append(message)
        
        # 限制历史长度
        if len(self._conversations[key]) > self.max_history_length:
            self._conversations[key] = self._conversations[key][-self.max_history_length:]
        
        # 更新活动时间
        self._last_activity[key] = datetime.now()
        
        print(f"[Conversation] Added {role} message to {key}, total: {len(self._conversations[key])}")
        
        return message
    
    def get_history(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            limit: 限制返回数量（可选）
            
        Returns:
            消息列表
        """
        key = self._get_conversation_key(user_id, session_id)
        
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        history = self._conversations.get(key, [])
        
        if limit:
            return history[-limit:]
        
        return history
    
    def get_context_for_ai(
        self,
        user_id: int,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        获取用于 AI 的上下文（最近N轮对话）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            
        Returns:
            上下文消息列表
        """
        history = self.get_history(user_id, session_id)
        
        # 只返回最近的对话
        context = history[-self.context_window:]
        
        # 只保留 role 和 content 字段
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in context
        ]
    
    def clear_history(
        self,
        user_id: int,
        session_id: Optional[str] = None
    ) -> bool:
        """
        清除对话历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            
        Returns:
            是否成功
        """
        key = self._get_conversation_key(user_id, session_id)
        
        if key in self._conversations:
            del self._conversations[key]
            print(f"[Conversation] Cleared history for {key}")
        
        if key in self._file_references:
            del self._file_references[key]
        
        if key in self._last_activity:
            del self._last_activity[key]
        
        return True
    
    def add_file_reference(
        self,
        user_id: int,
        file_id: int,
        session_id: Optional[str] = None
    ):
        """
        添加文件引用
        
        Args:
            user_id: 用户ID
            file_id: 文件ID
            session_id: 会话ID（可选）
        """
        key = self._get_conversation_key(user_id, session_id)
        
        if key not in self._file_references:
            self._file_references[key] = []
        
        if file_id not in self._file_references[key]:
            self._file_references[key].append(file_id)
            print(f"[Conversation] Added file reference {file_id} to {key}")
    
    def get_file_references(
        self,
        user_id: int,
        session_id: Optional[str] = None
    ) -> List[int]:
        """
        获取文件引用列表
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            
        Returns:
            文件ID列表
        """
        key = self._get_conversation_key(user_id, session_id)
        return self._file_references.get(key, [])
    
    def _cleanup_expired_sessions(self):
        """清理过期的会话"""
        now = datetime.now()
        expired_keys = []
        
        for key, last_time in self._last_activity.items():
            if now - last_time > self.session_timeout:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self._conversations:
                del self._conversations[key]
            if key in self._file_references:
                del self._file_references[key]
            if key in self._last_activity:
                del self._last_activity[key]
            
            print(f"[Conversation] Cleaned up expired session: {key}")
    
    def get_session_info(
        self,
        user_id: int,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        获取会话信息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            
        Returns:
            会话信息
        """
        key = self._get_conversation_key(user_id, session_id)
        
        history = self._conversations.get(key, [])
        file_refs = self._file_references.get(key, [])
        last_activity = self._last_activity.get(key)
        
        return {
            "session_key": key,
            "message_count": len(history),
            "file_reference_count": len(file_refs),
            "last_activity": last_activity.isoformat() if last_activity else None,
            "is_active": key in self._conversations
        }


# 全局单例
conversation_service = ConversationService()
