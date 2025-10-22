import time
from typing import Dict, List, Any
from pydantic import BaseModel, Field
# {
#     "user_input": "用户查询输入",
#     "experience_nld": "可能与用户输入相关的案例经验",
#     "related_graph": "与用户输入相关的知识图谱上的节点和子图",
#     "think_process": "自然语言描述的思考或推理过程",
#     "plan": "plan的todo list",
#     "data_results": "中间过程工具获取的数据或者执行结果",
#     "output": "最终输出结果"
# }

class Whiteboard(BaseModel):
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="按时间顺序存储所有事件")
    
    _instance = None
    _initialized = False

    def __new__(cls, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, **data):
        if not self._initialized:
            super().__init__(**data)
            if not hasattr(self, 'timeline') or self.timeline is None:
                self.timeline = []
            self._initialized = True
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False

    def user_input(self, content: Dict[str, Any]):
        self.add_entry("user_input", content)
    
    def experience_nld(self, content: Dict[str, Any]):
        self.add_entry("experience_nld", content)
        
    def related_graph(self, content: Dict[str, Any]):
        self.add_entry("related_graph", content)
        
    def thought_process(self, content: Dict[str, Any]):
        self.add_entry("thought_process", content)
        
    def plan(self, content: Dict[str, Any]):
        self.add_entry("plan", content)

    def update_plan(self, content: Dict[str, Any]):
        self.remove_entry("plan")
        self.add_entry("plan", content)
        
    def data_results(self, content: Dict[str, Any]):
        self.add_entry("data_results", content)
        
    def output(self, content: Dict[str, Any]):
        self.add_entry("output", content)
        
    def add_entry(self, data_type: str, content: Dict[str, Any]):
        entry = {
            "type": data_type,  # user_input, experience_nld, related_graph, thought_process, plan, data_results, output
            "content": content
        }
        self.timeline.append(entry)

    def remove_entry(self, data_type: str):
        self.timeline = [e for e in self.timeline if not (e["type"] == data_type)]
        
    def get_latest_entry(self, data_type: str = None):
        if not self.timeline:
            return None
        if data_type:
            for e in self.timeline[::-1]:
                if e["type"] == data_type:
                    return e
        else:
            return self.timeline[-1]
        
    def get_entries(self, data_type: str = None, since: float = None):
        results = self.timeline
        return results

    def summarize_entries_as_string(self):
        summary = ""
        for e in self.timeline:
            summary += f"{e['type']}: {str(e['content'])[:80]}\n"
        return summary

