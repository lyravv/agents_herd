todo_tool_schema = {
    "name": "todo_tool",
    "description": (
        "管理一个带有依赖关系（DAG）的任务清单。"
        "支持创建、完成、标记失败、查看等操作。"
        "可用于LLM自主规划和追踪任务执行状态。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["todo_create", "todo_complete", "todo_failure", "todo_show"],
                "description": (
                    "要执行的操作类型：\n"
                    "- todo_create: 创建一个新的 todo DAG\n"
                    "- todo_complete: 将某个任务标记为完成\n"
                    "- todo_failure: 将某个任务标记为失败\n"
                    "- todo_show: 查看当前 DAG"
                )
            },
            "todo_text": {
                "type": "string",
                "description": (
                    "当 action=todo_create 时提供，"
                    "LLM 输出的任务描述文本，格式为：\n"
                    "level 1\n[] task_0: *** dependency []\n"
                    "level 2\n[] task_1: *** dependency [task_0]\n[] task_2: *** dependency [task_0]\n"
                    "level 3\n[] task_3: *** dependency [task_2]\n"
                    "level 4\n[] task_4: *** dependency [task_1, task_3]\n"
                ),
                "nullable": True
            },
            "task_id": {
                "type": "string",
                "description": (
                    "当 action=todo_complete 或 todo_failure 时提供，"
                    "指定要修改状态的任务 ID。"
                ),
                "nullable": True
            }
        },
        "required": ["action"]
    }
}

import os
from typing import Dict, Any, List, Literal, Optional


TODO_FILE = "todo_dag.txt"

def load_todo_text() -> str:
    """加载任务文本"""
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_todo_text(todo_text: str):
    """保存任务文本"""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        f.write(todo_text)

def update_task_status(todo_text: str, task_id: str, new_status: str) -> str:
    """更新任务状态"""
    if not todo_text:
        return f"Error: No tasks found."
    
    lines = todo_text.split("\n")
    updated_lines = []
    
    for line in lines:
        if line.strip() and f" {task_id}:" in line:
            # 替换状态标记
            if new_status == "completed":
                line = line.replace("[] ", "✓ ", 1)
            elif new_status == "failed":
                line = line.replace("[] ", "✗ ", 1)
        updated_lines.append(line)
    
    return "\n".join(updated_lines)

def todo_tool(
    action: Literal["todo_create", "todo_complete", "todo_failure", "todo_show"],
    todo_text: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    通用 todo tool 函数。
    支持动作：
        - todo_create: 创建 DAG
        - todo_complete: 标记完成
        - todo_failure: 标记失败
        - todo_show: 查看 DAG
    """
    if action == "todo_create":
        if not todo_text:
            return {"error": "todo_text is required for todo_create"}
        save_todo_text(todo_text)
        return {"message": "Todo DAG created.", "todo_text": todo_text}

    current_todo_text = load_todo_text()
    if not current_todo_text:
        return {"error": "No todo list found. Please create one first."}

    if action == "todo_complete":
        if not task_id:
            return {"error": "task_id is required for todo_complete"}
        updated_text = update_task_status(current_todo_text, task_id, "completed")
        save_todo_text(updated_text)
        return {"message": f"{task_id} marked as completed.", "todo_text": updated_text}

    elif action == "todo_failure":
        if not task_id:
            return {"error": "task_id is required for todo_failure"}
        updated_text = update_task_status(current_todo_text, task_id, "failed")
        save_todo_text(updated_text)
        return {"message": f"{task_id} marked as failed.", "todo_text": updated_text}

    elif action == "todo_show":
        return current_todo_text

    else:
        return {"error": f"Unknown action: {action}"}


if __name__ == "__main__":
    dag_text = """
    level 1
    [] task_0: 定义需求 dependency []
    level 2
    [] task_1: 设计方案 dependency [task_0]
    [] task_2: 技术评审 dependency [task_0]
    level 3
    [] task_3: 开发实现 dependency [task_2]
    level 4
    [] task_4: 测试验收 dependency [task_1, task_3]
    """

    res = todo_tool("todo_create", todo_text=dag_text)
    print(res["message"])

    # 标记任务完成
    todo_tool("todo_complete", task_id="task_1")

    # 标记任务失败
    todo_tool("todo_failure", task_id="task_3")

    # 查看当前 DAG
    print(todo_tool("todo_show"))