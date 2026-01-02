"""
审计日志查询接口

功能：
1. 查询审计日志列表（支持多条件筛选）
2. 分页查询
3. 导出日志
4. 统计分析
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import csv
import io

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]
    page: int
    page_size: int


class AuditLogStatsResponse(BaseModel):
    total_count: int
    action_stats: dict
    resource_stats: dict
    recent_activity: List[dict]


@router.get("/list", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询审计日志列表
    
    支持多条件筛选：
    - action: 操作类型（upload, review, generate, etc.）
    - resource_type: 资源类型（file, document, template）
    - user_id: 用户ID
    - start_date/end_date: 日期范围
    - keyword: 关键词搜索（搜索 details）
    """
    print(f"[AuditLog] Query: page={page}, action={action}, resource_type={resource_type}")
    
    # 构建查询条件
    conditions = []
    
    # 普通用户只能查看自己的日志
    # 管理员可以查看所有日志（这里简化处理，实际应该有角色判断）
    if not current_user.is_active:  # 简化：假设 is_active 为管理员标识
        conditions.append(AuditLog.user_id == current_user.id)
    
    if action:
        conditions.append(AuditLog.action == action)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            conditions.append(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，应为 YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            conditions.append(AuditLog.created_at < end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，应为 YYYY-MM-DD")
    
    # 关键词搜索（搜索 details JSON）
    if keyword:
        # 这里简化处理，实际可以使用 PostgreSQL 的 JSON 搜索功能
        pass
    
    # 查询总数
    count_query = select(func.count(AuditLog.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    result = await db.execute(count_query)
    total = result.scalar() or 0
    
    # 查询数据
    query = select(AuditLog, User.username).join(
        User, AuditLog.user_id == User.id
    ).order_by(AuditLog.created_at.desc())
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    # 构建响应
    items = []
    for log, username in rows:
        items.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at
        ))
    
    print(f"[AuditLog] Found {total} logs, returning {len(items)} items")
    
    return AuditLogListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=AuditLogStatsResponse)
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取审计日志统计信息
    
    Args:
        days: 统计最近N天的数据
    """
    print(f"[AuditLog] Getting stats for last {days} days")
    
    # 计算时间范围
    start_date = datetime.now() - timedelta(days=days)
    
    # 构建基础查询条件
    base_condition = AuditLog.created_at >= start_date
    
    # 普通用户只能查看自己的统计
    if not current_user.is_active:
        base_condition = and_(base_condition, AuditLog.user_id == current_user.id)
    
    # 总数统计
    count_query = select(func.count(AuditLog.id)).where(base_condition)
    result = await db.execute(count_query)
    total_count = result.scalar() or 0
    
    # 按操作类型统计
    action_query = select(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).where(base_condition).group_by(AuditLog.action)
    
    result = await db.execute(action_query)
    action_stats = {row.action: row.count for row in result}
    
    # 按资源类型统计
    resource_query = select(
        AuditLog.resource_type,
        func.count(AuditLog.id).label('count')
    ).where(
        and_(base_condition, AuditLog.resource_type.isnot(None))
    ).group_by(AuditLog.resource_type)
    
    result = await db.execute(resource_query)
    resource_stats = {row.resource_type: row.count for row in result}
    
    # 最近活动（最近10条）
    recent_query = select(AuditLog, User.username).join(
        User, AuditLog.user_id == User.id
    ).where(base_condition).order_by(
        AuditLog.created_at.desc()
    ).limit(10)
    
    result = await db.execute(recent_query)
    rows = result.all()
    
    recent_activity = [
        {
            "action": log.action,
            "username": username,
            "resource_type": log.resource_type,
            "created_at": log.created_at.isoformat()
        }
        for log, username in rows
    ]
    
    print(f"[AuditLog] Stats: total={total_count}, actions={len(action_stats)}, resources={len(resource_stats)}")
    
    return AuditLogStatsResponse(
        total_count=total_count,
        action_stats=action_stats,
        resource_stats=resource_stats,
        recent_activity=recent_activity
    )


@router.get("/export")
async def export_audit_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出审计日志为 CSV 文件
    """
    print(f"[AuditLog] Exporting logs: action={action}, resource_type={resource_type}")
    
    # 构建查询条件（与 list 接口相同）
    conditions = []
    
    if not current_user.is_active:
        conditions.append(AuditLog.user_id == current_user.id)
    
    if action:
        conditions.append(AuditLog.action == action)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            conditions.append(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            conditions.append(AuditLog.created_at < end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误")
    
    # 查询数据（限制最多导出10000条）
    query = select(AuditLog, User.username).join(
        User, AuditLog.user_id == User.id
    ).order_by(AuditLog.created_at.desc()).limit(10000)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    rows = result.all()
    
    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        'ID', '用户', '操作', '资源类型', '资源ID', 
        'IP地址', '时间', '详情'
    ])
    
    # 写入数据
    for log, username in rows:
        writer.writerow([
            log.id,
            username,
            log.action,
            log.resource_type or '',
            log.resource_id or '',
            log.ip_address or '',
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            str(log.details) if log.details else ''
        ])
    
    # 准备响应
    output.seek(0)
    
    print(f"[AuditLog] Exported {len(rows)} logs")
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条审计日志详情"""
    result = await db.execute(
        select(AuditLog, User.username).join(
            User, AuditLog.user_id == User.id
        ).where(AuditLog.id == log_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    log, username = row
    
    # 权限检查：普通用户只能查看自己的日志
    if not current_user.is_active and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此日志")
    
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        username=username,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        details=log.details,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at
    )
