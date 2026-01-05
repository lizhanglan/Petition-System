
import httpx
import asyncio
from typing import Optional, Dict, Any
from app.core.config import settings

class DeepSeekService:
    """DeepSeek API 服务"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL
        self.retry_times = settings.API_RETRY_TIMES
        self.retry_delays = settings.API_RETRY_DELAYS_LIST
        self.timeout = settings.API_TIMEOUT
    
    async def _call_api(self, messages: list, temperature: float = 0.7) -> Optional[str]:
        """调用 DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            print(f"[DeepSeek] Calling API: {self.api_base}/chat/completions")
            print(f"[DeepSeek] Model: {self.model}, Temperature: {temperature}")
            print(f"[DeepSeek] Messages count: {len(messages)}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                print(f"[DeepSeek] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(f"[DeepSeek] Success: {len(content)} characters")
                    return content
                else:
                    error_msg = f"API call failed: {response.status_code} - {response.text}"
                    print(f"[DeepSeek] Error: {error_msg}")
                    raise Exception(error_msg)
        except httpx.TimeoutException as e:
            error_msg = f"API call timeout after {self.timeout} seconds"
            print(f"[DeepSeek] Timeout: {error_msg}")
            raise Exception(error_msg)
        except httpx.ConnectError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"[DeepSeek] Connection error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[DeepSeek] Unexpected error: {error_msg}")
            raise
    
    async def call_with_retry(self, messages: list, temperature: float = 0.7) -> Optional[str]:
        """带重试机制的 API 调用"""
        last_error = None
        for attempt in range(self.retry_times):
            try:
                result = await self._call_api(messages, temperature)
                return result
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else repr(e)
                print(f"API call attempt {attempt + 1} failed: [{error_type}] {error_msg}")
                
                # 打印详细的错误信息
                import traceback
                traceback.print_exc()
                
                if attempt < self.retry_times - 1:
                    delay = self.retry_delays[attempt] / 1000  # 转换为秒
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败了
        error_type = type(last_error).__name__ if last_error else "Unknown"
        error_msg = str(last_error) if last_error and str(last_error) else repr(last_error)
        print(f"All {self.retry_times} API call attempts failed. Last error: [{error_type}] {error_msg}")
        return None
    
    async def review_document(self, content: str) -> Optional[str]:
        """文档研判 - 返回JSON字符串"""
        system_prompt = """你是信访文书审核专家，严格遵循《党政机关公文格式》《党政机关公文处理工作条例》《信访业务术语（2023年版）》。

请对文书进行全面审核，包括：
1. 内容合规性：错别字、术语规范、语义准确、诉求完整、法规真实性
2. 格式规范性：文号、排版、页眉页脚、落款格式

**重要：必须严格按照以下JSON格式返回，不要添加任何其他文字：**

{
  "summary": "总体评价文字，简明扼要地说明文档的整体质量和主要问题",
  "errors": [
    {
      "description": "问题的详细描述",
      "suggestion": "具体的修改建议",
      "reference": "相关的法律法规依据（可选）"
    }
  ]
}

如果没有发现问题，errors数组为空即可。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请审核以下文书：\n\n{content[:3000]}"}  # 限制长度避免超时
        ]
        
        result = await self.call_with_retry(messages, temperature=0.3)
        
        if result:
            # 尝试清理可能的markdown代码块标记
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            print(f"[DeepSeek] Cleaned result: {result[:200]}...")
        
        return result
    
    async def generate_document(
        self, 
        prompt: str, 
        template_info: Dict[str, Any], 
        context: list = None,
        file_context: str = None
    ) -> Optional[str]:
        """生成文书（支持多轮对话和文件引用）- 返回JSON格式"""
        system_prompt = f"""你是信访文书生成专家，严格遵循《党政机关公文格式》规范。

当前使用模板：{template_info.get('name', '未知模板')}
模板类型：{template_info.get('document_type', '未知类型')}

**重要：必须严格按照以下JSON格式返回，不要添加任何其他文字：**

