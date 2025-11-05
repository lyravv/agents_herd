from models.llm import get_llm_response_gpt_4o
import json

def  nl_sum(query: str):
    system_prompt = """你是一个智能求和助手。你的任务是：**仅当用户明确表达"对某些数值求和"的意图时**，才从输入中提取那些**待求和的具体数值项**，并转换为标准数字列表。
    支持的数值形式包括：
    - 阿拉伯数字：如 5, 9800, 3.14, -20
    - 中文数字：如 五、十二、三百、一万二（=12000）、三点五（=3.5）
    - 带单位缩写：如 10k（=10000）、5w（=50000）、2.5万（=25000）
    - 混合表达：如 "共买了三次，分别是2件、五件和10件" → 提取 [2, 5, 10]

    处理规则：
    1. **只提取明确作为"数值量"的数字**，忽略日期、编号、序号、电话号码等非统计性数字。
    2. 中文数字需正确转换为阿拉伯数字（注意："一万二" = 12000，"三千五" = 3500）。
    3. 单位如"k"=1000，"w"或"万"=10000，"亿"=100000000。
    4. 输出必须是严格有效的 JSON 对象，仅包含一个字段 "numbers"，其值为数字列表（按出现顺序）。

    示例输入：
    "10月份有5笔订单，分别是9800，10w，一万二，90000，5k，他们的总金额是多少"

    期望输出：
    {"numbers": [9800, 100000, 12000, 90000, 5000]}
    """
    
    prompt = f"""以下是用户输入的自然语言查询：{query}
    
    ## 输出：
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    result = get_llm_response_gpt_4o(messages)
    
    try:
        result = json.loads(result)
        print(result)
    except json.JSONDecodeError as e:
        error_msg = f"数值提取结果解析失败: {result}"
        print(error_msg)
        return error_msg

    if not isinstance(result, dict) or "numbers" not in result:
        error_msg = f"数值提取结果格式错误: {result}"
        print(error_msg)
        return error_msg

    numbers_raw = result["numbers"]
    print(f"提取到的原始数字列表: {numbers_raw}")
    
    if not isinstance(numbers_raw, list):
        error_msg = f"numbers字段应为列表: {numbers_raw}"
        print(error_msg)
        return error_msg

    numbers = []
    for idx, n in enumerate(numbers_raw):
        try:
            num = float(n)
            numbers.append(num)
            print(f"成功转换第{idx + 1}个数字: {n} -> {num}")
        except (ValueError, TypeError) as e:
            error_msg = f"numbers列表中第{idx + 1}项无法转为数字: {n}"
            print(f"数字转换失败: {error_msg}, 错误: {e}")
            return error_msg

    final_sum = sum(numbers)
    print(f"计算完成: {numbers} 的总和为 {final_sum}")
    return final_sum