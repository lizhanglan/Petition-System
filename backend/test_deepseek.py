"""
测试 DeepSeek API 连接
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_deepseek_api():
    """测试 DeepSeek API"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    print("=" * 60)
    print("DeepSeek API 连接测试")
    print("=" * 60)
    print(f"API Base: {api_base}")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: None")
    print("=" * 60)
    
    if not api_key:
        print("❌ 错误：未找到 DEEPSEEK_API_KEY 环境变量")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "请回复：测试成功"}
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        print("\n正在连接 DeepSeek API...")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ 连接成功！")
                print(f"AI 回复: {content}")
                return True
            else:
                print(f"❌ API 调用失败")
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ 连接超时（30秒）")
        print("可能原因：")
        print("  1. 网络连接问题")
        print("  2. 防火墙阻止")
        print("  3. API 服务响应慢")
        return False
        
    except httpx.ConnectError as e:
        print(f"❌ 连接错误: {str(e)}")
        print("可能原因：")
        print("  1. 无法访问 DeepSeek API 服务器")
        print("  2. DNS 解析失败")
        print("  3. 网络不通")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n开始测试...\n")
    success = asyncio.run(test_deepseek_api())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！DeepSeek API 连接正常")
    else:
        print("❌ 测试失败！请检查配置和网络连接")
    print("=" * 60)
