from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton
from PyQt5.QtCore import pyqtSignal

class EnhancedTable(QTableWidget):
    process_stop = pyqtSignal(str)  # 信号：工具名称
    
    def __init__(self):
        super().__init__()
        self.setColumnCount(6)  # 新增操作列
        self.setHorizontalHeaderLabels(["工具名称", "状态", "启动时间", "运行时长", "资源占用", "操作"])
        
    def add_process(self, tool_name, info):
        row = self.rowCount()
        self.insertRow(row)
        
        # 原有列设置...
        # 新增操作按钮
        stop_btn = QPushButton("终止")
        stop_btn.clicked.connect(lambda: self._on_stop_clicked(tool_name))
        self.setCellWidget(row, 5, stop_btn)
        
    def _on_stop_clicked(self, tool_name):
        self.process_stop.emit(tool_name)