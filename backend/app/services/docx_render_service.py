"""
docxtpl 渲染服务
使用 docxtpl 库渲染 Word 模板，生成最终文档
"""
import io
from typing import Dict, Any, Optional
from docxtpl import DocxTemplate


class DocxRenderService:
    """docxtpl 渲染服务"""
    
    def __init__(self):
        pass
    
    async def render_template(
        self,
        template_bytes: bytes,
        context: Dict[str, Any]
    ) -> bytes:
        """
        渲染 Word 模板
        
        Args:
            template_bytes: 模板文件二进制内容
            context: 渲染数据字典
            
        Returns:
            渲染后的 Word 文档二进制
        """
        try:
            # 加载模板
            doc = DocxTemplate(io.BytesIO(template_bytes))
            
            # 渲染
            doc.render(context)
            
            # 保存到内存
            buffer = io.BytesIO()
            doc.save(buffer)
            
            return buffer.getvalue()
            
        except Exception as e:
            print(f"[DocxRender] Render error: {e}")
            raise Exception(f"模板渲染失败: {str(e)}")
    
    async def validate_context(
        self,
        fields: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证渲染数据是否完整
        
        Args:
            fields: 模板字段定义
            context: 待验证的数据字典
            
        Returns:
            验证结果
        """
        missing_fields = []
        
        for field_name, field_info in fields.items():
            if field_info.get("required", False):
                if field_name not in context or not context[field_name]:
                    missing_fields.append({
                        "name": field_name,
                        "label": field_info.get("label", field_name)
                    })
        
        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }
    
    def get_template_variables(self, template_bytes: bytes) -> list:
        """
        获取模板中的所有变量名
        
        Args:
            template_bytes: 模板文件二进制
            
        Returns:
            变量名列表
        """
        try:
            doc = DocxTemplate(io.BytesIO(template_bytes))
            # 使用 docxtpl 的内置方法获取未声明的变量
            variables = doc.get_undeclared_template_variables()
            return list(variables)
        except Exception as e:
            print(f"[DocxRender] Get variables error: {e}")
            return []


# 创建全局实例
docx_render_service = DocxRenderService()
