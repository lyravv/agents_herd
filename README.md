# 项目介绍
通过whiteboard呈现信息的agentic系统

# 快速开始
## 安装依赖
```bash
uv sync
```

## 配置env
```bash
cp .env_example .env
```
编辑.env配置你的环境

## 启动mcp服务器
```bash
python tools/mcp_server.py
```

## 启动master_agent进行问答
```bash
python master_agent.py
```