# ONLYOFFICE集成测试脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ONLYOFFICE集成测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BACKEND_URL = "http://localhost:8000"
$ONLYOFFICE_URL = "http://101.37.24.171:9090"

# 测试1: 后端健康检查
Write-Host "测试1: 后端健康检查..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/onlyoffice/health" -Method Get
    Write-Host "✓ 后端健康检查通过" -ForegroundColor Green
    Write-Host "  - 状态: $($response.status)" -ForegroundColor Gray
    Write-Host "  - ONLYOFFICE启用: $($response.onlyoffice_enabled)" -ForegroundColor Gray
    Write-Host "  - 服务器URL: $($response.server_url)" -ForegroundColor Gray
    Write-Host "  - 后端公网URL: $($response.backend_public_url)" -ForegroundColor Gray
} catch {
    Write-Host "✗ 后端健康检查失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 测试2: ONLYOFFICE服务检查
Write-Host "测试2: ONLYOFFICE服务检查..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$ONLYOFFICE_URL/healthcheck" -Method Get
    if ($response -eq $true) {
        Write-Host "✓ ONLYOFFICE服务正常" -ForegroundColor Green
    } else {
        Write-Host "✗ ONLYOFFICE服务异常" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ ONLYOFFICE服务无法访问: $_" -ForegroundColor Red
}
Write-Host ""

# 测试3: ONLYOFFICE API脚本
Write-Host "测试3: ONLYOFFICE API脚本..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ONLYOFFICE_URL/web-apps/apps/api/documents/api.js" -Method Get -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ ONLYOFFICE API脚本可访问" -ForegroundColor Green
        Write-Host "  - 大小: $($response.Content.Length) bytes" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ ONLYOFFICE API脚本无法访问: $_" -ForegroundColor Red
}
Write-Host ""

# 测试4: 用户登录（获取token）
Write-Host "测试4: 用户登录..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "admin"
        password = "admin123"
    }
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
    $token = $response.access_token
    Write-Host "✓ 登录成功，获取到token" -ForegroundColor Green
    Write-Host "  - Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "⚠ 登录失败（可能需要先注册用户）: $_" -ForegroundColor Yellow
    Write-Host "  提示: 请先通过前端注册一个用户" -ForegroundColor Gray
    $token = $null
}
Write-Host ""

# 测试5: 获取文件列表
if ($token) {
    Write-Host "测试5: 获取文件列表..." -ForegroundColor Yellow
    try {
        $headers = @{
            "Authorization" = "Bearer $token"
        }
        $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/files/?skip=0&limit=10" -Method Get -Headers $headers
        Write-Host "✓ 获取文件列表成功" -ForegroundColor Green
        Write-Host "  - 文件总数: $($response.total)" -ForegroundColor Gray
        
        if ($response.items.Count -gt 0) {
            $testFileId = $response.items[0].id
            Write-Host "  - 测试文件ID: $testFileId" -ForegroundColor Gray
            Write-Host "  - 文件名: $($response.items[0].file_name)" -ForegroundColor Gray
            
            # 测试6: 获取ONLYOFFICE编辑器配置
            Write-Host ""
            Write-Host "测试6: 获取ONLYOFFICE编辑器配置..." -ForegroundColor Yellow
            try {
                $configBody = @{
                    file_id = $testFileId
                    mode = "view"
                } | ConvertTo-Json
                
                $config = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/onlyoffice/config" -Method Post -Body $configBody -ContentType "application/json" -Headers $headers
                Write-Host "✓ 获取编辑器配置成功" -ForegroundColor Green
                Write-Host "  - 文档类型: $($config.documentType)" -ForegroundColor Gray
                Write-Host "  - 文件类型: $($config.document.fileType)" -ForegroundColor Gray
                Write-Host "  - 文档key: $($config.document.key)" -ForegroundColor Gray
                Write-Host "  - 文档URL: $($config.document.url)" -ForegroundColor Gray
                Write-Host "  - 回调URL: $($config.editorConfig.callbackUrl)" -ForegroundColor Gray
                
                # 测试7: 测试代理端点
                Write-Host ""
                Write-Host "测试7: 测试文件下载代理端点..." -ForegroundColor Yellow
                try {
                    $proxyUrl = "$BACKEND_URL/api/v1/onlyoffice/download/file/$testFileId"
                    $response = Invoke-WebRequest -Uri $proxyUrl -Method Get -UseBasicParsing
                    if ($response.StatusCode -eq 200) {
                        Write-Host "✓ 代理端点测试成功" -ForegroundColor Green
                        Write-Host "  - 文件大小: $($response.Content.Length) bytes" -ForegroundColor Gray
                        Write-Host "  - Content-Type: $($response.Headers.'Content-Type')" -ForegroundColor Gray
                    }
                } catch {
                    Write-Host "✗ 代理端点测试失败: $_" -ForegroundColor Red
                }
            } catch {
                Write-Host "✗ 获取编辑器配置失败: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  ⚠ 没有找到文件，请先上传一个文件" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ 获取文件列表失败: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 如果没有用户，请通过前端注册: http://localhost:5173/register" -ForegroundColor Gray
Write-Host "2. 上传一个DOCX文件进行测试" -ForegroundColor Gray
Write-Host "3. 打开测试页面: test_onlyoffice_with_backend.html" -ForegroundColor Gray
Write-Host "4. 在测试页面中配置后端地址: http://101.37.24.171:8000" -ForegroundColor Gray
Write-Host ""
