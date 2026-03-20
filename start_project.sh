#!/bin/bash

# 允许用户即便用 `sh start_project.sh` 启动，也会自动切换到 bash。
if [ -z "${BASH_VERSION:-}" ]; then
    exec /bin/bash "$0" "$@"
fi

set -u

# 获取脚本所在目录作为项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PYTHON="$HOME/anaconda3/envs/rxncommons/bin/python"
FRONTEND_NODE_BIN="$HOME/anaconda3/envs/rxn_front/bin"
FRONTEND_NODE="$FRONTEND_NODE_BIN/node"

is_port_listening() {
    local port="$1"
    ss -ltn "( sport = :$port )" 2>/dev/null | awk 'NR>1 {print $0}' | grep -q "LISTEN"
}

# 识别使用同一份配置文件启动的 frpc，兼容相对路径和绝对路径两种写法
is_frpc_running_for_config() {
    local target_config="$1"
    local target_real pid proc_cwd proc_cmdline arg config_path next_is_config

    target_real="$(readlink -f "$target_config" 2>/dev/null || printf '%s' "$target_config")"

    while read -r pid; do
        [ -r "/proc/$pid/cmdline" ] || continue

        proc_cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        proc_cmdline="$(tr '\0' '\n' < "/proc/$pid/cmdline" 2>/dev/null || true)"
        [ -n "$proc_cmdline" ] || continue

        next_is_config=false
        while IFS= read -r arg; do
            if [ "$next_is_config" = true ]; then
                config_path="$arg"
                next_is_config=false
            else
                case "$arg" in
                    -c|--config)
                        next_is_config=true
                        continue
                        ;;
                    -c=*|--config=*)
                        config_path="${arg#*=}"
                        ;;
                    *)
                        continue
                        ;;
                esac
            fi

            if [[ "$config_path" != /* ]] && [ -n "$proc_cwd" ]; then
                config_path="$proc_cwd/$config_path"
            fi
            config_path="$(readlink -f "$config_path" 2>/dev/null || printf '%s' "$config_path")"

            if [ "$config_path" = "$target_real" ]; then
                return 0
            fi
        done <<< "$proc_cmdline"
    done < <(pgrep -x -u "$(id -u)" frpc 2>/dev/null || true)

    return 1
}

# 加载 Conda 环境
source ~/anaconda3/etc/profile.d/conda.sh

echo "=========================================="
echo "   RxnCommons Project Launcher"
echo "=========================================="

# 1. 检查并启动 Docker 服务
echo "[1/4] Checking Docker services..."
if ! docker ps | grep -q "rxncommons-postgres"; then
    echo "Starting Docker containers..."
    docker-compose up -d
else
    echo "Docker containers are already running."
fi

# 2. 启动后端 (Backend)
echo "[2/4] Starting Backend..."
if is_port_listening 8001; then
    echo "Backend already running on :8001. Skipping backend start."
else
    cd "$BACKEND_DIR"
    if [ ! -x "$BACKEND_PYTHON" ]; then
        echo "Error: Backend Python not found at $BACKEND_PYTHON"
        exit 1
    fi
    # 直接用 setsid 托管 uvicorn，避免无交互后台中进程提前退出
    setsid "$BACKEND_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > server.log 2>&1 < /dev/null &
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
echo "[3/4] Starting Frontend..."
if is_port_listening 3000; then
    echo "Frontend already running on :3000. Skipping frontend start."
else
    cd "$FRONTEND_DIR"
    if [ ! -d "$FRONTEND_NODE_BIN" ]; then
        echo "Error: Frontend env bin not found at $FRONTEND_NODE_BIN"
        exit 1
    fi
    if [ ! -x "$FRONTEND_NODE" ]; then
        echo "Error: Frontend Node not found at $FRONTEND_NODE"
        exit 1
    fi
    export PATH="$FRONTEND_NODE_BIN:$PATH"
    echo "Building frontend production bundle..."
    if ! npm run build > out.log 2>&1; then
        echo "Error: Frontend build failed. Check logs: $FRONTEND_DIR/out.log"
        tail -n 80 "$FRONTEND_DIR/out.log" 2>/dev/null || true
        exit 1
    fi
    # 直接调用 Node 启动 Next production server，避免 npm/next 在无交互后台中提前退出
    setsid "$FRONTEND_NODE" "$FRONTEND_DIR/node_modules/next/dist/bin/next" start -H 0.0.0.0 -p 3000 >> out.log 2>&1 < /dev/null &
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

# 4. 启动 frpc 内网穿透（对外暴露前端）
FRP_CONFIG="$PROJECT_ROOT/frpc-rxncommons.toml"
if [ -f "$FRP_CONFIG" ] && command -v frpc >/dev/null 2>&1; then
    if is_frpc_running_for_config "$FRP_CONFIG"; then
        echo "FRP tunnel already running. Skipping."
    else
        echo "[4/4] Starting FRP tunnel..."
        nohup frpc -c "$FRP_CONFIG" > "$PROJECT_ROOT/frpc-rxncommons.log" 2>&1 &
        sleep 2
        if grep -q "start proxy success" "$PROJECT_ROOT/frpc-rxncommons.log" 2>/dev/null; then
            echo "FRP tunnel started. External access: http://haihe.luoszgroup.com:2233"
        else
            echo "Warning: FRP tunnel may not have connected. Check frpc-rxncommons.log"
        fi
    fi
fi
