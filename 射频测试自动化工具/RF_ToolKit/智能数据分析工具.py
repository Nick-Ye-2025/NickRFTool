import re
import difflib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import sys
import threading
import platform
import matplotlib
matplotlib.use('Agg')  # 禁用GUI后端
import pandas as pd
import subprocess
from datetime import datetime
import shutil
# ======================
# 输出重定向核心类
# ======================
class TimestampRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.last_timestamp = None
        self.lock = threading.Lock()

    def write(self, msg):
        with self.lock:
            msg = self.ansi_escape.sub('', msg)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.last_timestamp == current_time:
                formatted_msg = f"{msg}"
            else:
                formatted_msg = f"{current_time} -INFO- {msg}"
                self.last_timestamp = current_time

            self.text_widget.insert(tk.END, formatted_msg)
            self.text_widget.see(tk.END)
        
    def flush(self):
        pass
# ======================
# Excel文件处理模块
# ======================
class ExcelHandler:
    @staticmethod
    def display_excel(file_path, text_widget):
        text_widget.delete(1.0, tk.END)
        try:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                df = excel_file.parse(sheet_name)
                text_widget.insert(tk.END, f"\n=== {sheet_name} ===\n")
                text_widget.insert(tk.END, df.to_string(index=False) + "\n")
        except Exception as e:
            text_widget.insert(tk.END, f"Error reading Excel file: {str(e)}")

    @staticmethod
    def compare_excel(file1, file2, text_widget):
        try:
            excel1 = pd.ExcelFile(file1)
            excel2 = pd.ExcelFile(file2)
            
            text_widget.tag_config("diff", foreground="red")
            text_widget.delete(1.0, tk.END)
            
            for sheet_name in excel1.sheet_names:
                if sheet_name in excel2.sheet_names:
                    df1 = excel1.parse(sheet_name)
                    df2 = excel2.parse(sheet_name)
                    
                    diff = pd.concat([df1, df2]).drop_duplicates(keep=False)
                    if not diff.empty:
                        text_widget.insert(tk.END, f"\n=== {sheet_name} 差异 ===\n", "diff")
                        text_widget.insert(tk.END, diff.to_string(index=False) + "\n", "diff")
                    else:
                        text_widget.insert(tk.END, f"\n=== {sheet_name} 无差异 ===\n")
                else:
                    text_widget.insert(tk.END, f"\n=== {sheet_name} 仅存在于文件1 ===\n", "diff")
                    
            for sheet_name in excel2.sheet_names:
                if sheet_name not in excel1.sheet_names:
                    text_widget.insert(tk.END, f"\n=== {sheet_name} 仅存在于文件2 ===\n", "diff")
                    
        except Exception as e:
            text_widget.insert(tk.END, f"Error comparing Excel files: {str(e)}")
# ======================
# 文本对比模块
# ======================
class TextComparer:
    @staticmethod
    def compare_text(text1, text2, text_widget):
        text_widget.tag_config("diff", foreground="red")
        text_widget.delete(1.0, tk.END)
        
        d = difflib.Differ()
        diff = list(d.compare(text1.splitlines(), text2.splitlines()))
        
        for line in diff:
            if line.startswith('  '):
                text_widget.insert(tk.END, line[2:] + '\n')
            elif line.startswith('- ') or line.startswith('+ '):
                text_widget.insert(tk.END, line[2:] + '\n', "diff")
            else:
                text_widget.insert(tk.END, line + '\n')
# ======================
# VNC远程连接模块
# ======================
class VNCConnector:
    @staticmethod
    def connect_vnc(ip_address):
        try:
            username = "gdlocal"
            password = "gdlocal"
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", f"vnc://{username}:{password}@{ip_address}"])
            elif platform.system() == "Windows":  # Windows
                subprocess.run(["mstsc", f"/v:{ip_address}"])
            else:  # Linux
                subprocess.run(["vncviewer", f"{username}:{password}@{ip_address}"])
            return True
        except Exception as e:
            messagebox.showerror("连接失败", f"无法建立VNC连接: {str(e)}")
            return False
