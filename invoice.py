import sys
import os
import fitz  # PyMuPDF
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QCheckBox, QLineEdit, QFormLayout, QMessageBox, QProgressBar,
                             QGridLayout)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import base64
import json
import requests
from PyQt6.QtWidgets import QApplication, QMessageBox # 确保引入了这些用于更新UI和弹窗的组件

class InvoiceProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大模型发票智能处理系统")
        self.resize(1100, 750)
        
        self.target_files = []      # 存放待处理的文件列表 (支持 PDF 和 图片)
        self.current_index = 0      # 当前处理的索引
        self.results_data = []      # 暂存已确认的数据，最后统一写入Excel
        self.current_image_path = "temp_invoice.png" # 用于在UI上显示PDF截图
        
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 核心调整：最外层改为垂直布局
        root_layout = QVBoxLayout(main_widget)
        
        # 创建一个水平布局，用于包裹原本的左右两块核心内容
        content_layout = QHBoxLayout()
        
        # --- 左侧：图像显示 ---
        left_layout = QVBoxLayout()
        
        # 进度提示文本框
        self.progress_label = QLabel("共找到 0 张，当前处理第 0 张")
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.progress_label)

        self.image_label = QLabel("发票预览将显示在这里")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0;")
        left_layout.addWidget(self.image_label)
        
        # --- 右侧：控制与数据表单 ---
        right_layout = QVBoxLayout()
        
        # 1. 操作区
        self.btn_select_dir = QPushButton("选择发票文件夹")
        self.btn_select_dir.setMinimumHeight(40)
        self.btn_select_dir.clicked.connect(self.load_folder)
        right_layout.addWidget(self.btn_select_dir)
        
