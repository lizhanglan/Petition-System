from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.rate_limiter import ai_rate_limit, user_rate_limit
from app.models.user import User
from app.models.document import Document
from app.models.file import File
from app.models.audit_log import AuditLog
from app.models.version import Version
from app.api.v1.endpoints.auth import get_current_user
from app.services.deepseek_service import deepseek_service
from app.services.file_parser_service import file_parser_service
from app.services.document_export_service import document_export_service
from app.services.conversation_service import conversation_service
from app.services.health_monitor_service import get_health_monitor
from app.services.local_rules_engine import get_local_rules_engine
from app.core.minio_client import minio_client
from pydantic import BaseModel
from fastapi.responses import Response
import json

router = APIRouter()

class DocumentReviewRequest(BaseModel):
    file_id: int

class DocumentReviewResponse(BaseModel):
    document_id: int
    errors: List[dict]
    summary: str
    fallback_mode: Optional[bool] = False  # 新增：是否降级模式
    fallback_notice: Optional[str] = None  # 新增：降级通知
    estimated_recovery: Optional[int] = None  # 新增：预计恢复时间

class DocumentGenerateRequest(BaseModel):
    template_id: int
    prompt: str
    context: Optional[List[dict]] = None
    session_id: Optional[str] = None  # 新增：会话ID
    file_references: Optional[List[int]] = None  # 新增：文件引用

class ConversationHistoryResponse(BaseModel):
    messages: List[dict]
    session_info: dict

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    document_type: str
    status: str
    classification: Optional[str] = "public"  # 新增：密级
    ai_annotations: Optional[dict]
    preview_url: Optional[str] = None  # 新增：预览URL
    created_at: datetime

class DocumentUpdateRequest(BaseModel):
    content: Optional[str] = None
    structured_content: Optional[dict] = None
    title: Optional[str] = None
    status: Optional[str] = None
    classification: Optional[str] = None  # 新增：密级
    change_description: Optional[str] = None

class ClassificationUpdateRequest(BaseModel):
    classification: str  # public, internal, confidential, secret, top_secret

