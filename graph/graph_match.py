
import json
import os
from pathlib import Path
import numpy as np
from typing import List, Dict, Tuple, Optional
import re

try:
    from models.llm import LLM
    from models.llm_openai import OpenAILLM
except ImportError:
    # 如果在不同环境中运行，可能需要调整导入路径
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.llm import LLM
    from models.llm_openai import OpenAILLM

class TableMatcher:
    """表格匹配器，用于将自然语言查询映射到相关表格"""
    
    def __init__(self, graph_json_path: str):
        """初始化表格匹配器
        
        Args:
            graph_json_path: 表格图谱JSON文件路径
        """
        self.graph_data = self._load_graph_data(graph_json_path)
        self.llm = self._init_llm()
        
    def _load_graph_data(self, graph_json_path: str) -> Dict:
        """加载表格图谱数据
        
        Args:
            graph_json_path: 表格图谱JSON文件路径
            
        Returns:
            Dict: 表格图谱数据
        """
        if not os.path.exists(graph_json_path):
            raise FileNotFoundError(f"图谱文件不存在: {graph_json_path}")
            
        with open(graph_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_llm(self) -> LLM:
        """初始化LLM模型
        
        Returns:
            LLM: 语言模型实例
        """
        # 这里使用项目中已有的LLM模型
        # 如果需要，可以根据实际情况调整
        return OpenAILLM()
    
    def match_tables(self, query: str, top_k: int = 3) -> List[Dict]:
        """匹配查询与表格
        
        Args:
            query: 自然语言查询
            top_k: 返回的最相关表格数量
            
        Returns:
            List[Dict]: 最相关的表格列表，包含相关度分数
        """
        # 1. 提取查询中的关键信息
        query_info = self._extract_query_info(query)
        
        # 2. 计算每个表格与查询的相关度
        table_scores = []
        for entity in self.graph_data['entities']:
            score = self._calculate_relevance(query_info, entity)
            table_scores.append({
                'table_id': entity['id'],
                'table_name': entity['name'],
                'description': entity['description'],
                'score': score
            })
        
        # 3. 按相关度排序并返回top_k个结果
        sorted_tables = sorted(table_scores, key=lambda x: x['score'], reverse=True)
        return sorted_tables[:top_k]
    
    def _extract_query_info(self, query: str) -> Dict:
        """从查询中提取关键信息
        
        Args:
            query: 自然语言查询
            
        Returns:
            Dict: 查询信息，包含实体、关系等
        """
        # 使用LLM提取查询中的关键信息
        prompt = f"""
        请从以下自然语言查询中提取关键信息：
        
        查询: {query}
        
        请提取以下信息:
        1. 主要实体或对象
        2. 查询的属性或字段
        3. 查询的目的或意图
        4. 可能涉及的业务流程
        
        以JSON格式返回，格式如下:
        {{
            "entities": ["实体1", "实体2", ...],
            "attributes": ["属性1", "属性2", ...],
            "intent": "查询意图",
            "business_process": "相关业务流程"
        }}
        """
        
        response = self.llm.generate(prompt)
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 如果无法提取JSON，返回简单的结构
                return {
                    "entities": [query],
                    "attributes": [],
                    "intent": "查询",
                    "business_process": ""
                }
        except Exception as e:
            print(f"解析查询信息时出错: {e}")
            # 返回简单的结构
            return {
                "entities": [query],
                "attributes": [],
                "intent": "查询",
                "business_process": ""
            }
    
    def _calculate_relevance(self, query_info: Dict, table_entity: Dict) -> float:
        """计算查询与表格的相关度
        
        Args:
            query_info: 查询信息
            table_entity: 表格实体信息
            
        Returns:
            float: 相关度分数 (0-1)
        """
        # 构建提示，让LLM评估相关度
        table_headers_text = "\n".join([
            f"- {header['name']}: {header['description']}"
            for header in table_entity.get('headers', [])
        ])
        
        entities_text = ", ".join(query_info.get('entities', []))
        attributes_text = ", ".join(query_info.get('attributes', []))
        
        prompt = f"""
        请评估以下查询与表格的相关度:
        
        查询信息:
        - 实体: {entities_text}
        - 属性: {attributes_text}
        - 意图: {query_info.get('intent', '')}
        - 业务流程: {query_info.get('business_process', '')}
        
        表格信息:
        - 表名: {table_entity['name']}
        - 描述: {table_entity['description']}
        - 字段:
        {table_headers_text}
        
        请给出一个0到1之间的相关度分数，其中1表示完全相关，0表示完全不相关。
        只返回一个数字，不要有其他文本。
        """
        
        response = self.llm.generate(prompt)
        
        # 尝试提取数值
        try:
            # 查找0到1之间的数字
            score_match = re.search(r'(\d+\.\d+|\d+)', response)
            if score_match:
                score = float(score_match.group(1))
                # 确保分数在0-1范围内
                return max(0.0, min(1.0, score))
            else:
                # 如果无法提取数字，返回默认值
                return 0.5
        except Exception as e:
            print(f"计算相关度时出错: {e}")
            return 0.5

def graph_match(query: str) -> str:
    """根据查询匹配相关表格和操作
    
    Args:
        query: 自然语言查询
        
    Returns:
        str: 匹配结果，包含相关表格和操作
    """
    # 处理特定的硬编码查询
    if query == "POD异常分析":
        return ""
    elif "订单未生成POD的原因" in query:
        return f"""
        销售订单查询工具——查询——销售订单
        POD查询工具——查询——订单POD状态
        POD异常分析节点——查询——货品比对
        POD异常分析节点——查询——缺料分析
        POD异常分析节点——查询——直发确认
        POD异常分析节点——查询——货品签收
       """
    
    # 使用语义匹配查找相关表格
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        graph_json_path = os.path.join(project_root, "table_graph.json")
        
        # 初始化表格匹配器
        matcher = TableMatcher(graph_json_path)
        
        # 匹配相关表格
        matched_tables = matcher.match_tables(query)
        
        if not matched_tables:
            return "未找到相关表格"
        
        # 构建返回结果
        result = []
        for table in matched_tables:
            result.append(f"{table['table_name']}查询工具——查询——{table['table_name']} (相关度: {table['score']:.2f})")
        
        return "\n".join(result)
    except Exception as e:
        print(f"表格匹配时出错: {e}")
        return f"表格匹配出错: {str(e)}"