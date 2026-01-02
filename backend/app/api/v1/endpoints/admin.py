"""
管理员 API 端点

提供规则管理和性能监控接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.local_rules_engine import get_local_rules_engine
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


class RuleInfo(BaseModel):
    """规则信息"""
    id: str
    name: str
    category: str
    priority: int
    enabled: bool
    critical: bool
    rule_type: str
    description: str


class RulePerformanceMetric(BaseModel):
    """规则性能指标"""
    rule_id: str
    rule_name: str
    execution_count: int
    total_time: float
    average_time: float
    max_time: float
    min_time: float


class RulesListResponse(BaseModel):
    """规则列表响应"""
    total_rules: int
    enabled_rules: int
    disabled_rules: int
    rules: List[RuleInfo]


class RulePerformanceResponse(BaseModel):
    """规则性能响应"""
    total_validations: int
    total_execution_time: float
    average_execution_time: float
    rule_metrics: List[RulePerformanceMetric]
    slow_rules: List[Dict[str, Any]]


class RuleStatisticsResponse(BaseModel):
    """规则统计响应"""
    config_info: Dict[str, Any]
    enabled_rules_count: int
    category_statistics: Dict[str, Dict[str, int]]
    performance_metrics: Dict[str, Any]
    # 前端需要的额外字段
    total_rules: int
    enabled_rules: int
    disabled_rules: int
    rules_by_category: Dict[str, Dict[str, int]]


class RuleToggleRequest(BaseModel):
    """规则启用/禁用请求"""
    enabled: bool


@router.get("/rules/list", response_model=RulesListResponse)
async def list_rules(
    current_user: User = Depends(get_current_user)
):
    """
    列出所有规则
    
    返回所有规则的基本信息，包括启用状态
    """
    local_engine = get_local_rules_engine()
    
    if not local_engine:
        raise HTTPException(
            status_code=503,
            detail="本地规则引擎未初始化"
        )
    
    # 获取所有规则
    config = local_engine.config_manager.current_config
    
    if not config:
        raise HTTPException(
            status_code=500,
            detail="规则配置未加载"
        )
    
    rules_info = []
    enabled_count = 0
    
    for rule in config.rules:
        rules_info.append(RuleInfo(
            id=rule.id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            enabled=rule.enabled,
            critical=rule.critical,
            rule_type=rule.rule_type,
            description=rule.description
        ))
        
        if rule.enabled:
            enabled_count += 1
    
    return RulesListResponse(
        total_rules=len(rules_info),
        enabled_rules=enabled_count,
        disabled_rules=len(rules_info) - enabled_count,
        rules=rules_info
    )


@router.get("/rules/performance", response_model=RulePerformanceResponse)
async def get_rule_performance(
    current_user: User = Depends(get_current_user)
):
    """
    获取规则性能指标
    
    返回每个规则的执行时间统计，标识慢规则
    """
    local_engine = get_local_rules_engine()
    
    if not local_engine:
        raise HTTPException(
            status_code=503,
            detail="本地规则引擎未初始化"
        )
    
    # 获取性能指标
    metrics = local_engine.get_performance_metrics()
    
    # 转换规则指标格式
    rule_metrics = []
    # rule_metrics 包含 {"total_rules": int, "rules": {...}}
    rule_metrics_data = metrics.get("rule_metrics", {}).get("rules", {})
    for rule_id, rule_metric in rule_metrics_data.items():
        rule_metrics.append(RulePerformanceMetric(
            rule_id=rule_id,
            rule_name=rule_metric.get("rule_name", rule_id),
            execution_count=rule_metric.get("executions", 0),
            total_time=rule_metric.get("avg_time", 0.0) * rule_metric.get("executions", 0),
            average_time=rule_metric.get("avg_time", 0.0),
            max_time=rule_metric.get("max_time", 0.0),
            min_time=rule_metric.get("min_time", 0.0)
        ))
    
    return RulePerformanceResponse(
        total_validations=metrics.get("total_validations", 0),
        total_execution_time=metrics.get("total_execution_time", 0.0),
        average_execution_time=metrics.get("average_execution_time", 0.0),
        rule_metrics=rule_metrics,
        slow_rules=metrics.get("slow_rules", [])
    )


@router.get("/rules/statistics", response_model=RuleStatisticsResponse)
async def get_rule_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    获取规则统计信息
    
    返回规则配置信息、分类统计、性能指标等
    """
    local_engine = get_local_rules_engine()
    
    if not local_engine:
        raise HTTPException(
            status_code=503,
            detail="本地规则引擎未初始化"
        )
    
    stats = local_engine.get_rule_statistics()
    
    return RuleStatisticsResponse(
        config_info=stats.get("config_info", {}),
        enabled_rules_count=stats.get("enabled_rules_count", 0),
        category_statistics=stats.get("category_statistics", {}),
        performance_metrics=stats.get("performance_metrics", {}),
        # 添加前端需要的字段
        total_rules=stats.get("total_rules", 0),
        enabled_rules=stats.get("enabled_rules", 0),
        disabled_rules=stats.get("disabled_rules", 0),
        rules_by_category=stats.get("rules_by_category", {})
    )


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: str,
    request: RuleToggleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    启用/禁用规则
    
    动态启用或禁用指定规则，无需重启服务
    """
    local_engine = get_local_rules_engine()
    
    if not local_engine:
        raise HTTPException(
            status_code=503,
            detail="本地规则引擎未初始化"
        )
    
    # 切换规则状态
    success = local_engine.config_manager.toggle_rule(rule_id, request.enabled)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"规则 {rule_id} 不存在"
        )
    
    return {
        "success": True,
        "message": f"规则 {rule_id} 已{'启用' if request.enabled else '禁用'}",
        "rule_id": rule_id,
        "enabled": request.enabled
    }


@router.post("/rules/reload")
async def reload_rules(
    current_user: User = Depends(get_current_user)
):
    """
    重载规则配置
    
    手动触发规则配置重载，从配置文件重新加载所有规则
    """
    local_engine = get_local_rules_engine()
    
    if not local_engine:
        raise HTTPException(
            status_code=503,
            detail="本地规则引擎未初始化"
        )
    
    # 重载配置
    try:
        config = await local_engine.config_manager.load_config()
        
        if not config:
            raise HTTPException(
                status_code=500,
                detail="配置重载失败，请检查配置文件格式"
            )
        
        return {
            "success": True,
            "message": "规则配置已重载",
            "rules_count": len(config.rules),
            "enabled_rules_count": len([r for r in config.rules if r.enabled])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"配置重载失败: {str(e)}"
        )
