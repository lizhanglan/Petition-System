"""
初始化标准信访模板 - 已弃用

注意：此脚本已不再使用。

新的模板系统使用 Word 模板文件：
1. 用户上传 Word 文档
2. AI 自动识别可变字段并替换为占位符
3. 使用 docxtpl 渲染生成最终文书

如需初始化数据库表，请使用：
  python manual_create_tables.py
"""

print("=" * 60)
print("此脚本已弃用")
print("=" * 60)
print()
print("新的模板系统使用 Word 模板文件，不再预置 JSON 模板。")
print()
print("使用方法：")
print("  1. 运行 python manual_create_tables.py 创建数据库表")
print("  2. 在前端上传 Word 文档作为模板")
print("  3. AI 会自动识别字段并生成模板")
print()
print("=" * 60)
