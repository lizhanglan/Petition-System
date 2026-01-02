"""
本地规则引擎

负责使用本地规则进行文档验证，作为 AI 服务的降级方案
"""
import time
from typing import Dict, Any, Optional
import logging

from app.core.rules_config import RulesConfigManager
from app.services.rule_executor import RuleExecutor
from app.models.validation import ValidationResult, ValidationError

logger = logging.getLogger(__name__)


class LocalRulesEngine:
    """本地规则引擎"""
    
    def __init__(self, config_manager: RulesConfigManager):
        """
        初始化本地规则引擎
        
        Args:
            config_manager: 规则配置管理器
        """
        self.config_manager = config_manager
        self.executor = RuleExecutor()
        self.validation_count = 0
        self.total_execution_time = 0.0
    
    async def validate_document(self, content: str, metadata: Dict[str, Any] = None) -> ValidationResult:
        """
        验证文档
        
        Args:
            content: 文档内容
            metadata: 元数据（可能包含结构化数据）
            
        Returns:
            验证结果
        """
        start_time = time.time()
        
        if metadata is None:
            metadata = {}
        
        # 获取启用的规则
        rules = self.config_manager.get_enabled_rules()
        
        if not rules:
            logger.warning("没有启用的规则")
            return ValidationResult(
                success=True,
                errors=[],
                summary="没有启用的规则，跳过验证",
                execution_time=0.0,
                rules_executed=0
            )
        
        logger.info(f"开始本地规则验证，规则数量: {len(rules)}")
        
        # 执行规则
        try:
            results = await self.executor.execute_rules(rules, content, metadata)
        except Exception as e:
            logger.error(f"规则执行失败: {e}")
            execution_time = time.time() - start_time
            return ValidationResult(
                success=False,
                errors=[ValidationError(
                    type="content_error",
                    level="error",
                    description=f"规则执行失败: {str(e)}",
                    suggestion="请检查文档格式或联系管理员"
                )],
                summary="规则执行失败",
                execution_time=execution_time,
                rules_executed=0
            )
        
        # 收集所有错误
        all_errors = []
        for result in results:
            all_errors.extend(result.errors)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 更新统计信息
        self.validation_count += 1
        self.total_execution_time += execution_time
        
        # 生成摘要
        if not all_errors:
            summary = "文档验证通过，未发现问题"
            success = True
        else:
            error_count = len(all_errors)
            error_levels = {}
            for error in all_errors:
                level = error.level
                error_levels[level] = error_levels.get(level, 0) + 1
            
            summary_parts = [f"发现 {error_count} 个问题"]
            if error_levels.get("error", 0) > 0:
                summary_parts.append(f"{error_levels['error']} 个错误")
            if error_levels.get("warning", 0) > 0:
                summary_parts.append(f"{error_levels['warning']} 个警告")
            if error_levels.get("info", 0) > 0:
                summary_parts.append(f"{error_levels['info']} 个提示")
            
            summary = "，".join(summary_parts)
            success = error_levels.get("error", 0) == 0
        
        logger.info(f"本地规则验证完成: {summary}, 执行时间: {execution_time:.2f}s")
        
        return ValidationResult(
            success=success,
            errors=all_errors,
            summary=summary,
            execution_time=execution_time,
            rules_executed=len(results)
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        avg_time = self.total_execution_time / self.validation_count if self.validation_count > 0 else 0
        
        metrics = {
            "total_validations": self.validation_count,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": avg_time,
            "rule_metrics": self.executor.get_performance_metrics(),
            "slow_rules": self.executor.get_slow_rules()
        }
        
        return metrics
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        获取规则统计信息
        
        Returns:
            规则统计字典
        """
        config_info = self.config_manager.get_config_info()
        enabled_rules = self.config_manager.get_enabled_rules()
        
        # 按类别统计
        category_stats = {}
        for rule in enabled_rules:
            category = rule.category
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "critical_count": 0
                }
            category_stats[category]["count"] += 1
            if rule.critical:
                category_stats[category]["critical_count"] += 1
        
        return {
            "config_info": config_info,
            "enabled_rules_count": len(enabled_rules),
            "category_statistics": category_stats,
            "performance_metrics": self.get_performance_metrics()
        }


# 全局实例（将在应用启动时初始化）
local_rules_engine: Optional[LocalRulesEngine] = None


def get_local_rules_engine() -> Optional[LocalRulesEngine]:
    """获取本地规则引擎实例"""
    return local_rules_engine


def init_local_rules_engine(config_path: str) -> LocalRulesEngine:
    """
    初始化本地规则引擎
    
    Args:
        config_path: 规则配置文件路径
        
    Returns:
        本地规则引擎实例
    """
    global local_rules_engine
    
    config_manager = RulesConfigManager(config_path)
    local_rules_engine = LocalRulesEngine(config_manager)
    
    logger.info("本地规则引擎已初始化")
    return local_rules_engine
