# -*- coding: utf-8 -*-
import sys
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
                           QTextEdit, QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor
import platform

class ToolPlatform(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initial_expansion={}
        self.initial_item_order={}
        self.mouse_pressed = False
        self.mouse_position = QPoint()
        self.running_tools = {}  # {工具名: {'process': Popen对象, 'start_time': datetime}}
        self.initUI()
        self.load_tools()
        self.apply_theme()
        
        # 初始化定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)
        self.check_process_timer = QTimer(self)
        self.check_process_timer.timeout.connect(self.check_process_status)
        self.check_process_timer.start(1000)

    def apply_theme(self):
        base_style = """
        QWidget {
            background: #F5F5F7;
            color: #333333;
        }
        QTextEdit {
            background: #FFFFFF;
            border: 1px solid #D1D1D6;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton {
            background: #E0E0E6;
            color: #333333;
            min-width: 40px;
            padding: 4px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background: #D1D1D6;
        }
        QTableWidget {
            background: #FFFFFF;
            alternate-background-color: #F8F8F9;
            gridline-color: #E0E0E6;
        }
        QLabel {
            color: #666666;
            font-weight: bold;
            padding: 8px 4px;
        }
        QTreeWidget {
            border: 1px solid #D1D1D6;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(base_style)

    def initUI(self):
        self.setWindowTitle('OmniaNode')
        self.setGeometry(100, 100, 1280, 720)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 左侧面板
        left_panel = QVBoxLayout()
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("工具选择"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入工具名称...")
        self.search_input.setFixedWidth(180)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border-radius: 15px;
                padding: 5px 12px;
                border: 1px solid #D1D1D6;
            }
        """)
        self.search_input.textChanged.connect(self.filter_tools)
        title_layout.addWidget(self.search_input)
        left_panel.addLayout(title_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tool_selected)
        left_panel.addWidget(self.tree)
        main_layout.addLayout(left_panel, stretch=1)
        
        # 右侧面板（调整布局比例）
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("状态监控"), stretch=1)
        
        self.monitor_panel = QTableWidget()
        self.monitor_panel.setColumnCount(5)
        self.monitor_panel.setHorizontalHeaderLabels(["工具名称", "状态", "启动时间", "运行时长", "资源占用", "操作"])
        self.monitor_panel.horizontalHeader().setStretchLastSection(True)
        self.monitor_panel.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        right_panel.addWidget(self.monitor_panel, stretch=2)
        
        right_panel.addWidget(QLabel("工具信息"), stretch=1)
        self.tool_area = QTextEdit()
        self.tool_area.setReadOnly(True)
        right_panel.addWidget(self.tool_area, stretch=3)
        
        right_panel.addWidget(QLabel("日志输出"), stretch=1)
        self.console = QTextEdit()
        right_panel.addWidget(self.console, stretch=2)
        
        main_layout.addLayout(right_panel, stretch=3)
        main_widget.setLayout(main_layout)
        
        # 顶部控制栏（带居中标题）
        control_bar = QHBoxLayout()
        self.time_label = QLabel()
        control_bar.addWidget(self.time_label)
        
        control_bar.addStretch()
        title_label = QLabel("OmniaNode 全能工具平台")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        control_bar.addWidget(title_label)
        control_bar.addStretch()
        
        self.min_btn = QPushButton("－")
        self.close_btn = QPushButton("×")
        self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn.clicked.connect(self.cleanup_before_exit)
        control_bar.addWidget(self.min_btn)
        control_bar.addWidget(self.close_btn)
        
        # 根布局
        root_layout = QVBoxLayout()
        root_layout.addLayout(control_bar)
        root_layout.addWidget(main_widget)
        
        # 版权信息
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(QLabel("Copyright © 2025 NickYe 版权所有"))
        root_layout.addLayout(footer)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)
        self.update_dashboard()

    def update_dashboard(self):
        self.update_time()
        self.update_monitor()
    
    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.time_label.setText(current_time)

    def update_monitor(self):
        while self.monitor_panel.rowCount() > 0:
            self.monitor_panel.removeRow(0)
        
        for tool_name, info in self.running_tools.items():
            row = self.monitor_panel.rowCount()
            self.monitor_panel.insertRow(row)
            
            status = "运行中" if info['process'].poll() is None else "已停止"
            runtime = datetime.now() - info['start_time']
            runtime_str = f"{runtime.seconds//60:02d}:{runtime.seconds%60:02d}"
            
            # 状态颜色标记
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(0, 200, 0) if status == "运行中" else QColor(200, 0, 0))
            
            self.monitor_panel.setItem(row, 0, QTableWidgetItem(tool_name))
            self.monitor_panel.setItem(row, 1, status_item)
            self.monitor_panel.setItem(row, 2, QTableWidgetItem(info['start_time'].strftime("%H:%M:%S")))
            self.monitor_panel.setItem(row, 3, QTableWidgetItem(runtime_str))
            self.monitor_panel.setItem(row, 4, QTableWidgetItem(
                f"内存: {100 + runtime.seconds*2}MB" if status == "运行中" else "已释放"
            ))

    def check_process_status(self):
        current_time = datetime.now()
        for tool_name in list(self.running_tools.keys()):
            info = self.running_tools[tool_name]
            # 进程已结束且超过5秒
            if info['process'].poll() is not None:
                if 'end_time' not in info:
                    info['end_time'] = current_time
                    self.console.append(f"[{current_time.strftime('%H:%M:%S')}] {tool_name} 已停止")
                elif (current_time - info['end_time']).seconds > 5:
                    del self.running_tools[tool_name]

    def cleanup_before_exit(self):
        # 终止所有运行中的进程
        for tool_name, info in self.running_tools.items():
            if info['process'].poll() is None:
                info['process'].terminate()
        self.close()

    def load_tools(self):
        categories = {
            "脚本工具": ["PackWiAPSmini", "DataEraser","ConnectDUT"],
            "系统工具": ["进程监控", "网络诊断","NetSwitch"],
            "开发工具": ["代码格式化", "API测试"]
        }
        for cat, tools in categories.items():
            parent = QTreeWidgetItem(self.tree, [cat])
            parent.setExpanded(True)
            for tool in tools:
                QTreeWidgetItem(parent, [tool])
            self.initial_expansion[cat] = True
            self.initial_item_order[cat] = tools.copy()
    def on_tool_selected(self, item):
        if not item.parent(): return
        tool_name = item.text(0)
        self.execute_tool(tool_name)
        self.console.append(f"[{datetime.now().strftime('%H:%M:%S')}] 用户启动了：{tool_name}")

    def execute_tool(self, tool_name):
        if tool_name == "清理脚本":
            try:
                process = subprocess.Popen([sys.executable, r"d:\Nick\BeyondC\一键开天门.py"])
                start_time = datetime.now()
                self.running_tools[tool_name] = {
                    'process': process,
                    'start_time': start_time
                }
                self.console.append(f"[{start_time.strftime('%H:%M:%S')}] 成功启动：{tool_name}")
            except Exception as e:
                self.console.append(f"[ERROR] {tool_name} 启动失败：{str(e)}")

    def filter_tools(self):
        keyword = self.search_input.text().lower()
        
        def check_item(item):            
            if not item.parent():  # 分类节点
                has_visible_child = False
                if keyword:
                    item.setExpanded(True)
                else:
                    cat_name=item.text(0)
                    item.setExpanded(self.initial_expansion.get(cat_name,True))
                    item.setBackground(0, QColor(245, 245, 247))
                    item.setForeground(0, QColor(0, 0, 0))

                for i in range(item.childCount()):
                    child = item.child(i)
                    if check_item(child):
                        has_visible_child = True
                item.setHidden(not has_visible_child and bool(keyword))
                return has_visible_child
            else:  # 工具节点
                tool_name = item.text(0).lower()
                match = keyword in tool_name if keyword else True
                bg_color = QColor(255, 255, 150) if keyword and match else QColor(245, 245, 247)
                # 恢复原始背景色#F5F5F7
                item.setBackground(0, bg_color)
                item.setForeground(0, QColor(0, 0, 0))

                if keyword:
                    item.setHidden(not match)
                else:
                    parent = item.parent()
                    tools=self.initial_item_order.get(parent.text(0),[])
                    try:
                        original_index=tools.index(item.text(0))
                        parent.removeChild(item)
                        parent.insertChild(original_index,item)
                    except ValueError:
                        pass
                return match
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            check_item(category_item)
        
        if not keyword:
            root=self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                cat_item = root.child(i)
                cat_name = cat_item.text(0)
                cat_item.setExpanded(self.initial_expansion.get(cat_name, True))
                for j in range(cat_item.childCount()):
                    child=cat_item.child(j)
                    child.setHidden(False)

    # 鼠标事件处理
    def mousePressEvent(self, event):
        self.mouse_pressed = True
        self.mouse_position = event.globalPos() - self.pos()
        
    def mouseMoveEvent(self, event):
        if self.mouse_pressed:
            self.move(event.globalPos() - self.mouse_position)
            
    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if platform.system() == 'Windows':
        app.setFont(QFont('Microsoft Yahei', 10))
    elif platform.system() == 'Darwin':
        app.setFont(QFont('PingFang SC', 13))
    ex = ToolPlatform()
    ex.show()
    sys.exit(app.exec_())