# ======================
# 数据清理功能
# ======================
class DataCleaner:
    @staticmethod
    def coarse_tune(path):
        """
        递归清理冗余目录（压缩包和同名文件夹）
        """
        try:
            for root, dirs, files in os.walk(path):
                dir_list = []
                file_list = []
                
                # 获取当前目录下的文件夹和文件
                for name in dirs:
                    dir_list.append(name)
                for name in files:
                    file_list.append(name)
                
                # 检查是否有同名压缩包和文件夹
                dir_addzip = [item + '.zip' for item in dir_list]
                same_items = [item for item in dir_addzip if item in file_list]
                
                # 删除同名文件夹
                for same in same_items:
                    target_dir = same.replace('.zip', '')
                    target_path = os.path.join(root, target_dir)
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                        print(f'已删除冗余目录: {target_path}')
                        
        except Exception as e:
            print(f'粗清理出错: {str(e)}')

    @staticmethod
    def fine_tune(path):
        """
        递归清理子目录中的 blob 文件夹和 CSV 文件
        """
        try:
            for root, dirs, files in os.walk(path):
                # 删除 blob 文件夹
                if 'test_station_output_blob' in dirs:
                    blob_path = os.path.join(root, 'test_station_output_blob')
                    backup_path = os.path.join('备份', datetime.now().strftime('%Y-%m-%d'))
                    os.makedirs(backup_path, exist_ok=True)
                    shutil.copytree(blob_path, os.path.join(backup_path, 'test_station_output_blob'))
                    shutil.rmtree(blob_path)
                    print(f'已备份并删除: {blob_path}')
                    dirs.remove('test_station_output_blob')  # 避免重复遍历

                # 清理 CSV 文件
                if 'test_station_output_logs' in dirs:
                    logs_path = os.path.join(root, 'test_station_output_logs')
                    for sub_root, _, sub_files in os.walk(logs_path):
                        for file in sub_files:
                            if file.endswith('.csv') and not file.endswith(('Alchemy.csv', 'Global_Offset.csv')):
                                dump_csv = os.path.join(sub_root, file)
                                try:
                                    os.remove(dump_csv)
                                    print(f'已删除CSV文件: {dump_csv}')
                                except OSError:
                                    print('资源紧张😓，跳过当前文件')
                    dirs.remove('test_station_output_logs')  # 避免重复遍历
                    
        except Exception as e:
            print(f'精细清理出错: {str(e)}')

    @classmethod
    def clean_data(cls):
        """
        执行数据清理
        """
        path = filedialog.askdirectory(title='选择要清理的文件夹')
        # if not path:
        #     return
        
        print(f'开始清理: {path}')
        cls.coarse_tune(path)  # 先进行粗清理
        cls.fine_tune(path)     # 再进行精细清理
        print('清理完成!')
# ======================
# 网络服务管理模块（macOS专用）
# ======================
class NetworkSwitcher:
    @staticmethod
    def get_service_order():
        try:
            output = subprocess.check_output(
                ["networksetup", "-listnetworkserviceorder"],
                stderr=subprocess.STDOUT,
                text=True
            )
            services = []
            pattern = re.compile(r'\(\d+\)\s+(.*)')
            for line in output.split('\n'):
                if 'Hardware Port' in line:
                    match = pattern.search(line)
                    if match:
                        services.append(match.group(1))
            return services
        except subprocess.CalledProcessError as e:
            raise Exception(f"获取网络服务失败: {e.output}")

    @staticmethod
    def switch_ethernet_priority():
        try:
            services = NetworkSwitcher.get_service_order()
            target_services = ["Ethernet", "Apple USB Ethernet Adapter"]
            indexes = []
            for service in target_services:
                try:
                    indexes.append(services.index(service))
                except ValueError:
                    pass

            if len(indexes) < 2:
                raise Exception("找不到需要切换的网络服务")

            services[indexes[0]], services[indexes[1]] = services[indexes[1]], services[indexes[0]]
            cmd = ["sudo", "networksetup", "-ordernetworkservices"] + services
            subprocess.run(
                ["osascript", "-e", f'do shell script "{ " ".join(cmd) }" with administrator privileges'],
                check=True
            )
            return True
        except Exception as e:
            raise Exception(f"网络切换失败: {str(e)}")
