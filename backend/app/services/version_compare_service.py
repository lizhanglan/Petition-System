"""
版本对比服务
实现文档版本间的差异对比功能
"""
import difflib
from typing import Dict, List, Any, Optional
from datetime import datetime


class VersionCompareService:
    """版本对比服务"""
    
    @staticmethod
    def compare_text(text1: str, text2: str) -> Dict[str, Any]:
        """
        文本级差异对比
        
        Args:
            text1: 旧版本文本
            text2: 新版本文本
            
        Returns:
            差异对比结果
        """
        # 按行分割文本
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        # 生成差异
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))
        
        # 统计变更
        added_lines = [line[2:] for line in diff if line.startswith('+ ')]
        removed_lines = [line[2:] for line in diff if line.startswith('- ')]
        unchanged_lines = [line[2:] for line in diff if line.startswith('  ')]
        
        # 生成 HTML 差异视图
        html_diff = difflib.HtmlDiff().make_table(
            lines1, 
            lines2,
            fromdesc='旧版本',
            todesc='新版本',
            context=True,
            numlines=3
        )
        
        # 计算相似度
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        return {
            'added_lines': added_lines,
            'removed_lines': removed_lines,
            'unchanged_lines': unchanged_lines,
            'added_count': len(added_lines),
            'removed_count': len(removed_lines),
            'unchanged_count': len(unchanged_lines),
            'similarity': round(similarity * 100, 2),
            'html_diff': html_diff,
            'diff_summary': f"新增 {len(added_lines)} 行，删除 {len(removed_lines)} 行"
        }
    
    @staticmethod
    def compare_fields(fields1: Dict[str, Any], fields2: Dict[str, Any]) -> Dict[str, Any]:
        """
        字段级差异对比
        
        Args:
            fields1: 旧版本字段
            fields2: 新版本字段
            
        Returns:
            字段差异对比结果
        """
        # 获取所有字段键
        all_keys = set(fields1.keys()) | set(fields2.keys())
        
        # 分类字段变更
        added_fields = {}
        removed_fields = {}
        modified_fields = {}
        unchanged_fields = {}
        
        for key in all_keys:
            if key not in fields1:
                # 新增字段
                added_fields[key] = fields2[key]
            elif key not in fields2:
                # 删除字段
                removed_fields[key] = fields1[key]
            elif fields1[key] != fields2[key]:
                # 修改字段
                modified_fields[key] = {
                    'old_value': fields1[key],
                    'new_value': fields2[key],
                    'diff': VersionCompareService._get_field_diff(fields1[key], fields2[key])
                }
            else:
                # 未变更字段
                unchanged_fields[key] = fields1[key]
        
        return {
            'added_fields': added_fields,
            'removed_fields': removed_fields,
            'modified_fields': modified_fields,
            'unchanged_fields': unchanged_fields,
            'added_count': len(added_fields),
            'removed_count': len(removed_fields),
            'modified_count': len(modified_fields),
            'unchanged_count': len(unchanged_fields),
            'change_summary': f"新增 {len(added_fields)} 个字段，删除 {len(removed_fields)} 个字段，修改 {len(modified_fields)} 个字段"
        }
    
    @staticmethod
    def _get_field_diff(value1: Any, value2: Any) -> str:
        """
        获取单个字段的差异描述
        
        Args:
            value1: 旧值
            value2: 新值
            
        Returns:
            差异描述
        """
        if isinstance(value1, str) and isinstance(value2, str):
            # 字符串类型，计算相似度
            similarity = difflib.SequenceMatcher(None, value1, value2).ratio()
            if similarity > 0.8:
                return f"轻微修改 (相似度: {round(similarity * 100, 2)}%)"
            else:
                return f"大幅修改 (相似度: {round(similarity * 100, 2)}%)"
        else:
            # 其他类型，直接比较
            return f"从 '{value1}' 改为 '{value2}'"
    
    @staticmethod
    def compare_versions(
        version1: Dict[str, Any],
        version2: Dict[str, Any],
        compare_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        完整版本对比
        
        Args:
            version1: 旧版本数据
            version2: 新版本数据
            compare_type: 对比类型 ('full', 'text', 'fields')
            
        Returns:
            完整的对比结果
        """
        result = {
            'version1_number': version1.get('version_number'),
            'version2_number': version2.get('version_number'),
            'compare_type': compare_type,
            'compared_at': datetime.now().isoformat()
        }
        
        # 文本对比
        if compare_type in ['full', 'text']:
            text1 = version1.get('content', '')
            text2 = version2.get('content', '')
            result['text_diff'] = VersionCompareService.compare_text(text1, text2)
        
        # 字段对比
        if compare_type in ['full', 'fields']:
            fields1 = version1.get('structured_content', {})
            fields2 = version2.get('structured_content', {})
            result['fields_diff'] = VersionCompareService.compare_fields(fields1, fields2)
        
        # 元数据对比
        result['metadata'] = {
            'version1_created_at': version1.get('created_at'),
            'version2_created_at': version2.get('created_at'),
            'version1_description': version1.get('change_description'),
            'version2_description': version2.get('change_description'),
            'is_rollback': version2.get('is_rollback', 0) == 1
        }
        
        return result
    
    @staticmethod
    def generate_diff_summary(diff_result: Dict[str, Any]) -> str:
        """
        生成差异摘要
        
        Args:
            diff_result: 差异对比结果
            
        Returns:
            差异摘要文本
        """
        summary_parts = []
        
        # 文本差异摘要
        if 'text_diff' in diff_result:
            text_diff = diff_result['text_diff']
            summary_parts.append(
                f"文本变更：{text_diff['diff_summary']}，相似度 {text_diff['similarity']}%"
            )
        
        # 字段差异摘要
        if 'fields_diff' in diff_result:
            fields_diff = diff_result['fields_diff']
            summary_parts.append(
                f"字段变更：{fields_diff['change_summary']}"
            )
        
        # 版本信息
        summary_parts.append(
            f"版本对比：V{diff_result['version1_number']} → V{diff_result['version2_number']}"
        )
        
        return "；".join(summary_parts)
    
    @staticmethod
    def get_change_highlights(diff_result: Dict[str, Any], max_items: int = 5) -> List[Dict[str, str]]:
        """
        获取主要变更亮点
        
        Args:
            diff_result: 差异对比结果
            max_items: 最多返回的亮点数量
            
        Returns:
            变更亮点列表
        """
        highlights = []
        
        # 字段变更亮点
        if 'fields_diff' in diff_result:
            fields_diff = diff_result['fields_diff']
            
            # 新增字段
            for key, value in list(fields_diff['added_fields'].items())[:max_items]:
                highlights.append({
                    'type': 'added',
                    'field': key,
                    'description': f"新增字段 '{key}': {value}"
                })
            
            # 删除字段
            for key, value in list(fields_diff['removed_fields'].items())[:max_items]:
                highlights.append({
                    'type': 'removed',
                    'field': key,
                    'description': f"删除字段 '{key}': {value}"
                })
            
            # 修改字段
            for key, change in list(fields_diff['modified_fields'].items())[:max_items]:
                highlights.append({
                    'type': 'modified',
                    'field': key,
                    'description': f"修改字段 '{key}': {change['diff']}"
                })
        
        return highlights[:max_items]


# 创建全局实例
version_compare_service = VersionCompareService()
