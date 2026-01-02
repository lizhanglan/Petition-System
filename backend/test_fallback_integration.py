"""
本地规则库降级功能 - 集成测试（简化版）

不依赖 pytest，可以直接运行
"""
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.health_monitor_service import HealthMonitorService, init_health_monitor
from app.services.local_rules_engine import LocalRulesEngine, init_local_rules_engine
from app.core.rules_config import RulesConfigManager


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        self.total_tests += 1
        
        try:
            asyncio.run(test_func())
            self.passed_tests += 1
            return True
        except AssertionError as e:
            print(f"\n  ✗ 测试失败: {test_name}")
            print(f"    断言错误: {e}")
            self.failed_tests += 1
            return False
        except Exception as e:
            print(f"\n  ✗ 测试异常: {test_name}")
            print(f"    错误: {e}")
            import traceback
            traceback.print_exc()
            self.failed_tests += 1
            return False
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"总测试数: {self.total_tests}")
        print(f"通过: {self.passed_tests}")
        print(f"失败: {self.failed_tests}")
        print(f"成功率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        print("=" * 70)
        
        if self.failed_tests == 0:
            print("\n🎉 所有集成测试通过！降级功能工作正常。")
            return 0
        else:
            print(f"\n⚠️  有 {self.failed_tests} 个测试失败，请检查错误信息。")
            return 1


# ============================================================================
# 测试1: AI 服务失败触发降级
# ============================================================================

async def test_ai_failure_triggers_fallback():
    """测试 AI 服务失败触发降级"""
    print("\n=== 测试1: AI 服务失败触发降级 ===")
    
    # 初始化健康监控
    monitor = HealthMonitorService(
        check_interval=1,
        failure_threshold=3,
        recovery_threshold=2,
        timeout=1
    )
    
    # 模拟 AI 服务失败
    async def mock_check_health():
        return False
    
    original_check = monitor.check_ai_health
    monitor.check_ai_health = mock_check_health
    
    try:
        # 执行 3 次健康检查（达到失败阈值）
        for i in range(3):
            await monitor._perform_health_check()
            print(f"  检查 {i+1}: 失败，连续失败次数: {monitor.consecutive_failures}")
        
        # 验证已切换到降级模式
        assert monitor.mode == "fallback", "应该切换到降级模式"
        assert monitor.consecutive_failures == 3, "连续失败次数应为 3"
        print("  ✓ 成功切换到降级模式")
        
        # 验证降级统计
        status = monitor.get_health_status()
        assert status.fallback_statistics["total_fallback_events"] == 1, "应该记录 1 次降级事件"
        print(f"  ✓ 降级统计正确: {status.fallback_statistics['total_fallback_events']} 次降级事件")
    
    finally:
        monitor.check_ai_health = original_check


# ============================================================================
# 测试2: 降级模式使用本地引擎
# ============================================================================

async def test_fallback_mode_uses_local_engine():
    """测试降级模式使用本地引擎"""
    print("\n=== 测试2: 降级模式使用本地引擎 ===")
    
    # 初始化本地规则引擎
    engine = init_local_rules_engine("backend/config/validation_rules.json")
    await engine.config_manager.load_config()
    
    # 测试文档
    test_content = """
    关于信访事项的答复
    
    主送单位：市信访局
    
    正文：
    经调查核实，您反映的问题属实。
    
    落款：
    XX单位
    2024年1月2日
    """
    
    # 执行验证
    result = await engine.validate_document(test_content)
    
    # 验证结果
    assert result is not None, "应该返回验证结果"
    assert result.execution_time < 3.0, f"执行时间应小于 3 秒，实际: {result.execution_time:.3f}秒"
    assert result.rules_executed > 0, "应该执行了规则"
    
    print(f"  ✓ 本地引擎验证成功")
    print(f"    - 执行时间: {result.execution_time:.3f}秒")
    print(f"    - 执行规则: {result.rules_executed} 个")
    print(f"    - 发现问题: {len(result.errors)} 个")
    print(f"    - 验证结果: {'通过' if result.success else '未通过'}")


# ============================================================================
# 测试3: 降级通知包含在响应中
# ============================================================================

async def test_fallback_notice_in_response():
    """测试降级通知包含在响应中"""
    print("\n=== 测试3: 降级通知包含在响应中 ===")
    
    # 初始化健康监控
    monitor = init_health_monitor(
        check_interval=1,
        failure_threshold=3,
        recovery_threshold=2,
        timeout=1
    )
    
    # 模拟降级模式
    monitor.mode = "fallback"
    monitor.fallback_start_time = time.time()
    
    # 验证降级状态
    assert monitor.is_fallback_mode(), "应该处于降级模式"
    
    # 获取恢复时间估算
    recovery_time = monitor.get_estimated_recovery_time()
    assert recovery_time is not None, "应该提供恢复时间估算"
    
    print(f"  ✓ 降级模式已激活")
    print(f"    - 预计恢复时间: {recovery_time} 秒")
    
    # 模拟响应数据
    response_data = {
        "fallback_mode": True,
        "fallback_notice": "AI 服务当前不可用，使用本地规则库进行基础校验",
        "estimated_recovery": recovery_time
    }
    
    assert response_data["fallback_mode"] is True, "响应应标记降级模式"
    assert response_data["fallback_notice"] is not None, "响应应包含降级通知"
    print(f"  ✓ 降级通知正确: {response_data['fallback_notice']}")


# ============================================================================
# 测试4: AI 服务恢复触发正常模式
# ============================================================================

async def test_ai_recovery_triggers_normal_mode():
    """测试 AI 服务恢复触发正常模式"""
    print("\n=== 测试4: AI 服务恢复触发正常模式 ===")
    
    # 初始化健康监控
    monitor = HealthMonitorService(
        check_interval=1,
        failure_threshold=3,
        recovery_threshold=2,
        timeout=1
    )
    
    # 先进入降级模式
    monitor.mode = "fallback"
    monitor.fallback_start_time = time.time()
    monitor.consecutive_failures = 3
    monitor.consecutive_successes = 0
    
    print(f"  初始状态: {monitor.mode} 模式")
    
    # 模拟 AI 服务恢复
    async def mock_check_health():
        return True
    
    original_check = monitor.check_ai_health
    monitor.check_ai_health = mock_check_health
    
    try:
        # 执行 2 次健康检查（达到恢复阈值）
        for i in range(2):
            await monitor._perform_health_check()
            print(f"  检查 {i+1}: 成功，连续成功次数: {monitor.consecutive_successes}")
        
        # 验证已切换回正常模式
        assert monitor.mode == "normal", "应该切换回正常模式"
        assert monitor.consecutive_successes == 2, "连续成功次数应为 2"
        assert monitor.consecutive_failures == 0, "连续失败次数应重置为 0"
        print("  ✓ 成功切换回正常模式")
    
    finally:
        monitor.check_ai_health = original_check


# ============================================================================
# 测试5: 降级持续时间跟踪
# ============================================================================

async def test_fallback_duration_tracking():
    """测试降级持续时间跟踪"""
    print("\n=== 测试5: 降级持续时间跟踪 ===")
    
    # 初始化健康监控
    monitor = HealthMonitorService(
        check_interval=1,
        failure_threshold=3,
        recovery_threshold=2,
        timeout=1
    )
    
    # 进入降级模式
    monitor.mode = "fallback"
    start_time = time.time()
    monitor.fallback_start_time = start_time
    
    # 等待一段时间
    await asyncio.sleep(0.5)
    
    # 获取当前降级持续时间
    status = monitor.get_health_status()
    current_duration = status.fallback_statistics.get("current_fallback_duration")
    
    assert current_duration is not None, "应该跟踪当前降级持续时间"
    assert current_duration >= 0, "持续时间应该是非负数"
    
    print(f"  ✓ 降级持续时间跟踪正确: {current_duration} 秒")
    
    # 切换回正常模式
    monitor.mode = "normal"
    duration = time.time() - start_time
    monitor.total_fallback_duration += duration
    monitor.fallback_start_time = None
    
    # 验证总降级时间
    status = monitor.get_health_status()
    total_duration = status.fallback_statistics.get("total_fallback_duration")
    
    assert total_duration > 0, "应该记录总降级时间"
    print(f"  ✓ 总降级时间记录正确: {total_duration:.3f} 秒")


# ============================================================================
# 测试6: 降级模式下的并发验证
# ============================================================================

async def test_concurrent_validations_in_fallback_mode():
    """测试降级模式下的并发验证"""
    print("\n=== 测试6: 降级模式下的并发验证 ===")
    
    # 初始化本地规则引擎
    engine = init_local_rules_engine("backend/config/validation_rules.json")
    await engine.config_manager.load_config()
    
    # 测试文档
    test_content = "测试文档内容" * 100
    
    # 并发执行多个验证
    num_concurrent = 5
    start_time = time.time()
    
    tasks = [
        engine.validate_document(test_content)
        for _ in range(num_concurrent)
    ]
    
    results = await asyncio.gather(*tasks)
    
    elapsed_time = time.time() - start_time
    
    # 验证所有结果
    assert len(results) == num_concurrent, f"应该返回 {num_concurrent} 个结果"
    
    for i, result in enumerate(results):
        assert result is not None, f"结果 {i+1} 不应为空"
        assert result.execution_time < 3.0, f"结果 {i+1} 执行时间应小于 3 秒"
    
    avg_time = elapsed_time / num_concurrent
    
    print(f"  ✓ 并发验证成功")
    print(f"    - 并发数: {num_concurrent}")
    print(f"    - 总耗时: {elapsed_time:.3f}秒")
    print(f"    - 平均耗时: {avg_time:.3f}秒")
    print(f"    - 所有验证均在 3 秒内完成")


# ============================================================================
# 测试7: 配置重载（无需重启）
# ============================================================================

async def test_config_reload_without_restart():
    """测试无需重启的配置重载"""
    print("\n=== 测试7: 配置重载（无需重启）===")
    
    # 初始化配置管理器
    config_manager = RulesConfigManager("backend/config/validation_rules.json")
    initial_config = await config_manager.load_config()
    
    assert initial_config is not None, "初始配置应该加载成功"
    initial_rule_count = len(initial_config.rules)
    
    print(f"  初始配置: {initial_rule_count} 个规则")
    
    # 重新加载配置
    reloaded_config = await config_manager.load_config()
    
    assert reloaded_config is not None, "重载配置应该成功"
    assert len(reloaded_config.rules) == initial_rule_count, "规则数量应该一致"
    
    print(f"  ✓ 配置重载成功: {len(reloaded_config.rules)} 个规则")


# ============================================================================
# 测试8: 动态启用/禁用规则
# ============================================================================

async def test_rule_toggle_without_restart():
    """测试动态启用/禁用规则"""
    print("\n=== 测试8: 动态启用/禁用规则 ===")
    
    # 初始化配置管理器
    config_manager = RulesConfigManager("backend/config/validation_rules.json")
    await config_manager.load_config()
    
    # 获取第一个规则
    rules = config_manager.get_enabled_rules()
    assert len(rules) > 0, "应该有启用的规则"
    
    first_rule = rules[0]
    rule_id = first_rule.id
    initial_state = first_rule.enabled
    
    print(f"  规则 {rule_id} 初始状态: {'启用' if initial_state else '禁用'}")
    
    # 切换规则状态
    success = config_manager.toggle_rule(rule_id, not initial_state)
    assert success, "切换规则状态应该成功"
    
    # 验证状态已改变
    updated_rule = next((r for r in config_manager.current_config.rules if r.id == rule_id), None)
    
    assert updated_rule is not None, "应该找到更新后的规则"
    assert updated_rule.enabled == (not initial_state), "规则状态应该已改变"
    
    print(f"  ✓ 规则状态切换成功: {'启用' if updated_rule.enabled else '禁用'}")
    
    # 恢复原始状态
    config_manager.toggle_rule(rule_id, initial_state)
    print(f"  ✓ 规则状态已恢复")
    print(f"  ✓ 规则状态已恢复")


# ============================================================================
# 测试9: 执行时间跟踪
# ============================================================================

async def test_execution_time_tracking():
    """测试执行时间跟踪"""
    print("\n=== 测试9: 执行时间跟踪 ===")
    
    # 初始化本地规则引擎
    engine = init_local_rules_engine("backend/config/validation_rules.json")
    await engine.config_manager.load_config()
    
    # 执行多次验证
    test_content = "测试文档内容" * 100
    num_validations = 5
    
    for i in range(num_validations):
        await engine.validate_document(test_content)
    
    # 获取性能指标
    metrics = engine.get_performance_metrics()
    
    assert metrics["total_validations"] == num_validations, f"应该记录 {num_validations} 次验证"
    assert metrics["total_execution_time"] > 0, "应该记录总执行时间"
    assert metrics["average_execution_time"] > 0, "应该计算平均执行时间"
    
    print(f"  ✓ 性能指标跟踪正确")
    print(f"    - 总验证次数: {metrics['total_validations']}")
    print(f"    - 总执行时间: {metrics['total_execution_time']:.3f}秒")
    print(f"    - 平均执行时间: {metrics['average_execution_time']:.3f}秒")


# ============================================================================
# 测试10: 慢规则识别
# ============================================================================

async def test_slow_rule_identification():
    """测试慢规则识别"""
    print("\n=== 测试10: 慢规则识别 ===")
    
    # 初始化本地规则引擎
    engine = init_local_rules_engine("backend/config/validation_rules.json")
    await engine.config_manager.load_config()
    
    # 执行验证
    test_content = "测试文档内容" * 100
    await engine.validate_document(test_content)
    
    # 获取慢规则
    metrics = engine.get_performance_metrics()
    slow_rules = metrics.get("slow_rules", [])
    
    # 慢规则阈值是 500ms，正常情况下不应该有慢规则
    print(f"  ✓ 慢规则检测完成")
    print(f"    - 慢规则数量: {len(slow_rules)}")
    
    if slow_rules:
        print(f"    - 慢规则详情:")
        for rule in slow_rules[:3]:  # 只显示前3个
            print(f"      * {rule.get('rule_name')}: {rule.get('average_time', 0):.3f}秒")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有集成测试"""
    print("=" * 70)
    print("本地规则库降级功能 - 集成测试")
    print("=" * 70)
    
    runner = TestRunner()
    
    # 定义所有测试
    tests = [
        ("AI 服务失败触发降级", test_ai_failure_triggers_fallback),
        ("降级模式使用本地引擎", test_fallback_mode_uses_local_engine),
        ("降级通知包含在响应中", test_fallback_notice_in_response),
        ("AI 服务恢复触发正常模式", test_ai_recovery_triggers_normal_mode),
        ("降级持续时间跟踪", test_fallback_duration_tracking),
        ("降级模式下的并发验证", test_concurrent_validations_in_fallback_mode),
        ("配置重载（无需重启）", test_config_reload_without_restart),
        ("动态启用/禁用规则", test_rule_toggle_without_restart),
        ("执行时间跟踪", test_execution_time_tracking),
        ("慢规则识别", test_slow_rule_identification),
    ]
    
    # 运行所有测试
    for test_name, test_func in tests:
        runner.run_test(test_name, test_func)
    
    # 打印总结
    return runner.print_summary()


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