# ======================
# GUI主界面
# ======================
class MainApplication(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()        
        self.title("智能数据分析工具 v5.2")
        self.geometry("1280x720")
        self.configure_ui()
        sys.stdout = TimestampRedirector(self.output_text)
        
    def configure_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 功能按钮组
        buttons = [
            ("时间解析", self.timing_breakdown),
            ("异常分析", self.abnormal_analysis),
            ("数据减压", self.data_eraser),
            ("数据上传", self.data_upload_radar),
            ("工站远程", self.show_vnc_dialog),
            ("对比文件", self.compare_files),
            ("连接机台", self.connect_device),
            ("切换网络", self.switch_network)
        ]
        
        for text, cmd in buttons:
            btn = ttk.Button(toolbar, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2)
        
        # 双文件对比面板
        compare_frame = ttk.Frame(self)
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左文件面板
        self.left_panel = self.create_file_panel(compare_frame, "文件1", width=50)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        # 右文件面板
        self.right_panel = self.create_file_panel(compare_frame, "文件2", width=50)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
        
        # 日志输出
        console_frame = ttk.Labelframe(self, text="系统日志")
        console_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5, ipady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            console_frame, 
            height=10, 
            wrap=tk.WORD,
            font=('Menlo', 10) if platform.system() == 'Darwin' else ('Consolas', 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 版权信息
        copyright_frame = ttk.Frame(self)
        copyright_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Label(copyright_frame, 
                 text="Copyright © 2025 Nick_Ye 版权所有",
                 font=('Arial', 8),
                 foreground="gray").pack()

    def create_file_panel(self, parent, title, width=60):
        """创建文件面板"""
        frame = ttk.Frame(parent)
        
        # 标题栏
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=2)
        
        # 标题
        ttk.Label(header, text=title).pack(side=tk.LEFT)
        
        # 路径输入框
        path_entry = ttk.Entry(header, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 拖放支持
        path_entry.drop_target_register(DND_FILES)
        path_entry.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, path_entry, frame))
        
        # 操作按钮
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="浏览", command=lambda: self.load_file(frame)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="清除", command=lambda: self.clear_panel(frame)).pack(side=tk.LEFT)
        
        # 文本区域
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=width)
        if platform.system() == 'Darwin':
            text.configure(font=('Menlo', 12))  # macOS字体
        else:
            text.configure(font=('Courier New', 10))  # Windows/Linux字体
        text.pack(fill=tk.BOTH, expand=True)
        
        # 保存组件引用
        frame.text = text
        frame.path_entry = path_entry
        frame.path = None
        return frame
        
    def handle_drop(self, event, entry_widget, target_frame):
        """处理文件拖放事件"""
        files = self.parse_dropped_files(event.data)
        if files:
            file_path = files[0]
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
            self.load_file_to_panel(file_path, target_frame)
        
    def parse_dropped_files(self, data):
        """解析拖放的文件路径"""
        files = []
        if platform.system() == 'Windows':
            files = [data.replace('{', '').replace('}', '')]  # Windows路径处理
        else:
            files = data.split()  # macOS/Linux路径处理
        return [f.strip() for f in files if os.path.exists(f.strip())]
        
    def load_file(self, panel):
        """通过文件对话框加载文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), 
                      ("Excel files", "*.xlsx"), 
                      ("All files", "*.*")]
        )
        if file_path:
            panel.path_entry.delete(0, tk.END)
            panel.path_entry.insert(0, file_path)
            self.load_file_to_panel(file_path, panel)
            
    def load_file_to_panel(self, file_path, panel):
        """加载文件内容到面板"""
        try:
            panel.path = file_path
            if file_path.endswith('.xlsx'):
                ExcelHandler.display_excel(file_path, panel.text)  # 加载Excel文件
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    panel.text.insert(tk.END, f.read())  # 加载文本文件
        except Exception as e:
            messagebox.showerror("错误", f"文件加载失败: {str(e)}")
        
    def clear_panel(self, panel):
        """清空面板内容"""
        panel.path = None
        panel.path_entry.delete(0, tk.END)
        panel.text.delete(1.0, tk.END)
        
    def compare_files(self):
        """文件对比功能"""
        if not self.left_panel.path or not self.right_panel.path:
            messagebox.showwarning("警告", "请先选择两个文件")
            return
        
        if self.left_panel.path.endswith('.xlsx') and self.right_panel.path.endswith('.xlsx'):
            ExcelHandler.compare_excel(self.left_panel.path, self.right_panel.path, self.output_text)  # Excel对比
        else:
            text1 = self.left_panel.text.get(1.0, tk.END)
            text2 = self.right_panel.text.get(1.0, tk.END)
            TextComparer.compare_text(text1, text2, self.output_text)  # 文本对比
        
    def show_vnc_dialog(self):
        """显示VNC连接对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("VNC连接")
        dialog.geometry("300x100")
        
        ttk.Label(dialog, text="输入IP地址:").pack(pady=5)
        ip_entry = ttk.Entry(dialog)
        ip_entry.pack(pady=5)
        
        def connect():
            ip = ip_entry.get()
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                if VNCConnector.connect_vnc(ip):
                    dialog.destroy()
            else:
                messagebox.showwarning("错误", "请输入有效的IP地址")
        
        ttk.Button(dialog, text="连接", command=connect).pack(pady=5)
        ip_entry.bind("<Return>", lambda e: connect())
        
    def connect_device(self):
        """连接机台功能"""
        def run():
            self.output_text.insert(tk.END, "正在初始化设备连接...\n")
            SSHConnector.connect_device()
            self.output_text.insert(tk.END, "设备连接已建立\n")
            
        threading.Thread(target=run, daemon=True).start()

    def switch_network(self):
        """切换网络功能"""
        def network_task():
            try:
                if platform.system() != 'Darwin':
                    messagebox.showwarning("警告", "该功能仅支持macOS系统")
                    return
                
                print("正在切换网络服务顺序...")
                NetworkSwitcher.switch_ethernet_priority()
                print("网络服务顺序已更新！当前顺序：")
                services = NetworkSwitcher.get_service_order()
                print("\n".join([f"{i+1}. {s}" for i, s in enumerate(services)]))
                
            except Exception as e:
                print(f"操作失败: {str(e)}")
        
        threading.Thread(target=network_task, daemon=True).start()

    def timing_breakdown(self):
        """时间解析功能"""
        print("时间解析功能开发中...")
        
    def abnormal_analysis(self):
        """异常分析功能"""
        print("异常分析功能开发中...")
        
    def data_eraser(self):
        """数据清理功能"""
        threading.Thread(target=DataCleaner.clean_data, daemon=True).start()
        
    def data_upload_radar(self):
        """数据上传功能"""
        print("数据上传功能开发中...")
# ======================
# 启动程序
# ======================
if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()