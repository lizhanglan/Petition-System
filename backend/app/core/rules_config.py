"""
规则配置管理器

负责加载、验证和管理规则配置文件，支持热重载
"""
import json
import os
import asyncio
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from app.models.validation import RulesConfig, Rule

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, manager: 'RulesConfigManager'):
        self.manager = manager
        self.last_modified = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if isinstance(event, FileModifiedEvent):
            # 防止重复触发
            import time
            current_time = time.time()
            if current_time - self.last_modified < 1:
                return
            self.last_modified = current_time
            
            if Path(event.src_path) == self.manager.config_path:
                logger.info(f"检测到配置文件变更: {event.src_path}")
                # 异步重载配置
                asyncio.create_task(self.manager.reload_config())


class RulesConfigManager:
    """规则配置管理器"""
    
    def __init__(self, config_path: str):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.current_config: Optional[RulesConfig] = None
        self.previous_valid_config: Optional[RulesConfig] = None
        self.observer: Optional[Observer] = None
        self.watching = False
        
    async def load_config(self) -> Optional[RulesConfig]:
        """
        加载配置文件
        
        Returns:
            配置对象，如果加载失败返回 None
        """
        try:
            if not self.config_path.exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置
            config = RulesConfig(**config_data)
            is_valid, error_msg = config.validate_rules()
            
            if not is_valid:
                logger.error(f"配置验证失败: {error_msg}")
                return None
            
            # 保存当前有效配置
            if self.current_config:
                self.previous_valid_config = self.current_config
            self.current_config = config
            
            logger.info(f"成功加载配置文件: {self.config_path}, 规则数量: {len(config.rules)}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            return None
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return None
    
    async def reload_config(self) -> bool:
        """
        重新加载配置文件
        
        Returns:
            是否成功重载
        """
        logger.info("开始重新加载配置文件...")
        new_config = await self.load_config()
        
        if new_config is None:
            logger.warning("配置重载失败，继续使用上一个有效配置")
            # 恢复到上一个有效配置
            if self.previous_valid_config:
                self.current_config = self.previous_valid_config
            return False
        
        logger.info("配置重载成功")
        return True
    
    def validate_config(self, config_data: dict) -> Tuple[bool, Optional[str]]:
        """
        验证配置数据
        
        Args:
            config_data: 配置数据字典
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            config = RulesConfig(**config_data)
            return config.validate_rules()
        except Exception as e:
            return False, f"配置格式错误: {str(e)}"
    
    def get_enabled_rules(self) -> List[Rule]:
        """
        获取所有启用的规则
        
        Returns:
            启用的规则列表，按优先级降序排序
        """
        if not self.current_config:
            return []
        
        enabled_rules = [rule for rule in self.current_config.rules if rule.enabled]
        # 按优先级降序排序
        enabled_rules.sort(key=lambda r: r.priority, reverse=True)
        return enabled_rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """
        根据ID获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则对象，如果不存在返回 None
        """
        if not self.current_config:
            return None
        
        for rule in self.current_config.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_rule_templates(self) -> List[Dict[str, Any]]:
        """
        获取规则模板
        
        Returns:
            规则模板列表
        """
        if not self.current_config:
            return []
        return self.current_config.templates
    
    def toggle_rule(self, rule_id: str, enabled: bool) -> bool:
        """
        启用或禁用规则
        
        Args:
            rule_id: 规则ID
            enabled: 是否启用
            
        Returns:
            是否成功
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            logger.warning(f"规则不存在: {rule_id}")
            return False
        
        rule.enabled = enabled
        logger.info(f"规则 {rule_id} 已{'启用' if enabled else '禁用'}")
        return True
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息
        
        Returns:
            配置信息字典
        """
        if not self.current_config:
            return {
                "loaded": False,
                "version": None,
                "total_rules": 0,
                "enabled_rules": 0
            }
        
        enabled_count = len([r for r in self.current_config.rules if r.enabled])
        
        return {
            "loaded": True,
            "version": self.current_config.version,
            "total_rules": len(self.current_config.rules),
            "enabled_rules": enabled_count,
            "config_path": str(self.config_path)
        }
    
    async def start_watching(self) -> None:
        """开始监控配置文件变更"""
        if self.watching:
            logger.warning("配置文件监控已经启动")
            return
        
        try:
            event_handler = ConfigFileHandler(self)
            self.observer = Observer()
            
            # 监控配置文件所在目录
            watch_dir = self.config_path.parent
            self.observer.schedule(event_handler, str(watch_dir), recursive=False)
            self.observer.start()
            
            self.watching = True
            logger.info(f"开始监控配置文件: {self.config_path}")
            
        except Exception as e:
            logger.error(f"启动配置文件监控失败: {e}")
    
    def stop_watching(self) -> None:
        """停止监控配置文件变更"""
        if self.observer and self.watching:
            self.observer.stop()
            self.observer.join()
            self.watching = False
            logger.info("停止监控配置文件")
