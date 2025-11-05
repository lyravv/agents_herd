from fastmcp import Client
import asyncio




async def get_available_tools_async():
    async with Client("http://127.0.0.1:3458/mcp") as client:
        tools = await client.list_tools()
        return tools
        

async def call_tool(function_name: str, function_args: dict):
    async with Client("http://127.0.0.1:3458/mcp") as client:
        result = await client.call_tool(function_name, function_args)
        return result.content[0].text

def convert_mcp_tool_to_openai(mcp_tool):
    return {
        "type": "function",
        "function": {
            "name": mcp_tool["name"],
            "description": mcp_tool.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": mcp_tool["inputSchema"].get("properties", {}),
                "required": mcp_tool["inputSchema"].get("required", [])
            }
        }
    }

if __name__ == "__main__":
    tools = asyncio.run(get_available_tools_async())
    print(f"可用工具: {tools}")

#     query = """这些订单的总金额是多少？
# order_id,contract_id,order_amount,order_date,delivery_date,status
# SO20251020,SC20251004,1100000.00,2025-10-20,2025-11-05,pending
# SO20251030,SC20251006,650000.00,2025-10-30,2025-11-15,pending
# SO20251110,SC20251008,820000.00,2025-11-10,2025-11-30,pending"""


#     result = asyncio.run(call_tool("natural_language_sum", {"query": query}))
#     print(f"结果: {result}")  # 2570000.0


    # result = asyncio.run(call_tool("think", {"whiteboard_id": "test_board"}))
    # print(f"结果: {result}")