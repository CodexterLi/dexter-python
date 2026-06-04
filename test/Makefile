.PHONY: help install dev dev-debug dev-fast logs clean lint test format upgrade upgrade-sync
.PHONY: login build push bp deploy release

# 虚拟环境路径
VENV := .venv
PYTHON := $(VENV)/bin/python
UV_RUN := VIRTUAL_ENV= uv run

# ============================================================
# Docker 构建与部署配置
# ============================================================
ECR_REGISTRY ?= 848332098320.dkr.ecr.ap-southeast-1.amazonaws.com
AWS_REGION ?= ap-southeast-1
IMAGE_NAME ?= dexter-ai
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)
PLATFORM ?= linux/arm64

# 部署配置
SERVER_USER ?= ec2-user
SERVER_IP ?= 18.139.55.205
DEPLOY_DIR ?= ~/dexter/ai
SSH_KEY ?= 
SSH_OPTS ?= $(if $(SSH_KEY),-i $(SSH_KEY)) -o StrictHostKeyChecking=no

# 默认目标
help:
	@echo "FastAPI AI - 可用命令:"
	@echo ""
	@echo "  环境管理:"
	@echo "    make install      - 创建虚拟环境并安装依赖"
	@echo "    make clean        - 清理缓存和临时文件"
	@echo ""
	@echo "  开发服务:"
	@echo "    make dev          - 开发模式运行（热重载）"
	@echo "    make dev-debug    - 开发模式运行（DEBUG 日志）"
	@echo "    make dev-fast     - 快速开发模式（DeepSeek + DEBUG）"
	@echo "    make logs         - 查看 Agent 执行日志"
	@echo ""
	@echo "  代码质量:"
	@echo "    make lint         - 代码检查"
	@echo "    make format       - 格式化代码"
	@echo "    make test         - 运行测试"
	@echo ""
	@echo "  依赖管理:"
	@echo "    make upgrade      - 升级所有依赖到最新版本"
	@echo "    make upgrade-sync - 升级依赖并同步 pyproject.toml 版本号"
	@echo ""
	@echo "  Docker 构建与部署:"
	@echo "    make login        - 登录 ECR"
	@echo "    make build        - 构建 Docker 镜像"
	@echo "    make push         - 推送镜像到 ECR"
	@echo "    make bp           - 构建并推送 (login + build + push)"
	@echo "    make deploy       - 远程部署到服务器"
	@echo "    make release      - 一键发布 (bp + deploy)"
	@echo ""

# ============================================================
# 环境管理
# ============================================================

# 创建虚拟环境并安装依赖
install:
	uv venv
	uv sync

# 清理缓存和临时文件
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true

# ============================================================
# 开发服务
# ============================================================

# 开发模式运行（热重载）
dev:
	$(UV_RUN) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 开发模式运行（DEBUG 日志）
dev-debug:
	LOG_LEVEL=DEBUG $(UV_RUN) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 开发模式运行（快速模型 + DEBUG）
dev-fast:
	LOG_LEVEL=DEBUG AGENT_MODEL=deepseek/deepseek-chat $(UV_RUN) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 查看 Agent 日志
logs:
	@mkdir -p logs
	tail -f logs/agent.log 2>/dev/null || echo "No agent logs yet. Run 'make dev' and make a request first."

# ============================================================
# 代码质量
# ============================================================

# 代码检查
lint:
	$(UV_RUN) ruff check app/
	$(UV_RUN) ruff format --check app/

# 格式化代码
format:
	$(UV_RUN) ruff format app/
	$(UV_RUN) ruff check --fix app/

# 运行测试
test:
	$(UV_RUN) pytest -v

# ============================================================
# 依赖管理
# ============================================================

# 升级所有依赖到最新版本
upgrade:
	uv lock --upgrade
	uv sync
	@echo "依赖已升级，uv.lock 已更新"

# 升级依赖并同步 pyproject.toml 中的版本号
upgrade-sync:
	uv lock --upgrade
	uv sync
	@$(PYTHON) -c "import re, tomllib; from pathlib import Path; lock = tomllib.loads(Path('uv.lock').read_text()); pyproject = Path('pyproject.toml').read_text(); pkg_versions = {p['name']: p['version'] for p in lock.get('package', [])}; replace_ver = lambda m: '\"' + m.group(1) + (m.group(2) or '') + '>=' + pkg_versions.get(m.group(1).lower().replace('_', '-'), m.group(3)) + '\"'; new_content = re.sub(r'\"([a-zA-Z0-9_-]+)(\[[^\]]+\])?>=([^\"]+)\"', replace_ver, pyproject); Path('pyproject.toml').write_text(new_content); print('pyproject.toml 版本已同步')"

# ============================================================
# Docker 构建与部署
# ============================================================

# ECR 登录
login:
	@echo "🔐 登录 ECR..."
	@aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)
	@echo "✅ ECR 登录成功"

# 构建镜像
build:
	@echo "🔨 构建 $(IMAGE_NAME) ($(PLATFORM))..."
	@docker buildx build --platform $(PLATFORM) --no-cache \
		-t $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) \
		-t $(ECR_REGISTRY)/$(IMAGE_NAME):latest \
		-f Dockerfile --load .
	@echo "✅ $(IMAGE_NAME) 构建完成"

# 推送镜像
push:
	@echo "📤 推送 $(IMAGE_NAME)..."
	@docker push $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@docker push $(ECR_REGISTRY)/$(IMAGE_NAME):latest
	@echo "✅ $(IMAGE_NAME) 推送完成"

# 构建并推送
bp: login build push
	@echo "🎉 $(IMAGE_NAME) 构建并推送完成!"
	@echo "   $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"

# 远程部署
deploy:
	@echo "🚀 开始部署..."
	@echo "📤 同步配置文件到服务器..."
	@scp $(SSH_OPTS) docker-compose.yaml $(SERVER_USER)@$(SERVER_IP):$(DEPLOY_DIR)/
	@echo "✅ 配置文件同步完成"
	@echo "🔄 连接服务器并部署..."
	@ssh $(SSH_OPTS) $(SERVER_USER)@$(SERVER_IP) '\
		echo "🔐 登录 ECR..." && \
		aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY) && \
		cd $(DEPLOY_DIR) && \
		export IMAGE_TAG=$(IMAGE_TAG) && \
		echo "📥 拉取最新镜像..." && \
		docker-compose pull && \
		echo "🔄 重启服务..." && \
		docker-compose up -d && \
		echo "🧹 清理旧镜像..." && \
		docker image prune -f && \
		echo "📋 服务状态:" && \
		docker-compose ps \
	'
	@echo "✅ 部署完成!"

# 构建、推送并部署 (一键发布)
release: bp deploy
	@echo "🎉 发布完成! $(IMAGE_NAME):$(IMAGE_TAG)"
