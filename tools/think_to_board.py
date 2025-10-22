#!/usr/bin/env python3
"""
使用think_tool函数生成思考结果并将其写入Whiteboard
"""

from tools.mcp_server import think_tool
from note_board import Whiteboard

def main():
    # 创建思考内容
    thought = "我需要分析销售合同与货物接单之间的关系，以确定一季度与中芯国际的合同是否已经确认收货。"
    
    # 调用think_tool函数生成思考结果
    think_result = think_tool(thought)
    print(f"生成的思考结果: {think_result}")
    
    # 创建Whiteboard实例
    whiteboard = Whiteboard()
    
    # 将思考结果写入Whiteboard
    whiteboard.thought_process({"content": think_result})
    
    # 打印Whiteboard中的内容摘要
    summary = whiteboard.summarize_entries_as_string()
    print("\nWhiteboard内容摘要:")
    print(summary)

if __name__ == "__main__":
    main()