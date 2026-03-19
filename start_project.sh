#!/bin/bash
set -u

# 获取脚本所在目录作为项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PYTHON="$HOME/anaconda3/envs/rxncommons/bin/python"
FRONTEND_NODE_BIN="$HOME/anaconda3/envs/rxn_front/bin"

is_port_listening() {
    local port="$1"
    ss -ltn "( sport = :$port )" 2>/dev/null | awk 'NR>1 {print $0}' | grep -q "LISTEN"
}

# 加载 Conda 环境
source ~/anaconda3/etc/profile.d/conda.sh

echo "=========================================="
echo "   RxnCommons Project Launcher"
echo "=========================================="

# 1. 检查并启动 Docker 服务
echo "[1/3] Checking Docker services..."
if ! docker ps | grep -q "rxncommons-postgres"; then
    echo "Starting Docker containers..."
    docker-compose up -d
else
    echo "Docker containers are already running."
fi

# 2. 启动后端 (Backend)
echo "[2/3] Starting Backend..."
if is_port_listening 8001; then
    echo "Backend already running on :8001. Skipping backend start."
else
    cd "$BACKEND_DIR"
    if [ ! -x "$BACKEND_PYTHON" ]; then
        echo "Error: Backend Python not found at $BACKEND_PYTHON"
        exit 1
    fi
    # 使用 nohup 后台运行（不启用 --reload，避免后台模式下 reloader 子进程退出导致端口掉线）
    nohup "$BACKEND_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > server.log 2>&1 &
    BACKEND_PID=$!
    sleep 2
    if is_port_listening 8001; then
        echo "Backend started (PID: $BACKEND_PID). Logs: $BACKEND_DIR/server.log"
    else
        echo "Error: Backend failed to start on :8001. Check logs: $BACKEND_DIR/server.log"
        tail -n 60 "$BACKEND_DIR/server.log" 2>/dev/null || true
        exit 1
    fi
fi

# 3. 启动前端 (Frontend)
echo "[3/3] Starting Frontend..."
if is_port_listening 3000; then
    echo "Frontend already running on :3000. Skipping frontend start."
else
    cd "$FRONTEND_DIR"
    if [ ! -d "$FRONTEND_NODE_BIN" ]; then
        echo "Error: Frontend env bin not found at $FRONTEND_NODE_BIN"
        exit 1
    fi
    export PATH="$FRONTEND_NODE_BIN:$PATH"
    # 使用 nohup 后台运行，日志写入 frontend/out.log
    # 使用 dev:node20 确保 Node 版本兼容性
    nohup npm run dev:node20 > out.log 2>&1 &
    FRONTEND_PID=$!
    sleep 3
    if is_port_listening 3000; then
        echo "Frontend started (PID: $FRONTEND_PID). Logs: $FRONTEND_DIR/out.log"
    else
        echo "Error: Frontend failed to start on :3000. Check logs: $FRONTEND_DIR/out.log"
        tail -n 60 "$FRONTEND_DIR/out.log" 2>/dev/null || true
        exit 1
    fi
fi

echo "=========================================="
echo "Project is running!"
echo "Backend API: http://localhost:8001/docs"
echo "Frontend UI: http://localhost:3000"
echo "=========================================="
