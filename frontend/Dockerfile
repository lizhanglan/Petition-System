# 构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 添加构建参数，用于破坏缓存（必须在COPY之前使用）
ARG CACHEBUST=1
RUN echo "Cache bust: $CACHEBUST"

# 复制 package 文件
COPY package*.json ./

RUN npm config set registry https://registry.npmmirror.com
# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
