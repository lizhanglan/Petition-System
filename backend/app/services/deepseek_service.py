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
        """生成文书（支持多轮对话和文件引用）"""
        system_prompt = f"""你是信访文书生成专家，严格遵循《党政机关公文格式》规范。
当前使用模板：{template_info.get('name', '未知模板')}
模板类型：{template_info.get('document_type', '未知类型')}

请根据用户需求生成符合规范的文书正文内容。注意：
1. 仅生成正文内容，不包含模板固定格式部分
2. 确保内容合规、语言规范、逻辑清晰
3. 如发现需求中信息缺失或错误，在回复末尾说明
4. 如果用户提供了参考文件，请结合参考文件内容生成"""
        
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
        
        return await self.call_with_retry(messages, temperature=0.7)
    
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

deepseek_service = DeepSeekService()
