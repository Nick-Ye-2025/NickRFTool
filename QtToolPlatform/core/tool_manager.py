import os
import json
from PyQt5.QtWidgets import QTreeWidgetItem

class ToolManager:
    def __init__(self):
        self.tools_path = os.path.join(os.path.dirname(__file__), '../config/tools')
        
    def load_tools(self, tree_widget):
        """动态加载工具配置"""
        # 清空现有工具
        tree_widget.clear()
        
        # 分类收集工具
        categories = {}
        for config_file in os.listdir(self.tools_path):
            if config_file.endswith('.json'):
                with open(os.path.join(self.tools_path, config_file), 'r', encoding='utf-8') as f:
                    tools = json.load(f)
                    category = tools.get('category', '未分类')
                    if category not in categories:
                        categories[category] = []
                    categories[category].extend(tools['items'])

        # 分类排序并创建树节点
        for cat in sorted(categories.keys(), key=self._sort_key):
            parent = QTreeWidgetItem(tree_widget, [cat])
            tools = sorted(categories[cat], key=lambda x: x['name'])
            for tool in tools:
                QTreeWidgetItem(parent, [tool['name']])

    def _sort_key(self, category):
        """中英文分类排序逻辑"""
        if any('\u4e00' <= char <= '\u9fff' for char in category):
            return (1, category)  # 中文分类在后
        return (0, category.lower())