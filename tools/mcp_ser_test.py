from fastmcp import FastMCP
from typing import Annotated, Literal, Optional
from pydantic import Field

mcp = FastMCP("test")


@mcp.tool(name="get_wether")
def get_wether(city: Annotated[str, Field(description="城市名称")]):
    """
    获取城市天气
    """
    return f"城市{city}的天气是晴天"

@mcp.tool(name="todo_write")
def todo_write(action: Annotated[Literal["todo_create", "todo_complete", "todo_failure", "todo_show"], Field(description="要执行的操作类型：\n"
                    "- todo_create: 创建一个新的 todo DAG\n"
                    "- todo_complete: 将某个任务标记为完成\n"
                    "- todo_failure: 将某个任务标记为失败\n"
                    "- todo_show: 查看当前 DAG")],
    todo_text: Annotated[Optional[str], Field(description="当 action=todo_create 时提供，"
                    "LLM 输出的任务描述文本，格式为：\n"
                    "任务描述：<任务描述>\n"
                    "依赖任务：<依赖任务1>, <依赖任务2>, ...\n"
                    "示例：\n"
                    "任务描述：完成项目文档\n"
                    "依赖任务：项目计划, 项目需求")]=None,
    task_id: Annotated[Optional[str], Field(description="当 action=todo_complete, todo_failure 时提供，"
                    "要操作的任务 ID")]=None):
    """
    操作 todo DAG
    """
    return f"操作{action}，任务描述：{todo_text}"

if __name__ == "__main__":
    mcp.run(transport="http", port=3459)
