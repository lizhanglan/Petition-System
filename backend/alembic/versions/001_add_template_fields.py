"""add word template fields to templates table

Revision ID: 001_template_fields
Revises: 
Create Date: 2026-01-05

为 templates 表添加 Word 模板系统所需的新字段
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_template_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 Word 模板系统所需的新字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('templates')]
    
    # 添加 template_file_path 字段（如果不存在）
    if 'template_file_path' not in columns:
        op.add_column('templates', 
            sa.Column('template_file_path', sa.String(500), nullable=True)
        )
    
    # 添加 original_file_path 字段（如果不存在）
    if 'original_file_path' not in columns:
        op.add_column('templates', 
            sa.Column('original_file_path', sa.String(500), nullable=True)
        )
    
    # 修改 structure 字段为可空（兼容新旧模板系统）
    # 注意：PostgreSQL 中 ALTER COLUMN 比较安全，重复执行通常没问题，
    # 但为了严谨，我们可以直接执行
    op.alter_column('templates', 'structure',
        existing_type=sa.JSON(),
        nullable=True
    )


def downgrade() -> None:
    """回滚：移除添加的字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('templates')]

    # 移除新增字段
    if 'original_file_path' in columns:
        op.drop_column('templates', 'original_file_path')
    
    if 'template_file_path' in columns:
        op.drop_column('templates', 'template_file_path')
    
    # 恢复 structure 为非空
    op.alter_column('templates', 'structure',
        existing_type=sa.JSON(),
        nullable=False
    )
