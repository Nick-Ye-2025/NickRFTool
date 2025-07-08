import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime,timedelta
import numpy as np

# 设置matplotlib支持中文显示
plt.rcParams["font.family"] = ["SimHei"] #"Heiti TC" ,# "WenQuanYi Micro Hei"

#生成时间序列数据
data_rng = pd.date_range(start="2024-01-01", end="2024-01-03", freq="H")
data = {
    "日期": data_rng,
    "发射功率(dBm)": np.random.randn(len(data_rng)) * 3 + 25,
    "接收功率(dBm)": np.random.randn(len(data_rng)) * 5 + (-74),
}

# pd.DataFrame(data).to_csv("rf-test.csv", index=False, encoding="utf-8")

class CSVPlotterApp:
    def __init__(self,root):
        self.root = root
        self.root.title("CSV文件绘图工具")
        self.root.geometry("1000x800")
        # 创建全局样式
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("微软雅黑", 12))
        self.style.configure("TButton", font=("微软雅黑", 12))
        self.style.configure("TRadiobutton", font=("微软雅黑", 12))
        # 初始化变量
        self.data = None
        self.selected_columns = []

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择区域
        self.file_frame = ttk.LabelFrame(self.main_frame, text="文件选择", padding="10")
        self.file_frame.pack(fill=tk.X, pady=8)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(self.file_frame, text="文件路径:").grid(row=0, column=0, padx=5, sticky="e")
        ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=55,font=("宋体", 12)).grid(row=0, column=1, padx=8, pady=8,sticky='ew')
        ttk.Button(self.file_frame, text="浏览...", command=self.browse_file).grid(row=0, column=2, padx=8, pady=8)
        ttk.Button(self.file_frame, text="加载数据", command=self.load_data).grid(row=0, column=3, padx=8, pady=8)
        self.file_frame.columnconfigure(1, weight=1)  # 输入框所在列自动扩展

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.file_frame, variable=self.progress_var, length=200)
        self.progress_bar.grid(row=0, column=4, padx=8, pady=8,sticky="e")
        
        # 数据预览区域
        self.preview_frame = ttk.LabelFrame(self.main_frame, text="数据预览", padding="10")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.columns_frame = ttk.LabelFrame(self.preview_frame, text="可用列", padding="5")
        self.columns_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.columns_listbox = tk.Listbox(self.columns_frame, selectmode=tk.MULTIPLE, height=15,font=("宋体", 12))
        self.columns_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_frame = ttk.LabelFrame(self.preview_frame, text="数据统计", padding="5")
        self.stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_text = tk.Text(self.stats_frame, height=15, wrap=tk.WORD,font=("宋体", 12))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绘图选项区域
        self.plot_options_frame = ttk.LabelFrame(self.main_frame, text="绘图选项", padding="10")
        self.plot_options_frame.pack(fill=tk.X, pady=5)
        
        self.plot_type_var = tk.StringVar(value="line")
        ttk.Radiobutton(self.plot_options_frame, text="折线图", variable=self.plot_type_var, value="line").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(self.plot_options_frame, text="箱线图", variable=self.plot_type_var, value="box").pack(side=tk.LEFT, padx=15)

        ttk.Button(self.plot_options_frame, text="绘制图表", command=self.plot_data).pack(side=tk.RIGHT, padx=10)
        
        # 图表显示区域
        self.plot_frame = ttk.LabelFrame(self.main_frame, text="图表", padding="10")
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def browse_file(self):
        """打开文件选择对话框"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    def load_data(self):
        """加载CSV文件数据"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请选择CSV文件")
            return
        
        try:
            # 更新进度条
            self.progress_var.set(20)
            self.root.update_idletasks()
            
            # 读取CSV文件
            self.data = pd.read_csv(file_path)
            
            # 更新进度条
            self.progress_var.set(60)
            self.root.update_idletasks()
            
            # 清空列表框并添加列名
            self.columns_listbox.delete(0, tk.END)
            for col in self.data.columns:
                self.columns_listbox.insert(tk.END, col)
            
            # 生成数据统计信息
            self.stats_text.delete(1.0, tk.END)
            stats = self.data.describe().to_csv(sep='\t', na_rep='nan')
            self.stats_text.insert(tk.END, stats)
            
            # 完成进度条
            self.progress_var.set(100)
            
            messagebox.showinfo("成功", "数据加载完成")
        except Exception as e:
            messagebox.showerror("错误", f"加载数据时出错: {str(e)}")
            self.progress_var.set(0)
    
    def plot_data(self):
        """根据选择绘制图表"""
        if self.data is None:
            messagebox.showwarning("警告", "请先加载数据")
            return
        
        # 获取选中的列
        selected_indices = self.columns_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请选择要绘制的列")
            return
        
        self.selected_columns = [self.columns_listbox.get(i) for i in selected_indices]
        
        # 清空当前图表，Axes对象负责管理坐标系，Figure对象负责管理绘图区域
        self.ax.clear()
        
        # 根据选择的图表类型绘制
        plot_type = self.plot_type_var.get()
        
        if plot_type == "line":
            # 绘制折线图
            for col in self.selected_columns:
                if pd.api.types.is_numeric_dtype(self.data[col]):
                    self.ax.plot(self.data[col], label=col)
                else:
                    # 尝试将列转换为数值类型
                    try:
                        numeric_data = pd.to_numeric(self.data[col], errors='coerce')
                        self.ax.plot(numeric_data, label=col)
                    except:
                        messagebox.showwarning("警告", f"列 '{col}' 无法转换为数值类型，不能绘制折线图")
            
            self.ax.set_title("折线图")
            self.ax.set_xlabel("索引")
            self.ax.set_ylabel("值")
            self.ax.legend()
        
        elif plot_type == "box":
            # 绘制箱线图
            box_data = []
            valid_columns = []
            
            for col in self.selected_columns:
                if pd.api.types.is_numeric_dtype(self.data[col]):
                    box_data.append(self.data[col].dropna())
                    valid_columns.append(col)
                else:
                    # 尝试将列转换为数值类型
                    try:
                        numeric_data = pd.to_numeric(self.data[col], errors='coerce').dropna()
                        if not numeric_data.empty:
                            box_data.append(numeric_data)
                            valid_columns.append(col)
                    except:
                        messagebox.showwarning("警告", f"列 '{col}' 无法转换为数值类型，不能绘制箱线图")
            
            if box_data:
                self.ax.boxplot(box_data, labels=valid_columns)
                self.ax.set_title("箱线图")
                self.ax.set_ylabel("值")
            else:
                messagebox.showwarning("警告", "没有找到合适的数值列来绘制箱线图")
        # 更新画布
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVPlotterApp(root)
    root.mainloop()