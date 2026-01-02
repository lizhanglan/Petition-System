"""
健康监控 API 端点

提供系统健康状态和降级统计查询接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.health_monitor_service import get_health_monitor
from app.models.validation import HealthStatus

router = APIRouter()


class HealthStatusResponse(BaseModel):
    """健康状态响应"""
    mode: str  # normal 或 fallback
    ai_service_healthy: bool
    consecutive_failures: int
    consecutive_successes: int
    last_check_time: datetime
    last_failure_time: Optional[datetime]
    estimated_recovery: Optional[int]  # 秒


class FallbackStatisticsResponse(BaseModel):
    """降级统计响应"""
    total_checks: int
    total_failures: int
    total_fallback_events: int
    total_fallback_duration: float  # 秒
    current_fallback_duration: Optional[int]  # 秒
    failure_rate: float
    uptime_rate: float


@router.get("/status", response_model=HealthStatusResponse)
async def get_health_status():
    """
    获取系统健康状态
    
    返回当前模式（正常/降级）、AI 服务健康状态、连续失败/成功次数等信息
    """
    health_monitor = get_health_monitor()
    
    if not health_monitor:
        raise HTTPException(
            status_code=503,
            detail="健康监控服务未初始化"
        )
    
    health_status = health_monitor.get_health_status()
    
    return HealthStatusResponse(
        mode=health_status.mode,
        ai_service_healthy=health_status.ai_service_healthy,
        consecutive_failures=health_status.consecutive_failures,
        consecutive_successes=health_status.consecutive_successes,
        last_check_time=health_status.last_check_time,
        last_failure_time=health_status.last_failure_time,
        estimated_recovery=health_status.estimated_recovery
    )


@router.get("/fallback-stats", response_model=FallbackStatisticsResponse)
async def get_fallback_statistics():
    """
    获取降级统计信息
    
    返回降级频率、持续时间、影响请求数等统计数据
    """
    health_monitor = get_health_monitor()
    
    if not health_monitor:
        raise HTTPException(
            status_code=503,
            detail="健康监控服务未初始化"
        )
    
    health_status = health_monitor.get_health_status()
    stats = health_status.fallback_statistics
    
    # 计算正常运行率
    uptime_rate = 1.0 - stats.get("failure_rate", 0)
    
    return FallbackStatisticsResponse(
        total_checks=stats.get("total_checks", 0),
        total_failures=stats.get("total_failures", 0),
        total_fallback_events=stats.get("total_fallback_events", 0),
        total_fallback_duration=stats.get("total_fallback_duration", 0.0),
        current_fallback_duration=stats.get("current_fallback_duration"),
        failure_rate=stats.get("failure_rate", 0.0),
        uptime_rate=uptime_rate
    )


@router.get("/check")
async def health_check():
    """
    简单的健康检查端点
    
    用于负载均衡器或监控系统快速检查服务是否运行
    """
    health_monitor = get_health_monitor()
    
    if not health_monitor:
        return {
            "status": "degraded",
            "message": "健康监控服务未初始化"
        }
    
    health_status = health_monitor.get_health_status()
    
    return {
        "status": "healthy" if health_status.mode == "normal" else "degraded",
        "mode": health_status.mode,
        "ai_service_healthy": health_status.ai_service_healthy
    }