# ==================== 2 & 3. 合并后的字段选择与数据修改区 ====================
        self.fields_layout = QGridLayout()
        self.fields_layout.setVerticalSpacing(15) # 设置行间距让界面更舒展
        
        # 1. 购买方名称
        self.chk_buyer = QCheckBox()
        self.chk_buyer.setChecked(True)
        self.input_buyer = QLineEdit()
        self.fields_layout.addWidget(self.chk_buyer, 0, 0)
        self.fields_layout.addWidget(QLabel("购买方名称:"), 0, 1)
        self.fields_layout.addWidget(self.input_buyer, 0, 2)

        # 2. 购买方税号
        self.chk_tax_id = QCheckBox()
        self.chk_tax_id.setChecked(True)
        self.input_tax_id = QLineEdit()
        self.fields_layout.addWidget(self.chk_tax_id, 1, 0)
        self.fields_layout.addWidget(QLabel("购买方税号:"), 1, 1)
        self.fields_layout.addWidget(self.input_tax_id, 1, 2)

        # 3. 发票号码
        self.chk_invoice_id = QCheckBox()
        self.chk_invoice_id.setChecked(True)
        self.input_invoice_id = QLineEdit()
        self.fields_layout.addWidget(self.chk_invoice_id, 2, 0)
        self.fields_layout.addWidget(QLabel("发票号码:"), 2, 1)
        self.fields_layout.addWidget(self.input_invoice_id, 2, 2)

        # 4. 开票日期
        self.chk_date = QCheckBox()
        self.chk_date.setChecked(True)
        self.input_date = QLineEdit()
        self.fields_layout.addWidget(self.chk_date, 3, 0)
        self.fields_layout.addWidget(QLabel("开票日期:"), 3, 1)
        self.fields_layout.addWidget(self.input_date, 3, 2)

        # 5. 总金额
        self.chk_amount = QCheckBox()
        self.chk_amount.setChecked(True)
        self.input_amount = QLineEdit()
        self.fields_layout.addWidget(self.chk_amount, 4, 0)
        self.fields_layout.addWidget(QLabel("总金额:"), 4, 1)
        self.fields_layout.addWidget(self.input_amount, 4, 2)

        # 设置列宽比例，让输入框占据大部分空间
        self.fields_layout.setColumnStretch(0, 0) # 复选框列
        self.fields_layout.setColumnStretch(1, 0) # 标签列
        self.fields_layout.setColumnStretch(2, 1) # 输入框列延展

        right_layout.addLayout(self.fields_layout)
        # =========================================================================
        
        # 4. 底部控制按钮区 (水平布局)
        btn_layout = QHBoxLayout()

        self.btn_confirm = QPushButton("确认并处理下一张")
        self.btn_confirm.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_confirm.clicked.connect(self.save_and_next)
        self.btn_confirm.setEnabled(False)
        
        self.btn_skip = QPushButton("跳过本张发票")
        self.btn_skip.setStyleSheet("background-color: #FFC107; color: black; font-weight: bold; padding: 10px;")
        self.btn_skip.clicked.connect(self.skip_invoice)
        self.btn_skip.setEnabled(False)

        self.btn_end = QPushButton("结束并写入EXCEL")
        self.btn_end.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 10px;")
        self.btn_end.clicked.connect(self.end_processing)

        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_skip)

        right_layout.addLayout(btn_layout)
        right_layout.addWidget(self.btn_end)
        
        # 将左右两块加入包裹布局中
        content_layout.addLayout(left_layout, 5)  
        content_layout.addLayout(right_layout, 3)
        
        # 将核心内容区域加入最外层布局
        root_layout.addLayout(content_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20) # 限制高度，使其更像底部的状态栏
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #ccc; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #4CAF50; }")
        
        root_layout.addWidget(self.progress_bar)


    def update_progress_label(self):
        total = len(self.target_files)
        current = self.current_index + 1 if self.current_index < total else total
        self.progress_label.setText(f"共找到 {total} 张，当前处理第 {current} 张")

        if total > 0:
            self.progress_bar.setValue(min(self.current_index, total))

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含发票的文件夹")
        if folder_path:
            # 扩展支持 PDF 和常见图像格式
            valid_exts = ('.pdf', '.png', '.jpg', '.jpeg')
            self.target_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]
            self.current_index = 0
            self.results_data = [] # 清空历史数据
            
            if self.target_files:
                self.progress_bar.setRange(0, len(self.target_files))
                self.progress_bar.setValue(0)
                self.process_current_invoice()
            else:
                QMessageBox.warning(self, "提示", "未找到PDF或图像文件！")
                self.progress_label.setText("共找到 0 张，当前处理第 0 张")

    def process_current_invoice(self):
        self.update_progress_label()

        if self.current_index >= len(self.target_files):
            QMessageBox.information(self, "完成", "所有发票处理完毕，请点击“结束并写入EXCEL”。")
            self.image_label.setText("处理完成")
            self.btn_confirm.setEnabled(False)
            self.btn_skip.setEnabled(False)
            return

        file_path = self.target_files[self.current_index]
        
        # --- UI 预览显示逻辑 ---
        if file_path.lower().endswith('.pdf'):
            # 对于PDF，仅使用 fitz 截图用于 UI 显示
            doc = fitz.open(file_path)
            page = doc[0] # 取第一页
            pix = page.get_pixmap(dpi=150)
            pix.save(self.current_image_path)
            pixmap = QPixmap(self.current_image_path)
        else:
            # 对于图像文件，直接读取显示
            pixmap = QPixmap(file_path)

        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        #  将原生文件传递给大模型
        self.call_llm_api(file_path)
        
    def call_llm_api(self, file_path):
        self.btn_confirm.setEnabled(False)
        self.btn_skip.setEnabled(False)
        self.image_label.setText("正在调用大模型识别，请稍候...")
        QApplication.processEvents() # 强制刷新界面
        
        # 判断应当发送给大模型的究竟是哪个文件
        if file_path.lower().endswith('.pdf'):
            target_file_to_encode = self.current_image_path
            mime_type = "image/png"
            print("识别到PDF文件，正在读取其渲染图...")
        else:
            # 如果是图像文件，直接发送原文件
            target_file_to_encode = file_path
            mime_type = "image/png" if file_path.lower().endswith('.png') else "image/jpeg"
            print(f"识别到图像文件，正在读取原生文件: {file_path}")

        # 将目标文件转换为 Base64
        try:
            with open(target_file_to_encode, "rb") as file_data:
                base64_file = base64.b64encode(file_data.read()).decode('utf-8')
        except Exception as e:
            QMessageBox.critical(self, "文件错误", f"无法读取文件进行编码：{e}")
            self.btn_skip.setEnabled(True)
            return

        # 2. 根据界面上勾选的复选框动态生成请求
        fields_to_extract = []
        if self.chk_buyer.isChecked(): fields_to_extract.append("购买方")
        if self.chk_tax_id.isChecked(): fields_to_extract.append("税号")
        if self.chk_invoice_id.isChecked(): fields_to_extract.append("发票号码")
        if self.chk_date.isChecked(): fields_to_extract.append("开票日期")
        if self.chk_amount.isChecked(): fields_to_extract.append("总金额")

        fields_str = "、".join(fields_to_extract)
        
        prompt = f"""
        你是一个专业的财务发票数据提取助手。
        请从提供的文件中提取以下字段信息：{fields_str}。
        
        要求：
        1. 严格以 JSON 格式输出，不要包含任何额外的问候语、解释性文本或 Markdown 代码块标记（如 ```json ）。
        2. JSON 的键名必须严格使用上述要求提取的字段名称。
        3. 如果某个字段在发票中完全找不到，请将该字段的值设置为 "未找到"。
        """

        url = "https://models.sjtu.edu.cn/api/v1/chat/completions" 
        # url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer XXXXX"  # API KEY
            # "Authorization": "Bearer "  # API KEY
        }
        
        data = {
            "model": "qwen3vl", 
            # "model": "qwen-vl-ocr-latest",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url", 
                            "image_url": {
                                # 传入原生文件的 Base64 及其正确格式
                                "url": f"data:{mime_type};base64,{base64_file}" 
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt 
                        }
                    ]
                }
            ],
            "stream": False,
            "temperature": 0.1 
        }

        # 5. 发送请求并解析结果
        try:
            print("正在等待大模型返回结果...")
            response = requests.post(url, headers=headers, json=data) # [cite: 11]
            response.raise_for_status()  # 如果遇到 4xx 或 5xx 错误会抛出异常
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip() # 获取大模型回复的具体文本 [cite: 3, 11]
            
            # 容错处理：清理大模型偶尔不听话带上的 Markdown 标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            print(f"大模型原始返回: \n{content}")
            
            # 解析为 Python 字典
            parsed_data = json.loads(content)
            
            # 6. 将提取到的数据填充回图形界面的输入框中
            self.input_buyer.setText(parsed_data.get("购买方", "未找到"))
            self.input_tax_id.setText(parsed_data.get("税号", "未找到"))
            self.input_invoice_id.setText(parsed_data.get("发票号码", "未找到"))
            self.input_date.setText(parsed_data.get("开票日期", "未找到"))
            self.input_amount.setText(parsed_data.get("总金额", "未找到"))
            
            # 恢复界面状态
            self.btn_confirm.setEnabled(True)
            # QMessageBox.information(self, "成功", "识别完成，请核对数据！")

        except json.JSONDecodeError:
            QMessageBox.warning(self, "解析失败", "大模型未返回标准的JSON格式数据，请重试。\n返回内容：\n" + content)
            self.btn_confirm.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "API调用错误", f"请求失败（请确保已连接校内网络并填对API Key ）：\n{str(e)}")
            self.btn_confirm.setEnabled(True)

    def save_and_next(self):
        # 1. 获取界面上（可能被用户修改过）的最终数据
        data = {
            "购买方": self.input_buyer.text(),
            "税号": self.input_tax_id.text(),
            "发票号码": self.input_invoice_id.text(),
            "开票日期": self.input_date.text(),
            "总金额": self.input_amount.text()
        }
        
        # 2. 追加到 Excel
        df = pd.DataFrame([data])
        excel_path = "发票汇总.xlsx"
        if not os.path.exists(excel_path):
            df.to_excel(excel_path, index=False)
        else:
            with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
        
        # 3. 处理下一张
        self.current_index += 1
        self.process_current_invoice()

    def skip_invoice(self):
        # 放弃当前数据，清空输入框，直接处理下一张
        self.clear_inputs()
        self.current_index += 1
        self.process_current_invoice()

    def end_processing(self):
        # 将积累的所有结果一次性写入Excel并退出
        if not self.results_data:
            QMessageBox.information(self, "退出", "没有保存任何发票数据，程序退出。")
            self.close()
            return
            
        df = pd.DataFrame(self.results_data)
        excel_path = "发票汇总.xlsx"
        
        try:
            if not os.path.exists(excel_path):
                df.to_excel(excel_path, index=False)
            else:
                with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
            
            QMessageBox.information(self, "保存成功", f"共处理并保存了 {len(self.results_data)} 条数据至 {excel_path}！")
            self.close() # 退出程序
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"写入 Excel 时出错，请确认文件是否被占用：\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InvoiceProcessorApp()
    ex.show()
    sys.exit(app.exec())