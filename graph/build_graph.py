import os
import re
import json
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

class TableHeaderGraphBuilder:
    def __init__(self, headers_dir):
        """初始化图谱构建器
        
        Args:
            headers_dir: 表头文件所在目录
        """
        self.headers_dir = headers_dir
        self.graph = nx.DiGraph()
        self.entities = {}
        self.relationships = []
        
    def parse_md_files(self):
        """解析所有的markdown表头文件"""
        md_files = list(Path(self.headers_dir).glob('*.md'))
        
        for md_file in md_files:
            self._parse_single_file(md_file)
            
    def _parse_single_file(self, file_path):
        """解析单个markdown文件
        
        Args:
            file_path: markdown文件路径
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取表名
        table_name_match = re.search(r'# table name\s+(.+)', content)
        if not table_name_match:
            return
            
        table_name = table_name_match.group(1).strip()
        
        # 提取表描述
        table_desc_match = re.search(r'# table description\s+(.+)', content)
        table_desc = table_desc_match.group(1).strip() if table_desc_match else ""
        
        # 提取表头信息
        headers_section = re.search(r'# headers description\s+\|.+\|\s+\|.+\|(.*?)(?:# example|\Z)', 
                                   content, re.DOTALL)
        
        if not headers_section:
            return
            
        headers_text = headers_section.group(1).strip()
        headers = []
        
        # 解析每个表头
        for line in headers_text.split('\n'):
            if '|' not in line or line.strip().startswith('---'):
                continue
                
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                header_name = parts[1].strip()
                header_desc = parts[2].strip()
                
                if header_name and header_desc:
                    headers.append({
                        'name': header_name,
                        'description': header_desc
                    })
        
        # 添加实体到图谱
        entity_id = file_path.stem
        self.entities[entity_id] = {
            'id': entity_id,
            'name': table_name,
            'description': table_desc,
            'headers': headers
        }
        
        self.graph.add_node(entity_id, 
                           name=table_name, 
                           description=table_desc,
                           type='table')
        
        # 查找外键关系
        for header in headers:
            if '外键' in header['description'] and '关联到' in header['description']:
                # 提取关联的表名
                related_table_match = re.search(r'关联到(.+?)表', header['description'])
                if related_table_match:
                    related_table = related_table_match.group(1).strip()
                    
                    # 查找目标实体
                    target_entity_id = None
                    for eid, entity in self.entities.items():
                        if entity['name'] == related_table or related_table in entity['name']:
                            target_entity_id = eid
                            break
                    
                    if target_entity_id:
                        relation = {
                            'source': entity_id,
                            'target': target_entity_id,
                            'name': f"has_{header['name']}",
                            'description': header['description']
                        }
                        self.relationships.append(relation)
                        self.graph.add_edge(entity_id, target_entity_id, 
                                          name=relation['name'],
                                          description=relation['description'])
    
    def build_graph(self):
        """构建知识图谱"""
        self.parse_md_files()
        return self.graph
    
    def visualize_graph(self, output_file=None):
        """可视化知识图谱
        
        Args:
            output_file: 输出文件路径，如果为None则显示图像
        """
        plt.figure(figsize=(12, 10))
        pos = nx.spring_layout(self.graph)
        
        # 绘制节点
        nx.draw_networkx_nodes(self.graph, pos, node_size=2000, node_color='lightblue')
        
        # 绘制边
        nx.draw_networkx_edges(self.graph, pos, width=1.5, arrowsize=20)
        
        # 绘制标签
        labels = {node: self.graph.nodes[node]['name'] for node in self.graph.nodes}
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=12)
        
        # 绘制边标签
        edge_labels = {(u, v): self.graph.edges[u, v]['name'] for u, v in self.graph.edges}
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=10)
        
        plt.axis('off')
        
        if output_file:
            plt.savefig(output_file, format='png', dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def export_to_json(self, output_file):
        """导出图谱到JSON文件
        
        Args:
            output_file: 输出文件路径
        """
        graph_data = {
            'entities': list(self.entities.values()),
            'relationships': self.relationships
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        return output_file

# 使用示例
if __name__ == "__main__":
    headers_dir = "/home/wangling/projects/agents_herd/data/table_headers"
    builder = TableHeaderGraphBuilder(headers_dir)
    graph = builder.build_graph()
    
    # 可视化图谱
    builder.visualize_graph("table_graph.png")
    
    # 导出到JSON
    builder.export_to_json("table_graph.json")
    
    print(f"图谱构建完成，共有 {len(builder.entities)} 个实体和 {len(builder.relationships)} 个关系")