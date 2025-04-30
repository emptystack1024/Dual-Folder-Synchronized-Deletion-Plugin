import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import sys

class SyncFileViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("同步文件查看器")
        self.geometry("1200x700")
        
        self.folder1_path = ""
        self.folder2_path = ""
        self.thumbnail_size = (100, 100)
        self.current_files = {"left": [], "right": []}
        
        # 添加多选支持
        self.selected_files = {"left": set(), "right": set()}
        self.last_selected = {"left": None, "right": None}
        self.shift_pressed = False
        self.ctrl_pressed = False
        
        # 创建自定义样式
        self.style = ttk.Style()
        self.style.configure("Selected.TFrame", background="#4a90e2")
        
        self.create_widgets()
        self.bind_keys()
        
    def bind_keys(self):
        # 绑定Shift和Ctrl键
        self.bind("<KeyPress-Shift_L>", lambda e: self.set_shift_state(True))
        self.bind("<KeyRelease-Shift_L>", lambda e: self.set_shift_state(False))
        self.bind("<KeyPress-Shift_R>", lambda e: self.set_shift_state(True))
        self.bind("<KeyRelease-Shift_R>", lambda e: self.set_shift_state(False))
        self.bind("<KeyPress-Control_L>", lambda e: self.set_ctrl_state(True))
        self.bind("<KeyRelease-Control_L>", lambda e: self.set_ctrl_state(False))
        self.bind("<KeyPress-Control_R>", lambda e: self.set_ctrl_state(True))
        self.bind("<KeyRelease-Control_R>", lambda e: self.set_ctrl_state(False))
        
        # 移除错误的Control键绑定
        # self.bind("<KeyPress-Control-Key>", lambda e: self.set_ctrl_state(True))
        # self.bind("<KeyRelease-Control-Key>", lambda e: self.set_ctrl_state(False))
    
    def set_shift_state(self, state):
        self.shift_pressed = state
        self.status_var.set(f"Shift键: {'按下' if state else '释放'}")
    
    def set_ctrl_state(self, state):
        self.ctrl_pressed = state
        self.status_var.set(f"Ctrl键: {'按下' if state else '释放'}")
        
    def create_widgets(self):
        # 顶部控制区域
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text="文件夹1:").grid(row=0, column=0, padx=5, pady=5)
        self.folder1_entry = ttk.Entry(control_frame, width=40)
        self.folder1_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="浏览...", command=lambda: self.browse_folder(1)).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(control_frame, text="文件夹2:").grid(row=1, column=0, padx=5, pady=5)
        self.folder2_entry = ttk.Entry(control_frame, width=40)
        self.folder2_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="浏览...", command=lambda: self.browse_folder(2)).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Button(control_frame, text="加载文件", command=self.load_files).grid(row=0, column=3, rowspan=2, padx=5, pady=5)
        
        # 添加删除选中文件的按钮
        ttk.Button(control_frame, text="删除选中", command=self.delete_selected_files).grid(row=0, column=4, rowspan=2, padx=5, pady=5)
        
        # 主显示区域 - 左右分屏
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧文件显示
        left_frame = ttk.LabelFrame(main_frame, text="文件夹1")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.left_canvas = tk.Canvas(left_frame)
        left_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.on_left_scroll)
        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.left_frame_inner = ttk.Frame(self.left_canvas)
        self.left_canvas.create_window((0, 0), window=self.left_frame_inner, anchor=tk.NW)
        self.left_frame_inner.bind("<Configure>", lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        
        # 添加鼠标滚轮支持
        self.left_canvas.bind("<MouseWheel>", lambda event: self.on_mousewheel(event, "left"))
        self.left_canvas.bind("<Button-4>", lambda event: self.on_mousewheel_linux(event, "left", -1))
        self.left_canvas.bind("<Button-5>", lambda event: self.on_mousewheel_linux(event, "left", 1))
        
        # 右侧文件显示
        right_frame = ttk.LabelFrame(main_frame, text="文件夹2")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.right_canvas = tk.Canvas(right_frame)
        right_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.on_right_scroll)
        self.right_canvas.configure(yscrollcommand=right_scrollbar.set)
        
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame_inner = ttk.Frame(self.right_canvas)
        self.right_canvas.create_window((0, 0), window=self.right_frame_inner, anchor=tk.NW)
        self.right_frame_inner.bind("<Configure>", lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")))
        
        # 添加鼠标滚轮支持
        self.right_canvas.bind("<MouseWheel>", lambda event: self.on_mousewheel(event, "right"))
        self.right_canvas.bind("<Button-4>", lambda event: self.on_mousewheel_linux(event, "right", -1))
        self.right_canvas.bind("<Button-5>", lambda event: self.on_mousewheel_linux(event, "right", 1))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 保存缩略图引用，防止被垃圾回收
        self.thumbnails = []
        
        # 保存文件框架引用，用于多选
        self.file_frames = {"left": {}, "right": {}}
    
    def on_left_scroll(self, *args):
        # 左侧滚动时同步右侧
        self.left_canvas.yview(*args)
        self.right_canvas.yview(*args)
    
    def on_right_scroll(self, *args):
        # 右侧滚动时同步左侧
        self.right_canvas.yview(*args)
        self.left_canvas.yview(*args)
    
    def on_mousewheel(self, event, side):
        # 处理鼠标滚轮事件，同步滚动两侧
        delta = int(-1 * (event.delta / 120))
        self.left_canvas.yview_scroll(delta, "units")
        self.right_canvas.yview_scroll(delta, "units")
    
    def on_mousewheel_linux(self, event, side, direction):
        # 处理Linux上的鼠标滚轮事件，同步滚动两侧
        self.left_canvas.yview_scroll(direction, "units")
        self.right_canvas.yview_scroll(direction, "units")
    
    def browse_folder(self, folder_num):
        folder_path = filedialog.askdirectory(title=f"选择文件夹 {folder_num}")
        if folder_path:
            if folder_num == 1:
                self.folder1_path = folder_path
                self.folder1_entry.delete(0, tk.END)
                self.folder1_entry.insert(0, folder_path)
            else:
                self.folder2_path = folder_path
                self.folder2_entry.delete(0, tk.END)
                self.folder2_entry.insert(0, folder_path)
    
    def load_files(self):
        self.folder1_path = self.folder1_entry.get()
        self.folder2_path = self.folder2_entry.get()
        
        if not self.folder1_path or not self.folder2_path:
            messagebox.showerror("错误", "请选择两个文件夹")
            return
        
        if not os.path.exists(self.folder1_path) or not os.path.exists(self.folder2_path):
            messagebox.showerror("错误", "文件夹不存在")
            return
        
        # 清空现有显示
        for widget in self.left_frame_inner.winfo_children():
            widget.destroy()
        
        for widget in self.right_frame_inner.winfo_children():
            widget.destroy()
        
        self.thumbnails = []
        self.file_frames = {"left": {}, "right": {}}
        self.selected_files = {"left": set(), "right": set()}
        self.last_selected = {"left": None, "right": None}
        
        # 加载文件
        self.status_var.set("正在加载文件...")
        threading.Thread(target=self.load_files_thread).start()
    
    def load_files_thread(self):
        try:
            # 获取文件列表
            files1 = os.listdir(self.folder1_path)
            files2 = os.listdir(self.folder2_path)
            
            self.current_files["left"] = files1
            self.current_files["right"] = files2
            
            # 显示文件
            self.display_files(self.left_frame_inner, self.folder1_path, files1, "left")
            self.display_files(self.right_frame_inner, self.folder2_path, files2, "right")
            
            self.status_var.set(f"已加载 {len(files1)} 个文件 (左) 和 {len(files2)} 个文件 (右)")
        except Exception as e:
            self.status_var.set(f"加载文件时出错: {str(e)}")
    
    def display_files(self, parent_frame, folder_path, files, side):
        row = 0
        col = 0
        max_cols = 4  # 每行显示的最大文件数
        
        for file in files:
            file_path = os.path.join(folder_path, file)
            
            # 创建文件框架
            file_frame = ttk.Frame(parent_frame, padding=5)
            file_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 保存文件框架引用
            self.file_frames[side][file] = file_frame
            
            # 生成缩略图
            thumbnail = self.create_thumbnail(file_path)
            if thumbnail:
                img_label = ttk.Label(file_frame, image=thumbnail)
                img_label.pack(pady=2)
                self.thumbnails.append(thumbnail)  # 保存引用
                
                # 为图片标签添加点击事件
                img_label.bind("<Button-1>", lambda e, f=file, s=side: self.select_file(f, s))
            
            # 文件名标签
            name_label = ttk.Label(file_frame, text=file, wraplength=100)
            name_label.pack(pady=2)
            # 为文件名标签添加点击事件
            name_label.bind("<Button-1>", lambda e, f=file, s=side: self.select_file(f, s))
            
            # 删除按钮
            delete_btn = ttk.Button(
                file_frame, 
                text="删除", 
                command=lambda fp=file_path, f=file, s=side: self.delete_file(fp, f, s)
            )
            delete_btn.pack(pady=2)
            
            # 为文件框架添加点击事件，支持多选
            file_frame.bind("<Button-1>", lambda e, f=file, s=side: self.select_file(f, s))
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def select_file(self, file, side):
        # 处理文件选择
        if self.ctrl_pressed:
            # Ctrl+点击：切换选择状态
            if file in self.selected_files[side]:
                self.selected_files[side].remove(file)
                self.update_file_frame_style(file, side, False)
            else:
                self.selected_files[side].add(file)
                self.update_file_frame_style(file, side, True)
        elif self.shift_pressed and self.last_selected[side]:
            # Shift+点击：选择范围
            files_list = self.current_files[side]
            try:
                start_idx = files_list.index(self.last_selected[side])
                end_idx = files_list.index(file)
                if start_idx > end_idx:
                    start_idx, end_idx = end_idx, start_idx
                
                # 清除之前的选择
                for f in self.selected_files[side].copy():
                    self.selected_files[side].remove(f)
                    self.update_file_frame_style(f, side, False)
                
                # 选择范围内的文件
                for i in range(start_idx, end_idx + 1):
                    if i < len(files_list):
                        self.selected_files[side].add(files_list[i])
                        self.update_file_frame_style(files_list[i], side, True)
            except ValueError:
                # 文件不在列表中，忽略
                pass
        else:
            # 普通点击：清除之前的选择，只选择当前文件
            for f in self.selected_files[side].copy():
                self.selected_files[side].remove(f)
                self.update_file_frame_style(f, side, False)
            
            self.selected_files[side].add(file)
            self.update_file_frame_style(file, side, True)
        
        self.last_selected[side] = file
        self.status_var.set(f"已选择 {len(self.selected_files['left'])} 个文件 (左) 和 {len(self.selected_files['right'])} 个文件 (右)")
    
    def update_file_frame_style(self, file, side, selected):
        # 更新文件框架的样式以显示选中状态
        if file in self.file_frames[side]:
            frame = self.file_frames[side][file]
            
            # 使用更明显的视觉反馈
            if selected:
                # 使用自定义样式
                frame.configure(style="Selected.TFrame")
                
                # 为所有子组件设置背景色
                for child in frame.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.configure(background="#4a90e2")
                    elif isinstance(child, ttk.Button):
                        # 按钮不改变背景色
                        pass
                
                # 添加边框
                frame.configure(borderwidth=2, relief="raised")
            else:
                # 恢复默认样式
                frame.configure(style="", borderwidth=0, relief="flat")
                
                # 恢复子组件默认背景色
                for child in frame.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.configure(background="")
    
    def delete_selected_files(self):
        # 删除所有选中的文件
        left_files = list(self.selected_files["left"])
        right_files = list(self.selected_files["right"])
        
        # 合并两侧选中的文件
        all_files = set(left_files + right_files)
        
        for file in all_files:
            # 删除左侧文件
            if file in self.current_files["left"]:
                file_path = os.path.join(self.folder1_path, file)
                self.delete_file_internal(file_path)
            
            # 删除右侧文件
            if file in self.current_files["right"]:
                file_path = os.path.join(self.folder2_path, file)
                self.delete_file_internal(file_path)
        
        # 重新加载文件
        if all_files:
            self.load_files()
            self.status_var.set(f"已删除 {len(all_files)} 个文件")
    
    def delete_file_internal(self, file_path):
        # 内部删除文件方法
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            return True
        except Exception as e:
            self.status_var.set(f"删除文件时出错: {str(e)}")
            return False
    
    def create_thumbnail(self, file_path):
        try:
            if os.path.isdir(file_path):
                # 对于文件夹，使用文件夹图标
                img = Image.new('RGB', self.thumbnail_size, color='lightgray')
                thumbnail = ImageTk.PhotoImage(img)
                return thumbnail
            
            # 检查是否为图像文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            if any(file_path.lower().endswith(ext) for ext in image_extensions):
                img = Image.open(file_path)
                img.thumbnail(self.thumbnail_size)
                thumbnail = ImageTk.PhotoImage(img)
                return thumbnail
            else:
                # 对于非图像文件，创建一个简单的图标
                img = Image.new('RGB', self.thumbnail_size, color='lightblue')
                thumbnail = ImageTk.PhotoImage(img)
                return thumbnail
        except Exception as e:
            print(f"创建缩略图时出错: {str(e)}")
            # 创建默认缩略图
            img = Image.new('RGB', self.thumbnail_size, color='gray')
            thumbnail = ImageTk.PhotoImage(img)
            return thumbnail
    
    def delete_file(self, file_path, file_name, side):
        try:
            # 删除当前文件，不再显示确认对话框
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            
            # 删除另一侧的文件
            other_side = "right" if side == "left" else "left"
            other_folder = self.folder2_path if side == "left" else self.folder1_path
            other_file_path = os.path.join(other_folder, file_name)
            
            if os.path.exists(other_file_path):
                if os.path.isdir(other_file_path):
                    shutil.rmtree(other_file_path)
                else:
                    os.remove(other_file_path)
            
            # 重新加载文件
            self.load_files()
            self.status_var.set(f"已删除文件: {file_name}")
        except Exception as e:
            messagebox.showerror("删除错误", f"删除文件时出错: {str(e)}")
            self.status_var.set(f"删除文件时出错: {str(e)}")

if __name__ == "__main__":
    app = SyncFileViewer()
    app.mainloop()