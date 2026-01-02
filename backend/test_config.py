"""
测试配置是否正确加载
"""
from app.core.config import settings

print("=" * 60)
print("配置验证")
print("=" * 60)
print(f"API_TIMEOUT: {settings.API_TIMEOUT}")
print(f"API_RETRY_TIMES: {settings.API_RETRY_TIMES}")
print(f"API_RETRY_DELAYS: {settings.API_RETRY_DELAYS}")
print(f"DEEPSEEK_API_KEY: {settings.DEEPSEEK_API_KEY[:20]}...")
print(f"DEEPSEEK_API_BASE: {settings.DEEPSEEK_API_BASE}")
print(f"DEEPSEEK_MODEL: {settings.DEEPSEEK_MODEL}")
print("=" * 60)

if settings.API_TIMEOUT == 120:
    print("✅ API_TIMEOUT 配置正确（120 秒）")
else:
    print(f"❌ API_TIMEOUT 配置错误（当前: {settings.API_TIMEOUT}，期望: 120）")
