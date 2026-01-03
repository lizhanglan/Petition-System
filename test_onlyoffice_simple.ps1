# ONLYOFFICE集成简单测试

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
}
catch {
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
    }
}
catch {
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
}
catch {
    Write-Host "✗ ONLYOFFICE API脚本无法访问: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "基础测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 打开前端: http://localhost:5173" -ForegroundColor Gray
Write-Host "2. 注册/登录用户" -ForegroundColor Gray
Write-Host "3. 上传一个DOCX文件" -ForegroundColor Gray
Write-Host "4. 打开测试页面: test_onlyoffice_with_backend.html" -ForegroundColor Gray
Write-Host "5. 在测试页面中配置后端地址: http://101.37.24.171:8000" -ForegroundColor Gray
Write-Host ""
