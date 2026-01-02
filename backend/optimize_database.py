"""
数据库性能优化
添加索引、优化查询
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# 需要添加的索引
INDEXES = [
    # documents 表索引
    {
        "table": "documents",
        "name": "idx_documents_user_status",
        "columns": ["user_id", "status"],
        "description": "优化按用户和状态查询文档"
    },
    {
        "table": "documents",
        "name": "idx_documents_created_at",
        "columns": ["created_at DESC"],
        "description": "优化按创建时间排序"
    },
    {
        "table": "documents",
        "name": "idx_documents_classification",
        "columns": ["classification"],
        "description": "优化按密级筛选"
    },
    
    # files 表索引
    {
        "table": "files",
        "name": "idx_files_user_status",
        "columns": ["user_id", "status"],
        "description": "优化按用户和状态查询文件"
    },
    {
        "table": "files",
        "name": "idx_files_created_at",
        "columns": ["created_at DESC"],
        "description": "优化按上传时间排序"
    },
    
    # templates 表索引
    {
        "table": "templates",
        "name": "idx_templates_user_active",
        "columns": ["user_id", "is_active"],
        "description": "优化查询用户的活跃模板"
    },
    {
        "table": "templates",
        "name": "idx_templates_document_type",
        "columns": ["document_type"],
        "description": "优化按文书类型筛选"
    },
    
    # versions 表索引
    {
        "table": "versions",
        "name": "idx_versions_document_version",
        "columns": ["document_id", "version_number DESC"],
        "description": "优化查询文档版本"
    },
    {
        "table": "versions",
        "name": "idx_versions_created_at",
        "columns": ["created_at DESC"],
        "description": "优化按创建时间排序"
    },
    
    # audit_logs 表索引
    {
        "table": "audit_logs",
        "name": "idx_audit_logs_user_action",
        "columns": ["user_id", "action"],
        "description": "优化按用户和操作类型查询"
    },
    {
        "table": "audit_logs",
        "name": "idx_audit_logs_resource",
        "columns": ["resource_type", "resource_id"],
        "description": "优化按资源查询审计日志"
    },
    {
        "table": "audit_logs",
        "name": "idx_audit_logs_created_at",
        "columns": ["created_at DESC"],
        "description": "优化按时间范围查询"
    }
]

def create_indexes():
    """创建索引"""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        created_count = 0
        skipped_count = 0
        
        for index in INDEXES:
            # 检查索引是否已存在
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = %s AND indexname = %s
            """, (index['table'], index['name']))
            
            if cursor.fetchone():
                print(f"  - 跳过已存在的索引: {index['name']}")
                skipped_count += 1
                continue
            
            # 创建索引
            columns_str = ", ".join(index['columns'])
            sql = f"CREATE INDEX {index['name']} ON {index['table']} ({columns_str})"
            
            try:
                cursor.execute(sql)
                conn.commit()
                created_count += 1
                print(f"  ✓ 已创建索引: {index['name']}")
                print(f"    表: {index['table']}")
                print(f"    列: {columns_str}")
                print(f"    说明: {index['description']}")
            except Exception as e:
                print(f"  ❌ 创建索引失败: {index['name']}")
                print(f"     错误: {str(e)}")
                conn.rollback()
        
        print(f"\n✓ 成功创建 {created_count} 个索引")
        print(f"✓ 跳过 {skipped_count} 个已存在的索引")
        print(f"✓ 总计 {len(INDEXES)} 个索引")
        
        cursor.close()
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def analyze_tables():
    """分析表统计信息"""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        tables = ['documents', 'files', 'templates', 'versions', 'audit_logs', 'users']
        
        print("\n分析表统计信息...")
        for table in tables:
            cursor.execute(f"ANALYZE {table}")
            print(f"  ✓ 已分析表: {table}")
        
        conn.commit()
        print("✓ 表统计信息更新完成")
        
        cursor.close()
    except Exception as e:
        print(f"❌ 分析表错误: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def show_table_stats():
    """显示表统计信息"""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        print("\n表统计信息:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                n_live_tup AS rows
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        print(f"{'表名':<20} {'大小':<15} {'行数':<10}")
        print("-" * 60)
        
        for row in cursor.fetchall():
            schema, table, size, rows = row
            print(f"{table:<20} {size:<15} {rows:<10}")
        
        cursor.close()
    except Exception as e:
        print(f"❌ 获取统计信息错误: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("数据库性能优化")
    print("=" * 60)
    
    # 创建索引
    print("\n1. 创建索引")
    print("-" * 60)
    create_indexes()
    
    # 分析表
    print("\n2. 分析表统计信息")
    print("-" * 60)
    analyze_tables()
    
    # 显示统计信息
    print("\n3. 表统计信息")
    print("-" * 60)
    show_table_stats()
    
    print("\n=" * 60)
    print("优化完成！")
    print("=" * 60)
