"""
添加密级字段到 documents 表
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def add_classification_field():
    """添加密级字段"""
    # 连接数据库
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='documents' AND column_name='classification'
        """)
        
        if cursor.fetchone() is None:
            # 添加密级字段
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN classification VARCHAR(20) DEFAULT 'public'
            """)
            conn.commit()
            print("✓ 密级字段添加成功")
        else:
            print("✓ 密级字段已存在")
        
        cursor.close()
    finally:
        conn.close()

if __name__ == "__main__":
    add_classification_field()
    print("完成！")
