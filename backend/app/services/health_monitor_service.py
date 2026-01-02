"""
健康监控服务

负责监控 AI 服务健康状态，管理降级模式切换
"""
import asyncio
import time
from datetime import datetime
from typing import Optional
import logging
import httpx

from app.models.validation import HealthStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthMonitorService:
    """健康监控服务"""
    
    def __init__(
        self,
        check_interval: int = 30,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        timeout: int = 5
    ):
        """
        初始化健康监控服务
        
        Args:
            check_interval: 健康检查间隔（秒）
            failure_threshold: 失败阈值（连续失败次数）
            recovery_threshold: 恢复阈值（连续成功次数）
            timeout: 健康检查超时时间（秒）
        """
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.timeout = timeout
        
        # 状态管理
        self.mode = "normal"  # normal 或 fallback
        self.ai_service_healthy = True
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None
        self.fallback_start_time: Optional[datetime] = None
        
        # 统计信息
        self.total_checks = 0
        self.total_failures = 0
        self.total_fallback_events = 0
        self.total_fallback_duration = 0.0
        
        # 后台任务
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
    
    async def check_ai_health(self) -> bool:
        """
        检查 AI 服务健康状态
        
        Returns:
            是否健康
        """
        try:
            # 使用轻量级的健康检查请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 简单的连接测试
                response = await client.get(
                    f"{settings.DEEPSEEK_API_BASE}/models",
                    headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"}
                )
                
                # 2xx 状态码表示健康
                is_healthy = 200 <= response.status_code < 300
                
                if is_healthy:
                    logger.debug("AI 服务健康检查通过")
                else:
                    logger.warning(f"AI 服务健康检查失败: HTTP {response.status_code}")
                
                return is_healthy
                
        except httpx.TimeoutException:
            logger.warning(f"AI 服务健康检查超时（{self.timeout}秒）")
            return False
        except httpx.ConnectError as e:
            logger.warning(f"AI 服务连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"AI 服务健康检查异常: {e}")
            return False
    
    async def _perform_health_check(self) -> None:
        """执行健康检查并更新状态"""
        self.total_checks += 1
        self.last_check_time = datetime.now()
        
        is_healthy = await self.check_ai_health()
        
        if is_healthy:
            self.consecutive_failures = 0
            self.consecutive_successes += 1
            
            # 如果在降级模式且连续成功达到阈值，切换回正常模式
            if self.mode == "fallback" and self.consecutive_successes >= self.recovery_threshold:
                await self._switch_to_normal_mode()
        else:
            self.consecutive_successes = 0
            self.consecutive_failures += 1
            self.total_failures += 1
            self.last_failure_time = datetime.now()
            
            # 如果在正常模式且连续失败达到阈值，切换到降级模式
            if self.mode == "normal" and self.consecutive_failures >= self.failure_threshold:
                await self._switch_to_fallback_mode()
        
        self.ai_service_healthy = is_healthy
    
    async def _switch_to_fallback_mode(self) -> None:
        """切换到降级模式"""
        logger.warning(f"切换到降级模式（连续失败 {self.consecutive_failures} 次）")
        self.mode = "fallback"
        self.fallback_start_time = datetime.now()
        self.total_fallback_events += 1
        
        # 记录降级事件
        # TODO: 添加到审计日志
    
    async def _switch_to_normal_mode(self) -> None:
        """切换回正常模式"""
        logger.info(f"切换回正常模式（连续成功 {self.consecutive_successes} 次）")
        
        # 记录降级持续时间
        if self.fallback_start_time:
            # 确保 fallback_start_time 是 datetime 对象
            if isinstance(self.fallback_start_time, (int, float)):
                from datetime import datetime as dt
                fallback_start = dt.fromtimestamp(self.fallback_start_time)
            else:
                fallback_start = self.fallback_start_time
            
            duration = (datetime.now() - fallback_start).total_seconds()
            self.total_fallback_duration += duration
            logger.info(f"本次降级持续时间: {duration:.1f}秒")
        
        self.mode = "normal"
        self.fallback_start_time = None
        
        # 记录恢复事件
        # TODO: 添加到审计日志
    
    async def _monitoring_loop(self) -> None:
        """健康监控循环"""
        logger.info(f"健康监控服务已启动（间隔: {self.check_interval}秒）")
        
        while self.is_monitoring:
            try:
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"健康检查执行失败: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)
    
    async def start_monitoring(self) -> None:
        """启动健康监控"""
        if self.is_monitoring:
            logger.warning("健康监控已经在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("健康监控服务启动成功")
    
    async def stop_monitoring(self) -> None:
        """停止健康监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("健康监控服务已停止")
    
    def is_fallback_mode(self) -> bool:
        """
        是否处于降级模式
        
        Returns:
            是否降级模式
        """
        return self.mode == "fallback"
    
    def get_estimated_recovery_time(self) -> Optional[int]:
        """
        获取预计恢复时间
        
        Returns:
            预计恢复时间（秒），如果无法估算返回 None
        """
        if self.mode == "normal":
            return None
        
        # 基于历史数据估算
        # 简单实现：假设平均恢复时间为 check_interval * recovery_threshold
        return self.check_interval * self.recovery_threshold
    
    def get_health_status(self) -> HealthStatus:
        """
        获取健康状态
        
        Returns:
            健康状态对象
        """
        # 计算当前降级持续时间
        current_fallback_duration = None
        if self.fallback_start_time:
            # 确保 fallback_start_time 是 datetime 对象
            if isinstance(self.fallback_start_time, (int, float)):
                from datetime import datetime as dt
                fallback_start = dt.fromtimestamp(self.fallback_start_time)
            else:
                fallback_start = self.fallback_start_time
            
            current_fallback_duration = int((datetime.now() - fallback_start).total_seconds())
        
        return HealthStatus(
            mode=self.mode,
            ai_service_healthy=self.ai_service_healthy,
            consecutive_failures=self.consecutive_failures,
            consecutive_successes=self.consecutive_successes,
            last_check_time=self.last_check_time or datetime.now(),
            last_failure_time=self.last_failure_time,
            estimated_recovery=self.get_estimated_recovery_time(),
            fallback_statistics={
                "total_checks": self.total_checks,
                "total_failures": self.total_failures,
                "total_fallback_events": self.total_fallback_events,
                "total_fallback_duration": self.total_fallback_duration,
                "current_fallback_duration": current_fallback_duration,
                "failure_rate": self.total_failures / self.total_checks if self.total_checks > 0 else 0
            }
        )


# 全局实例（将在应用启动时初始化）
health_monitor: Optional[HealthMonitorService] = None


def get_health_monitor() -> Optional[HealthMonitorService]:
    """获取健康监控服务实例"""
    return health_monitor


def init_health_monitor(
    check_interval: int = 30,
    failure_threshold: int = 3,
    recovery_threshold: int = 2,
    timeout: int = 5
) -> HealthMonitorService:
    """
    初始化健康监控服务
    
    Args:
        check_interval: 健康检查间隔（秒）
        failure_threshold: 失败阈值
        recovery_threshold: 恢复阈值
        timeout: 超时时间（秒）
        
    Returns:
        健康监控服务实例
    """
    global health_monitor
    
    health_monitor = HealthMonitorService(
        check_interval=check_interval,
        failure_threshold=failure_threshold,
        recovery_threshold=recovery_threshold,
        timeout=timeout
    )
    
    logger.info("健康监控服务已初始化")
    return health_monitor