{{
  "chat_message": "简短的对话回复，告诉用户生成了什么内容，有什么特点或建议（50-100字）",
  "document_content": "完整的文书正文内容，按照公文格式编排的纯文本",
  "summary": "文书的简要摘要（30-50字）",
  "suggestions": ["建议1", "建议2", "建议3"]
}}

**关键要求 - document_content字段：**
1. 必须是纯文本格式，不能包含任何JSON标记、引号、转义符
2. 按照标准公文格式编排：
   - 标题单独一行，居中
   - 正文段落之间用空行分隔
   - 每段首行缩进两个全角空格（　　）
   - 落款右对齐（使用适当空格）
   - 日期格式：YYYY年MM月DD日
3. 示例格式：

关于XXX的请求

　　尊敬的XXX：

　　根据您的来信，我们对XXX问题进行了认真研究。经核实，XXX情况属实。

　　针对您反映的问题，我们建议：一是XXX；二是XXX。

　　特此回复。

                                                    XXX单位
                                                    2024年1月4日

其他说明：
- chat_message: 用于对话显示，简要说明生成内容
- summary: 文书摘要
- suggestions: 改进建议列表（可选）
- 如发现需求信息不足，在chat_message中说明
- 如有参考文件，结合参考内容生成"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加文件引用上下文
        if file_context:
            messages.append({
                "role": "system",
                "content": f"用户提供的参考文件内容：\n{file_context}"
            })
        
        # 添加历史对话上下文（最多20条消息）
        if context:
            messages.extend(context[-20:])
        
        messages.append({"role": "user", "content": prompt})
        
        result = await self.call_with_retry(messages, temperature=0.7)
        
        if result:
            # 清理可能的markdown代码块标记
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            print(f"[DeepSeek] Cleaned generate result: {result[:200]}...")
        
        return result
    
    async def extract_template(self, content: str, file_type: str) -> Optional[Dict[str, Any]]:
        """提取模板结构"""
        system_prompt = """你是信访文书模板提取专家。请分析文书并提取模板结构。

返回 JSON 格式，包含：
- document_type: 文书类型
- fields: 字段列表，每个字段包含 id, name, type(text/date/number), required, default_value
- structure: 文书结构描述
- fixed_parts: 固定格式部分（文号规则、落款格式等）"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"文件类型：{file_type}\n\n文书内容：\n{content}"}
        ]
        
        return await self.call_with_retry(messages, temperature=0.3)
    
    async def verify_regulation(self, regulation_text: str) -> Optional[Dict[str, Any]]:
        """验证法规真实性（联网查询）"""
        system_prompt = """你是法规查询专家。请验证给定法规/政策的真实性和有效性。

