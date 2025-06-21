from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt

class SearchTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self._all_items = []

    def addTopLevelItem(self, item):
        super().addTopLevelItem(item)
        self._cache_items(item)

    def filter_items(self, text):
        query = text.lower()
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item.setHidden(not self._item_contains_text(item, query))
            iterator += 1

    def _item_contains_text(self, item, query):
        if query in item.text(0).lower():
            return True
        # 展开父节点如果子节点匹配
        for i in range(item.childCount()):
            if self._item_contains_text(item.child(i), query):
                return True
        return False

    def _cache_items(self, parent_item):
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            self._all_items.append(child)
            if child.childCount() > 0:
                self._cache_items(child)