"""
性能监控工具
"""
import time
from functools import wraps
from typing import Callable
import asyncio

class PerformanceMonitor:
    """性能监控器"""
    
    @staticmethod
    def measure_time(func_name: str = None):
        """
        测量函数执行时间的装饰器
        
        使用示例：
        @PerformanceMonitor.measure_time("查询文档列表")
        async def get_documents():
            ...
        """
        def decorator(func: Callable):
            name = func_name or func.__name__
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    
                    # 记录执行时间
                    if elapsed > 1.0:  # 超过 1 秒的慢查询
                        print(f"[Performance] SLOW: {name} took {elapsed:.2f}s")
                    elif elapsed > 0.5:  # 超过 0.5 秒的警告
                        print(f"[Performance] WARN: {name} took {elapsed:.2f}s")
                    else:
                        print(f"[Performance] {name} took {elapsed:.3f}s")
                    
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"[Performance] ERROR: {name} failed after {elapsed:.2f}s: {str(e)}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    
                    if elapsed > 1.0:
                        print(f"[Performance] SLOW: {name} took {elapsed:.2f}s")
                    elif elapsed > 0.5:
                        print(f"[Performance] WARN: {name} took {elapsed:.2f}s")
                    else:
                        print(f"[Performance] {name} took {elapsed:.3f}s")
                    
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"[Performance] ERROR: {name} failed after {elapsed:.2f}s: {str(e)}")
                    raise
            
            # 判断是否为异步函数
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator

performance_monitor = PerformanceMonitor()