返回 JSON 格式，包含：
- is_valid: 是否真实有效
- source: 来源链接
- level: 效力层级（法律/行政法规/部门规章等）
- status: 现行状态（现行/已废止/已修订）
- note: 说明"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请验证以下法规：{regulation_text}"}
        ]
        
        return await self.call_with_retry(messages, temperature=0.3)
    
    async def identify_template_fields(self, document_text: str) -> Optional[Dict[str, Any]]:
        """
        识别文档中的可变字段并生成占位符映射
        
        Args:
            document_text: 文档纯文本内容
            
        Returns:
            包含 fields 和 replacements 的字典
        """
        system_prompt = """你是信访文书模板分析专家。请分析文档内容，识别其中可能需要替换的可变字段（如姓名、日期、编号、单位名称等）。

**重要：必须严格按照以下 JSON 格式返回，不要添加任何其他文字：**

{
  "fields": {
    "variable_name": {
      "label": "中文字段名",
      "type": "text",
      "required": true,
      "description": "字段说明"
    }
  },
  "replacements": {
    "原文中的完整占位符": "{{ variable_name }}"
  }
}

**关键规则：**
1. variable_name 必须使用英文命名（如 petitioner_name, petition_date）
2. 占位符格式必须是 {{ variable_name }}（注意两边有空格）
3. **日期必须作为完整模式识别**：
   - 如果文档中有 "xx年xx月xx日" 或 "xxxx年xx月xx日"，应该将整个日期模式作为一个替换项
   - 例如："xx年xx月xx日" -> "{{ date }}"，而不是把 "xx" 单独替换
   - 同理："xxxx年xx月xx日" -> "{{ date }}"
4. **区分不同位置的相同占位符**：
   - 如果 "xx" 在不同位置表示不同含义（如姓名 vs 日期的年/月/日），应该识别完整的上下文模式
   - 姓名示例："xx（先生/女士）" 或 "xx先生" 整体替换
5. 识别以下类型的可变内容：
   - 人名（信访人、承办人等）
   - 日期（完整的日期格式，如 "xx年xx月xx日"）
   - 编号（信访编号、受理编号等）
   - 单位名称（承办单位、主管部门等）
6. 只识别确定需要替换的内容，固定模板文字不要替换
7. type 可选值：text, date, number

**示例1 - 完整日期：**
文档内容："将于xx年xx月xx日前办结"
应返回：
{
  "fields": {
    "deadline_date": {"label": "办结日期", "type": "date", "required": true}
  },
  "replacements": {
    "xx年xx月xx日": "{{ deadline_date }}"
  }
}

**示例2 - 区分姓名和日期：**
文档内容："xx（先生/女士）：您于xx年xx月xx日提出的信访事项..."
应返回：
{
  "fields": {
    "petitioner_name": {"label": "信访人姓名", "type": "text", "required": true},
    "petition_date": {"label": "信访日期", "type": "date", "required": true}
  },
  "replacements": {
    "xx（先生/女士）": "{{ petitioner_name }}",
    "xx年xx月xx日": "{{ petition_date }}"
  }
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下文档并识别可变字段：\n\n{document_text[:4000]}"}  # 限制长度
        ]
        
        result = await self.call_with_retry(messages, temperature=0.3)
        
        if result:
            # 清理可能的 markdown 代码块标记
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            try:
                import json
                data = json.loads(result)
                data["success"] = True
                return data
            except json.JSONDecodeError as e:
                print(f"[DeepSeek] JSON parse error: {e}")
                return {"success": False, "error": "AI 返回格式错误"}
        
        return {"success": False, "error": "AI 调用失败"}
    
    async def generate_field_values(
        self, 
        fields: Dict[str, Any], 
        prompt: str, 
        context: list = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据用户需求和对话上下文生成字段值
        
        Args:
            fields: 模板字段定义
            prompt: 用户输入的需求
            context: 对话历史
            
        Returns:
            字段值字典
        """
        # 构建字段说明
        field_descriptions = []
        for name, info in fields.items():
            label = info.get("label", name)
            field_type = info.get("type", "text")
            required = "必填" if info.get("required") else "选填"
            field_descriptions.append(f"- {name} ({label}): {field_type}, {required}")
        
        system_prompt = f"""你是信访文书生成助手。根据用户需求生成文书字段值。

**需要填写的字段：**
{chr(10).join(field_descriptions)}

**重要：必须严格按照以下 JSON 格式返回，不要添加任何其他文字：**

{{
  "chat_message": "对话回复（告诉用户生成了什么、还需要什么信息）",
  "field_values": {{
    "field_name": "字段值",
    ...
  }},
  "complete": true/false
}}

**规则：**
1. field_values 中的 key 必须和字段定义中的 variable_name 完全一致
2. 如果用户提供的信息不足以填写所有必填字段，在 chat_message 中询问
3. complete 表示是否所有必填字段都已填写
4. 日期格式使用：XXXX年XX月XX日"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.extend(context[-10:])  # 最多保留10条历史
        
        messages.append({"role": "user", "content": prompt})
        
        result = await self.call_with_retry(messages, temperature=0.7)
        
        if result:
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            try:
                import json
                data = json.loads(result)
                data["success"] = True
                return data
            except json.JSONDecodeError:
                return {"success": False, "error": "AI 返回格式错误"}
        
        return {"success": False, "error": "AI 调用失败"}

deepseek_service = DeepSeekService()
