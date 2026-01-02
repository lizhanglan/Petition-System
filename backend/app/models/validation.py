"""
数据模型：本地规则库降级系统

定义规则、验证结果和验证错误的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RuleCategory(str, Enum):
    """规则类别"""
    FORMAT = "format"
    CONTENT = "content"
    COMPLIANCE = "compliance"


class RuleType(str, Enum):
    """规则类型"""
    PATTERN = "pattern"  # 正则表达式匹配
    LENGTH = "length"  # 长度检查
    KEYWORD = "keyword"  # 关键词检测
    STRUCTURE = "structure"  # 结构验证
    CUSTOM = "custom"  # 自定义规则


class ErrorLevel(str, Enum):
    """错误级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorType(str, Enum):
    """错误类型"""
    FORMAT_ERROR = "format_error"
    CONTENT_ERROR = "content_error"
    COMPLIANCE_ERROR = "compliance_error"


class Rule(BaseModel):
    """验证规则"""
    id: str = Field(..., description="规则唯一标识")
    name: str = Field(..., description="规则名称")
    category: RuleCategory = Field(..., description="规则类别")
    priority: int = Field(..., ge=1, le=100, description="优先级（1-100，数字越大优先级越高）")
    enabled: bool = Field(default=True, description="是否启用")
    critical: bool = Field(default=False, description="是否为关键错误（检测到后立即停止）")
    rule_type: RuleType = Field(..., description="规则类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="规则参数")
    error_type: ErrorType = Field(..., description="错误类型")
    error_level: ErrorLevel = Field(..., description="错误级别")
    description: str = Field(..., description="错误描述")
    suggestion: Optional[str] = Field(None, description="修改建议")
    
    class Config:
        use_enum_values = True


class ValidationError(BaseModel):
    """验证错误"""
    type: ErrorType = Field(..., description="错误类型")
    level: ErrorLevel = Field(..., description="错误级别")
    position: Optional[Dict[str, Any]] = Field(None, description="错误位置（行号、列号、字段名等）")
    description: str = Field(..., description="错误描述")
    suggestion: Optional[str] = Field(None, description="修改建议")
    reference: Optional[str] = Field(None, description="规则ID或法规引用")
    
    class Config:
        use_enum_values = True


class ValidationResult(BaseModel):
    """验证结果"""
    success: bool = Field(..., description="验证是否成功")
    errors: List[ValidationError] = Field(default_factory=list, description="错误列表")
    summary: str = Field(..., description="验证摘要")
    fallback_mode: bool = Field(default=False, description="是否为降级模式")
    fallback_notice: Optional[str] = Field(None, description="降级模式通知")
    estimated_recovery: Optional[int] = Field(None, description="预计恢复时间（秒）")
    execution_time: float = Field(..., description="执行时间（秒）")
    rules_executed: int = Field(..., description="执行的规则数量")
    
    class Config:
        use_enum_values = True


class HealthStatus(BaseModel):
    """健康状态"""
    mode: str = Field(..., description="运行模式（normal/fallback）")
    ai_service_healthy: bool = Field(..., description="AI服务是否健康")
    consecutive_failures: int = Field(..., description="连续失败次数")
    consecutive_successes: int = Field(default=0, description="连续成功次数")
    last_check_time: datetime = Field(..., description="最后检查时间")
    last_failure_time: Optional[datetime] = Field(None, description="最后失败时间")
    estimated_recovery: Optional[int] = Field(None, description="预计恢复时间（秒）")
    fallback_statistics: Dict[str, Any] = Field(default_factory=dict, description="降级统计信息")


class RulesConfig(BaseModel):
    """规则配置"""
    version: str = Field(..., description="配置版本")
    rules: List[Rule] = Field(default_factory=list, description="规则列表")
    templates: List[Dict[str, Any]] = Field(default_factory=list, description="规则模板")
    
    def validate_rules(self) -> tuple[bool, Optional[str]]:
        """
        验证规则配置
        
        Returns:
            (是否有效, 错误信息)
        """
        # 检查规则ID唯一性
        rule_ids = [rule.id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            return False, "规则ID必须唯一"
        
        # 检查规则参数完整性
        for rule in self.rules:
            if rule.rule_type == RuleType.PATTERN:
                if "pattern" not in rule.parameters:
                    return False, f"规则 {rule.id} 缺少 pattern 参数"
            elif rule.rule_type == RuleType.LENGTH:
                if "min_length" not in rule.parameters and "max_length" not in rule.parameters:
                    return False, f"规则 {rule.id} 缺少 min_length 或 max_length 参数"
            elif rule.rule_type == RuleType.KEYWORD:
                if "keywords" not in rule.parameters:
                    return False, f"规则 {rule.id} 缺少 keywords 参数"
        
        return True, None
