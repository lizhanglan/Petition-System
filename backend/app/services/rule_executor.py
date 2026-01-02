"""
规则执行器

负责执行单个规则和规则集合
"""
import re
import time
from typing import List, Dict, Any, Optional
import logging

from app.models.validation import Rule, ValidationError, RuleType, ErrorType, ErrorLevel

logger = logging.getLogger(__name__)


class RuleResult:
    """规则执行结果"""
    
    def __init__(self, rule: Rule, passed: bool, errors: List[ValidationError], execution_time: float):
        self.rule = rule
        self.passed = passed
        self.errors = errors
        self.execution_time = execution_time


class RuleExecutor:
    """规则执行器"""
    
    def __init__(self):
        self.execution_times: Dict[str, List[float]] = {}
    
    async def execute_rule(self, rule: Rule, content: str, context: Dict[str, Any]) -> RuleResult:
        """
        执行单个规则
        
        Args:
            rule: 规则对象
            content: 文档内容
            context: 上下文信息（可能包含结构化数据）
            
        Returns:
            规则执行结果
        """
        start_time = time.time()
        errors = []
        
        try:
            if rule.rule_type == RuleType.PATTERN:
                errors = await self._execute_pattern_rule(rule, content, context)
            elif rule.rule_type == RuleType.LENGTH:
                errors = await self._execute_length_rule(rule, content, context)
            elif rule.rule_type == RuleType.KEYWORD:
                errors = await self._execute_keyword_rule(rule, content, context)
            elif rule.rule_type == RuleType.STRUCTURE:
                errors = await self._execute_structure_rule(rule, content, context)
            else:
                logger.warning(f"不支持的规则类型: {rule.rule_type}")
        
        except Exception as e:
            logger.error(f"规则执行失败 {rule.id}: {e}")
            errors = [ValidationError(
                type=rule.error_type,
                level=ErrorLevel.ERROR,
                description=f"规则执行错误: {str(e)}",
                reference=rule.id
            )]
        
        execution_time = time.time() - start_time
        
        # 记录执行时间
        if rule.id not in self.execution_times:
            self.execution_times[rule.id] = []
        self.execution_times[rule.id].append(execution_time)
        
        passed = len(errors) == 0
        return RuleResult(rule, passed, errors, execution_time)
    
    async def execute_rules(self, rules: List[Rule], content: str, context: Dict[str, Any] = None) -> List[RuleResult]:
        """
        执行规则集合
        
        Args:
            rules: 规则列表（应已按优先级排序）
            content: 文档内容
            context: 上下文信息
            
        Returns:
            规则执行结果列表
        """
        if context is None:
            context = {}
        
        results = []
        
        for rule in rules:
            result = await self.execute_rule(rule, content, context)
            results.append(result)
            
            # 如果是关键错误且检测到问题，立即停止
            if rule.critical and not result.passed:
                logger.warning(f"检测到关键错误，停止执行: {rule.id}")
                break
        
        return results
    
    async def _execute_pattern_rule(self, rule: Rule, content: str, context: Dict[str, Any]) -> List[ValidationError]:
        """执行正则表达式规则"""
        errors = []
        pattern = rule.parameters.get('pattern')
        field = rule.parameters.get('field')
        
        if not pattern:
            return errors
        
        try:
            # 如果指定了字段，从上下文中获取
            if field and field in context:
                text = str(context[field])
            else:
                text = content
            
            # 检查是否匹配
            if not re.search(pattern, text):
                errors.append(ValidationError(
                    type=rule.error_type,
                    level=rule.error_level,
                    position={"field": field} if field else None,
                    description=rule.description,
                    suggestion=rule.suggestion,
                    reference=rule.id
                ))
        
        except re.error as e:
            logger.error(f"正则表达式错误 {rule.id}: {e}")
        
        return errors
    
    async def _execute_length_rule(self, rule: Rule, content: str, context: Dict[str, Any]) -> List[ValidationError]:
        """执行长度检查规则"""
        errors = []
        min_length = rule.parameters.get('min_length')
        max_length = rule.parameters.get('max_length')
        
        content_length = len(content)
        
        if min_length and content_length < min_length:
            errors.append(ValidationError(
                type=rule.error_type,
                level=rule.error_level,
                description=f"{rule.description}（当前长度：{content_length}，最小要求：{min_length}）",
                suggestion=rule.suggestion,
                reference=rule.id
            ))
        
        if max_length and content_length > max_length:
            errors.append(ValidationError(
                type=rule.error_type,
                level=rule.error_level,
                description=f"{rule.description}（当前长度：{content_length}，最大限制：{max_length}）",
                suggestion=rule.suggestion,
                reference=rule.id
            ))
        
        return errors
    
    async def _execute_keyword_rule(self, rule: Rule, content: str, context: Dict[str, Any]) -> List[ValidationError]:
        """执行关键词检查规则"""
        errors = []
        keywords = rule.parameters.get('keywords', [])
        mode = rule.parameters.get('mode', 'required')  # required, prohibited, any_of
        
        if mode == 'required':
            # 检查必需关键词
            missing_keywords = []
            for keyword in keywords:
                if keyword not in content:
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                errors.append(ValidationError(
                    type=rule.error_type,
                    level=rule.error_level,
                    description=f"{rule.description}：缺少 {', '.join(missing_keywords)}",
                    suggestion=rule.suggestion,
                    reference=rule.id
                ))
        
        elif mode == 'prohibited':
            # 检查禁用关键词
            found_keywords = []
            for keyword in keywords:
                if keyword in content:
                    found_keywords.append(keyword)
            
            if found_keywords:
                errors.append(ValidationError(
                    type=rule.error_type,
                    level=rule.error_level,
                    description=f"{rule.description}：发现 {', '.join(found_keywords)}",
                    suggestion=rule.suggestion,
                    reference=rule.id
                ))
        
        elif mode == 'any_of':
            # 检查是否包含任意一个关键词
            found = any(keyword in content for keyword in keywords)
            if not found:
                errors.append(ValidationError(
                    type=rule.error_type,
                    level=rule.error_level,
                    description=rule.description,
                    suggestion=rule.suggestion,
                    reference=rule.id
                ))
        
        return errors
    
    async def _execute_structure_rule(self, rule: Rule, content: str, context: Dict[str, Any]) -> List[ValidationError]:
        """执行结构检查规则"""
        errors = []
        # 结构规则的具体实现取决于文档类型
        # 这里提供一个基础框架
        required_sections = rule.parameters.get('required_sections', [])
        
        for section in required_sections:
            if section not in content:
                errors.append(ValidationError(
                    type=rule.error_type,
                    level=rule.error_level,
                    description=f"{rule.description}：缺少章节 {section}",
                    suggestion=rule.suggestion,
                    reference=rule.id
                ))
        
        return errors
    
    def get_execution_time(self, rule_id: str) -> Optional[float]:
        """
        获取规则的平均执行时间
        
        Args:
            rule_id: 规则ID
            
        Returns:
            平均执行时间（秒），如果没有记录返回 None
        """
        if rule_id not in self.execution_times or not self.execution_times[rule_id]:
            return None
        
        times = self.execution_times[rule_id]
        return sum(times) / len(times)
    
    def get_slow_rules(self, threshold: float = 0.5) -> List[tuple[str, float]]:
        """
        获取慢规则列表
        
        Args:
            threshold: 阈值（秒），默认0.5秒
            
        Returns:
            (规则ID, 平均执行时间) 列表
        """
        slow_rules = []
        
        for rule_id, times in self.execution_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > threshold:
                    slow_rules.append((rule_id, avg_time))
        
        # 按执行时间降序排序
        slow_rules.sort(key=lambda x: x[1], reverse=True)
        return slow_rules
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        metrics = {
            "total_rules": len(self.execution_times),
            "rules": {}
        }
        
        for rule_id, times in self.execution_times.items():
            if times:
                metrics["rules"][rule_id] = {
                    "executions": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return metrics