@router.post("/review", response_model=DocumentReviewResponse)
@ai_rate_limit
async def review_document(
    request: DocumentReviewRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 文档研判"""
    # 获取文件
    result = await db.execute(
        select(File).where(File.id == request.file_id, File.user_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    print(f"[Review] Starting review for file: {file.file_name} (type: {file.file_type})")
    
    # 从 MinIO 读取文件内容
    file_bytes = await minio_client.download_file(file.storage_path)
    if not file_bytes:
        raise HTTPException(status_code=500, detail="无法读取文件内容")
    
    print(f"[Review] File downloaded: {len(file_bytes)} bytes")
    
    # 解析文件内容
    parsed_data = await file_parser_service.parse_file(file_bytes, file.file_type)
    if not parsed_data:
        raise HTTPException(status_code=500, detail="文件解析失败，请确保文件格式正确")
    
    file_content = parsed_data.get('text', '')
    if not file_content.strip():
        raise HTTPException(status_code=400, detail="文件内容为空，无法进行研判")
    
    print(f"[Review] File parsed: {len(file_content)} characters")
    
    # 检查是否需要使用降级模式
    health_monitor = get_health_monitor()
    local_engine = get_local_rules_engine()
    use_fallback = False
    fallback_reason = None
    
    if health_monitor and health_monitor.is_fallback_mode():
        use_fallback = True
        fallback_reason = "AI 服务当前不可用，使用本地规则库进行基础校验"
        print(f"[Review] 使用降级模式: {fallback_reason}")
    
    # 执行研判
    review_data = None
    
    if use_fallback and local_engine:
        # 使用本地规则引擎
        print(f"[Review] 使用本地规则引擎进行验证...")
        try:
            validation_result = await local_engine.validate_document(file_content, parsed_data)
            
            # 转换为统一格式
            review_data = {
                "errors": [error.dict() for error in validation_result.errors],
                "summary": validation_result.summary
            }
            
            print(f"[Review] 本地规则验证完成: {len(validation_result.errors)} 个问题")
            
        except Exception as e:
            print(f"[Review] 本地规则引擎失败: {e}")
            # 如果本地引擎也失败，尝试 AI 服务
            use_fallback = False
    
    if not use_fallback:
        # 调用 AI 研判
        print(f"[Review] Calling AI service for review...")
        try:
            review_result = await deepseek_service.review_document(file_content)
            
            if not review_result:
                # AI 服务失败，尝试降级
                if local_engine:
                    print(f"[Review] AI 服务失败，降级到本地规则引擎...")
                    use_fallback = True
                    fallback_reason = "AI 服务调用失败，已切换到本地规则库"
                    
                    validation_result = await local_engine.validate_document(file_content, parsed_data)
                    review_data = {
                        "errors": [error.dict() for error in validation_result.errors],
                        "summary": validation_result.summary
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="AI 研判服务暂时不可用，且本地规则库未初始化。请稍后重试。"
                    )
            else:
                # 解析 AI 返回结果
                print(f"[Review] Parsing AI result...")
                try:
                    review_data = json.loads(review_result)
                    print(f"[Review] JSON parsed successfully")
                    
                    # 确保数据结构正确
                    if not isinstance(review_data, dict):
                        raise ValueError("AI返回的不是有效的JSON对象")
                    
                    if "errors" not in review_data:
                        review_data["errors"] = []
                    
                    if "summary" not in review_data:
                        review_data["summary"] = "研判完成"
                    
                    # 确保errors是列表
                    if not isinstance(review_data["errors"], list):
                        review_data["errors"] = []
                    
                    print(f"[Review] Parsed data: summary={review_data['summary'][:50]}..., errors_count={len(review_data['errors'])}")
                    
                except json.JSONDecodeError as e:
                    print(f"[Review] JSON解析失败: {e}")
                    print(f"[Review] AI返回内容: {review_result[:500]}...")
                    
                    # JSON解析失败，将整个返回作为summary
                    review_data = {
                        "errors": [],
                        "summary": review_result
                    }
                except Exception as e:
                    print(f"[Review] 数据处理失败: {e}")
                    review_data = {
                        "errors": [],
                        "summary": review_result if isinstance(review_result, str) else "研判完成"
                    }
        
        except Exception as e:
            print(f"[Review] AI 服务异常: {e}")
            # 尝试降级
            if local_engine:
                print(f"[Review] 降级到本地规则引擎...")
                use_fallback = True
                fallback_reason = f"AI 服务异常（{str(e)}），已切换到本地规则库"
                
                validation_result = await local_engine.validate_document(file_content, parsed_data)
                review_data = {
                    "errors": [error.dict() for error in validation_result.errors],
                    "summary": validation_result.summary
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI 研判服务异常: {str(e)}"
                )
    
    print(f"[Review] Review completed, fallback_mode: {use_fallback}")
    
    # 确保数据结构正确
    if not isinstance(review_data.get("errors"), list):
        review_data["errors"] = []
    if not review_data.get("summary"):
        review_data["summary"] = "研判完成"
    
    # 创建文档记录
    document = Document(
        user_id=current_user.id,
        file_id=file.id,
        title=file.file_name,
        content=file_content,
        structured_content=parsed_data,
        document_type="petition",
        status="reviewed",
        ai_annotations=review_data
    )
    db.add(document)
    
    # 更新文件状态
    file.status = "reviewed"
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="review",
        resource_type="document",
        details={
            "file_id": file.id,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "content_length": len(file_content),
            "errors_count": len(review_data.get("errors", []))
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(document)
    
    # 创建初始版本（版本 1）
    version = Version(
        document_id=document.id,
        user_id=current_user.id,
        version_number=1,
        content=file_content,
        structured_content=parsed_data,
        change_description="初始版本 - AI 研判完成",
        is_rollback=0
    )
    db.add(version)
    await db.commit()
    
    print(f"[Review] Review completed for document ID: {document.id}, version 1 created")
    
    # 准备响应
    response = DocumentReviewResponse(
        document_id=document.id,
        errors=review_data.get("errors", []),
        summary=review_data.get("summary", "")
    )
    
    # 添加降级信息
    if use_fallback:
        response.fallback_mode = True
        response.fallback_notice = fallback_reason
        if health_monitor:
            response.estimated_recovery = health_monitor.get_estimated_recovery_time()
        
        # 记录降级事件到审计日志
        fallback_log = AuditLog(
            user_id=current_user.id,
            action="fallback_review",
            resource_type="document",
            details={
                "file_id": file.id,
                "file_name": file.file_name,
                "fallback_reason": fallback_reason,
                "errors_count": len(review_data.get("errors", []))
            }
        )
        db.add(fallback_log)
        await db.commit()
    
    return response

@router.post("/generate", response_model=DocumentResponse)
@ai_rate_limit
async def generate_document(
    request: DocumentGenerateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 生成文书（支持多轮对话）"""
    print(f"[Generate] Starting document generation for template ID: {request.template_id}")
    print(f"[Generate] Session ID: {request.session_id}")
    
    # 添加用户消息到对话历史
    conversation_service.add_message(
        user_id=current_user.id,
        role="user",
        content=request.prompt,
        session_id=request.session_id,
        metadata={"template_id": request.template_id}
    )
    
    # 处理文件引用
    if request.file_references:
        for file_id in request.file_references:
            conversation_service.add_file_reference(
                user_id=current_user.id,
                file_id=file_id,
                session_id=request.session_id
            )
    
    # 获取模板
    from app.models.template import Template
    result = await db.execute(
        select(Template).where(Template.id == request.template_id, Template.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    print(f"[Generate] Template found: {template.name}")
    
    # 准备模板信息
    template_info = {
        "name": template.name,
        "document_type": template.document_type,
        "fields": template.fields or {},
        "structure": template.structure or {}
    }
    
    # 获取对话上下文（使用服务管理的上下文）
    context = conversation_service.get_context_for_ai(
        user_id=current_user.id,
        session_id=request.session_id
    )
    
    print(f"[Generate] Using conversation context: {len(context)} messages")
    
    # 获取文件引用内容
    file_context = ""
    file_refs = conversation_service.get_file_references(
        user_id=current_user.id,
        session_id=request.session_id
    )
    
    if file_refs:
        print(f"[Generate] Loading {len(file_refs)} referenced files")
        for file_id in file_refs:
            result = await db.execute(
                select(File).where(File.id == file_id, File.user_id == current_user.id)
            )
            file = result.scalar_one_or_none()
            if file:
                # 读取文件内容
                file_bytes = await minio_client.download_file(file.storage_path)
                if file_bytes:
                    parsed_data = await file_parser_service.parse_file(file_bytes, file.file_type)
                    if parsed_data and parsed_data.get('text'):
                        file_context += f"\n\n--- 参考文件：{file.file_name} ---\n{parsed_data['text'][:1000]}"  # 限制长度
    
    # 调用 AI 生成
    print(f"[Generate] Calling AI with prompt length: {len(request.prompt)}")
    ai_response = await deepseek_service.generate_document(
        request.prompt,
        template_info,
        context,
        file_context=file_context if file_context else None
    )
    
    if not ai_response:
        # 添加失败消息到对话历史
        conversation_service.add_message(
            user_id=current_user.id,
            role="assistant",
            content="抱歉，生成失败，请稍后重试。",
            session_id=request.session_id
        )
        raise HTTPException(status_code=500, detail="AI 生成失败，请稍后重试")
    
    print(f"[Generate] AI response received, length: {len(ai_response)}")
    
    # 解析AI返回的JSON格式
    chat_message = ""
    document_content = ""
    summary = ""
    suggestions = []
    
    try:
        ai_data = json.loads(ai_response)
        print(f"[Generate] JSON parsed successfully")
        
        # 提取各个字段
        chat_message = ai_data.get("chat_message", "")
        document_content = ai_data.get("document_content", "")
        summary = ai_data.get("summary", "")
        suggestions = ai_data.get("suggestions", [])
        
        # 清理document_content中可能的JSON标记
        if document_content:
            # 移除可能的JSON字段标记
            import re
            # 移除类似 "document_content": 这样的标记
            document_content = re.sub(r'"document_content"\s*:\s*"', '', document_content)
            # 移除可能的转义引号
            document_content = document_content.replace('\\"', '"')
            document_content = document_content.replace('\\n', '\n')
            # 移除开头和结尾的引号
            document_content = document_content.strip('"')
            # 移除可能的JSON对象标记
            if document_content.startswith('{') and document_content.endswith('}'):
                # 尝试再次解析，看是否是嵌套的JSON
                try:
                    nested_data = json.loads(document_content)
                    if isinstance(nested_data, dict) and 'document_content' in nested_data:
                        document_content = nested_data['document_content']
                except:
                    pass  # 不是嵌套JSON，保持原样
        
        # 确保document_content不为空
        if not document_content or len(document_content.strip()) < 10:
            print(f"[Generate] Warning: document_content is empty or too short, using full response")
            document_content = ai_response
            chat_message = "已生成文书内容"
        
        print(f"[Generate] Parsed - chat_message: {len(chat_message)} chars, document_content: {len(document_content)} chars")
        print(f"[Generate] Document content preview: {document_content[:200]}...")
        
    except json.JSONDecodeError as e:
        print(f"[Generate] JSON解析失败: {e}")
        print(f"[Generate] AI返回内容: {ai_response[:500]}...")
        
        # JSON解析失败，使用整个返回作为文档内容
        document_content = ai_response
        chat_message = f"已生成文书，共 {len(ai_response)} 字。"
        
    except Exception as e:
        print(f"[Generate] 数据处理失败: {e}")
        document_content = ai_response if isinstance(ai_response, str) else ""
        chat_message = "文书已生成"
    
    # 添加 AI 回复到对话历史（使用chat_message）
    conversation_service.add_message(
        user_id=current_user.id,
        role="assistant",
        content=chat_message,
        session_id=request.session_id,
        metadata={
            "content_length": len(document_content),
            "summary": summary,
            "suggestions": suggestions
        }
    )
    
    # 解析生成的内容，尝试提取结构化字段
    structured_content = _parse_generated_content(document_content, template.fields or {})
    
    # 填充模板
    final_content = _fill_template(template.content_template, structured_content, document_content)
    
    # 创建文档记录
    document = Document(
        user_id=current_user.id,
        template_id=template.id,
        title=f"{template.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        content=final_content,
        structured_content=structured_content,
        document_type=template.document_type,
        status="draft"
    )
    db.add(document)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="generate",
        resource_type="document",
        details={
            "template_id": template.id,
            "template_name": template.name,
            "prompt_length": len(request.prompt),
            "content_length": len(final_content),
            "session_id": request.session_id,
            "context_messages": len(context),
            "file_references": len(file_refs) if file_refs else 0
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(document)
    
    # 创建初始版本（版本 1）
    version = Version(
        document_id=document.id,
        user_id=current_user.id,
        version_number=1,
        content=final_content,
        structured_content=structured_content,
        change_description="初始版本 - AI 生成完成",
        is_rollback=0
    )
    db.add(version)
    await db.commit()
    
    print(f"[Generate] Document created with ID: {document.id}, version 1 created")
    
    # 生成预览URL（优先使用WPS服务，降级到华为云）
    from app.core.minio_client import minio_client
    from app.services.preview_service_selector import preview_service_selector
    
    # 先将文档内容保存为临时文件到MinIO
    temp_filename = f"temp_preview/{current_user.id}/{document.id}.docx"
    
    # 使用document_export_service生成DOCX文件
    from app.services.document_export_service import document_export_service
    docx_bytes = await document_export_service.export_to_docx(
        content=final_content,
        title=document.title,
        options={"document_type": document.document_type}
    )
    
    # 上传到MinIO
    await minio_client.upload_file(
        temp_filename,
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    # 获取预览URL（优先WPS，降级到华为云）
    # 生成的文档默认可编辑
    file_url = minio_client.get_file_url(temp_filename, expires=3600, inline=True)
    preview_result = await preview_service_selector.get_preview_url(
        file_url=file_url,
        file_name=f"{document.title}.docx",
        user_id=str(current_user.id),
        permission="edit"  # 改为可编辑模式
    )
    
    preview_url = preview_result.get("preview_url") if preview_result else None
    service_type = preview_result.get("service_type", "unsupported") if preview_result else "unsupported"
    
    print(f"[Generate] Preview service: {service_type}, URL: {preview_url}")
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        document_type=document.document_type,
        status=document.status,
        ai_annotations={
            "chat_message": chat_message,
            "summary": summary,
            "suggestions": suggestions
        },
        preview_url=preview_url,
        created_at=document.created_at
    )


def _parse_generated_content(content: str, fields: dict) -> dict:
    """
    从生成的内容中解析结构化字段
    
    Args:
        content: AI 生成的内容
        fields: 模板字段定义
        
    Returns:
        结构化字段字典
    """
    structured = {}
    
    # 简单的字段提取逻辑
    # 实际应用中可以使用更复杂的 NLP 技术
    for field_id, field_info in fields.items():
        field_name = field_info.get('name', field_id)
        
        # 尝试在内容中查找字段值
        # 例如：查找 "主送单位：XXX" 这样的模式
        import re
        pattern = f"{field_name}[：:](.*?)(?:\n|$)"
        match = re.search(pattern, content)
        
        if match:
            structured[field_id] = match.group(1).strip()
        else:
            # 使用默认值
            structured[field_id] = field_info.get('default_value', '')
    
    return structured


def _fill_template(template_content: str, structured_data: dict, ai_content: str) -> str:
    """
    填充模板内容
    
    Args:
        template_content: 模板内容（可能包含占位符）
        structured_data: 结构化数据
        ai_content: AI 生成的纯文本内容（已按公文格式编排）
        
    Returns:
        填充后的完整内容
    """
    if not template_content:
        # 如果没有模板内容，直接返回 AI 生成的内容（已格式化）
        return ai_content
    
    # 检查模板内容是否是JSON格式（提取模板的情况）
    # 如果是JSON格式，直接使用AI生成的内容
    template_stripped = template_content.strip()
    if template_stripped.startswith('{') and template_stripped.endswith('}'):
        try:
            import json
            json.loads(template_stripped)
            # 是有效的JSON，说明这是提取的模板规则，直接返回AI内容
            print(f"[FillTemplate] 检测到JSON格式模板，直接使用AI生成内容")
            return ai_content
        except:
            pass  # 不是有效JSON，继续正常处理
    
    # 替换占位符
    filled_content = template_content
    for field_id, value in structured_data.items():
        placeholder = f"{{{{{field_id}}}}}"  # {{field_id}} 格式
        filled_content = filled_content.replace(placeholder, str(value))
    
    # 替换主体内容占位符
    if "{{content}}" in filled_content:
        filled_content = filled_content.replace("{{content}}", ai_content)
    elif "{{正文}}" in filled_content:
        filled_content = filled_content.replace("{{正文}}", ai_content)
    else:
        # 如果没有内容占位符，追加到末尾
        filled_content = filled_content + "\n\n" + ai_content
    
    return filled_content

@router.get("/list", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文书列表"""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            document_type=doc.document_type,
            status=doc.status,
            ai_annotations=doc.ai_annotations,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文书详情"""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        document_type=document.document_type,
        status=document.status,
        ai_annotations=document.ai_annotations,
        created_at=document.created_at
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    format: str = 'pdf',
    include_watermark: bool = False,
    include_annotations: bool = False,
    security_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载文档
    
    Args:
        document_id: 文档 ID
        format: 导出格式（pdf 或 docx）
        include_watermark: 是否包含水印
        include_annotations: 是否保留 AI 标注
        security_level: 密级标注
    """
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    print(f"[Download] Exporting document ID: {document_id}, format: {format}")
    
    # 准备导出内容
    content = document.content
    
    # 如果需要保留 AI 标注
    if include_annotations and document.ai_annotations:
        annotations = document.ai_annotations
        if isinstance(annotations, dict) and annotations.get('errors'):
            content += "\n\n--- AI 研判意见 ---\n"
            for idx, error in enumerate(annotations['errors'], 1):
                content += f"\n{idx}. {error.get('description', '')}"
                if error.get('suggestion'):
                    content += f"\n   建议：{error['suggestion']}"
    
    # 准备导出选项
    export_options = {}
    
    if include_watermark:
        export_options['watermark'] = "信访智能文书生成系统"
    
    if security_level:
        export_options['security_level'] = security_level
    
    # 导出文档
    try:
        file_bytes = await document_export_service.export_document(
            content=content,
            title=document.title,
            format=format,
            options=export_options
        )
    except Exception as e:
        print(f"[Download] Export error: {e}")
        raise HTTPException(status_code=500, detail=f"文档导出失败: {str(e)}")
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="download",
        resource_type="document",
        resource_id=document_id,
        details={
            "document_title": document.title,
            "format": format,
            "include_watermark": include_watermark,
            "include_annotations": include_annotations,
            "file_size": len(file_bytes)
        }
    )
    db.add(audit_log)
    await db.commit()
    
    print(f"[Download] Document exported successfully: {len(file_bytes)} bytes")
    
    # 返回文件 - 处理中文文件名
    from urllib.parse import quote
    filename = f"{document.title}.{format}"
    # 对文件名进行URL编码以支持中文
    encoded_filename = quote(filename)
    media_type = "application/pdf" if format == 'pdf' else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文档并自动创建新版本"""
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 检查是否有实际变更
    has_changes = False
    old_content = document.content
    old_structured_content = document.structured_content
    
    # 更新文档字段
    if request.content is not None and request.content != document.content:
        document.content = request.content
        has_changes = True
    
    if request.structured_content is not None and request.structured_content != document.structured_content:
        document.structured_content = request.structured_content
        has_changes = True
    
    if request.title is not None:
        document.title = request.title
    
    if request.status is not None:
        document.status = request.status
    
    if request.classification is not None:
        document.classification = request.classification
    
    # 如果有内容变更，创建新版本
    if has_changes:
        # 获取当前最大版本号
        result = await db.execute(
            select(Version.version_number)
            .where(Version.document_id == document_id)
            .order_by(Version.version_number.desc())
            .limit(1)
        )
        max_version = result.scalar_one_or_none()
        next_version = (max_version or 0) + 1
        
        # 创建新版本
        version = Version(
            document_id=document_id,
            user_id=current_user.id,
            version_number=next_version,
            content=document.content,
            structured_content=document.structured_content,
            change_description=request.change_description or f"版本 {next_version} - 文档更新",
            is_rollback=0
        )
        db.add(version)
        
        print(f"[Update] Document {document_id} updated, version {next_version} created")
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update",
        resource_type="document",
        resource_id=document_id,
        details={
            "has_changes": has_changes,
            "change_description": request.change_description,
            "new_version": (max_version or 0) + 1 if has_changes else None
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        document_type=document.document_type,
        status=document.status,
        ai_annotations=document.ai_annotations,
        created_at=document.created_at
    )

@router.get("/list", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档列表"""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            document_type=doc.document_type,
            status=doc.status,
            ai_annotations=doc.ai_annotations,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档详情"""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        document_type=document.document_type,
        status=document.status,
        ai_annotations=document.ai_annotations,
        created_at=document.created_at
    )


# 新增：对话管理接口

@router.get("/conversation/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: Optional[str] = None,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """获取对话历史"""
    messages = conversation_service.get_history(
        user_id=current_user.id,
        session_id=session_id,
        limit=limit
    )
    
    session_info = conversation_service.get_session_info(
        user_id=current_user.id,
        session_id=session_id
    )
    
    return ConversationHistoryResponse(
        messages=messages,
        session_info=session_info
    )


@router.delete("/conversation/clear")
async def clear_conversation(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """清除对话历史"""
    success = conversation_service.clear_history(
        user_id=current_user.id,
        session_id=session_id
    )
    
    return {"success": success, "message": "对话历史已清除"}


@router.get("/conversation/info")
async def get_conversation_info(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取对话会话信息"""
    session_info = conversation_service.get_session_info(
        user_id=current_user.id,
        session_id=session_id
    )
    
    return session_info



@router.put("/{document_id}/classification")
async def update_classification(
    document_id: int,
    request: ClassificationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文书密级"""
    # 验证密级值
    valid_classifications = ["public", "internal", "confidential", "secret", "top_secret"]
    if request.classification not in valid_classifications:
        raise HTTPException(
            status_code=400,
            detail=f"无效的密级。有效值：{', '.join(valid_classifications)}"
        )
    
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    old_classification = document.classification
    document.classification = request.classification
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update_classification",
        resource_type="document",
        resource_id=document_id,
        details={
            "old_classification": old_classification,
            "new_classification": request.classification
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(document)
    
    return {
        "success": True,
        "message": "密级更新成功",
        "classification": document.classification
    }

@router.get("/classifications")
async def get_classifications():
    """获取所有可用的密级选项"""
    return {
        "classifications": [
            {"value": "public", "label": "公开", "color": "#67C23A"},
            {"value": "internal", "label": "内部", "color": "#409EFF"},
            {"value": "confidential", "label": "秘密", "color": "#E6A23C"},
            {"value": "secret", "label": "机密", "color": "#F56C6C"},
            {"value": "top_secret", "label": "绝密", "color": "#909399"}
        ]
    }


@router.get("/{document_id}/preview")
async def get_document_preview(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文书预览URL"""
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    print(f"[Preview] Generating preview for document ID: {document_id}")
    
    try:
        # 生成DOCX文件
        from app.services.preview_service_selector import preview_service_selector
        
        docx_bytes = await document_export_service.export_to_docx(
            content=document.content,
            title=document.title,
            options={"document_type": document.document_type}
        )
        
        # 上传到MinIO
        temp_filename = f"temp_preview/{current_user.id}/{document.id}.docx"
        await minio_client.upload_file(
            temp_filename,
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # 获取预览URL（优先WPS，降级到华为云）
        file_url = minio_client.get_file_url(temp_filename, expires=3600, inline=True)
        preview_result = await preview_service_selector.get_preview_url(
            file_url=file_url,
            file_name=f"{document.title}.docx",
            user_id=str(current_user.id),
            permission="read"
        )
        
        preview_url = preview_result.get("preview_url") if preview_result else None
        service_type = preview_result.get("service_type", "unsupported") if preview_result else "unsupported"
        
        print(f"[Preview] Service: {service_type}, URL: {preview_url}")
        
        return {
            "preview_url": preview_url,
            "file_url": file_url,
            "service_type": service_type,
            "document_id": document.id
        }
    except Exception as e:
        print(f"[Preview] Error generating preview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")
