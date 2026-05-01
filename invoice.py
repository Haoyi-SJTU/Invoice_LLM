import sys
import os
import fitz  # PyMuPDF
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QCheckBox, QLineEdit, QFormLayout, QMessageBox)
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
        self.resize(1000, 700)
        
        self.pdf_files = []
        self.current_index = 0
        self.current_image_path = "temp_invoice.png"
        
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # --- 左侧：图像显示 ---
        left_layout = QVBoxLayout()
        self.image_label = QLabel("发票截图将显示在这里")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black;")
        left_layout.addWidget(self.image_label)
        
        # --- 右侧：控制与数据表单 ---
        right_layout = QVBoxLayout()
        
        # 1. 操作区
        self.btn_select_dir = QPushButton("选择发票文件夹")
        self.btn_select_dir.clicked.connect(self.load_folder)
        right_layout.addWidget(self.btn_select_dir)
        
        # 2. 字段选择区
        self.chk_buyer = QCheckBox("购买方名称")
        self.chk_tax_id = QCheckBox("购买方税号")
        self.chk_amount = QCheckBox("总金额")
        self.chk_invoice_id = QCheckBox("发票号码")
        self.chk_date = QCheckBox("开票日期")

        # self.chk_buyer.setChecked(True)
        # self.chk_tax_id.setChecked(True)
        self.chk_amount.setChecked(True)
        self.chk_invoice_id.setChecked(True)
        self.chk_date.setChecked(True)
 
        right_layout.addWidget(self.chk_buyer)
        right_layout.addWidget(self.chk_tax_id)
        right_layout.addWidget(self.chk_invoice_id)
        right_layout.addWidget(self.chk_date)
        right_layout.addWidget(self.chk_amount)
        
        # 3. 数据校验与修改区 (表单)
        self.form_layout = QFormLayout()

        self.input_buyer = QLineEdit()
        self.form_layout.addRow("购买方:", self.input_buyer)
        self.input_tax_id = QLineEdit()
        self.form_layout.addRow("税号:", self.input_tax_id)
        self.input_invoice_id = QLineEdit()
        self.form_layout.addRow("发票号码:", self.input_invoice_id)
        self.input_date = QLineEdit()
        self.form_layout.addRow("开票日期:", self.input_date)
        self.input_amount = QLineEdit()
        self.form_layout.addRow("总金额:", self.input_amount)

        right_layout.addLayout(self.form_layout)
        
        # 4. 确认按钮
        self.btn_confirm = QPushButton("确认并处理下一张")
        self.btn_confirm.clicked.connect(self.save_and_next)
        self.btn_confirm.setEnabled(False)
        right_layout.addWidget(self.btn_confirm)
        
        main_layout.addLayout(left_layout, 2)  # 左侧占宽比例大一些
        main_layout.addLayout(right_layout, 1)

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含PDF的文件夹")
        if folder_path:
            self.pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            self.current_index = 0
            if self.pdf_files:
                self.process_current_invoice()
            else:
                QMessageBox.warning(self, "提示", "未找到PDF文件！")

    def process_current_invoice(self):
        if self.current_index >= len(self.pdf_files):
            QMessageBox.information(self, "完成", "所有发票处理完毕！")
            self.image_label.setText("处理完成")
            self.btn_confirm.setEnabled(False)
            return

        pdf_path = self.pdf_files[self.current_index]
        
        # 1. PDF 转图像
        doc = fitz.open(pdf_path)
        page = doc[0] # 取第一页
        pix = page.get_pixmap(dpi=150)
        pix.save(self.current_image_path)
        
        # 在 UI 中显示
        pixmap = QPixmap(self.current_image_path)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        
        # 2. 调用大模型 API
        self.call_llm_api(self.current_image_path)
        
        self.btn_confirm.setEnabled(True)

    def call_llm_api(self, image_path):
        # 1. 刷新 UI 状态，提示用户正在处理
        self.btn_confirm.setEnabled(False)
        self.image_label.setText("正在调用校内大模型识别，请稍候...")
        QApplication.processEvents() # 强制刷新界面，避免主线程假死
        
        print(f"正在读取并编码图像: {image_path}")
        
        # 2. 将本地图像转换为 Base64 编码
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            QMessageBox.critical(self, "文件错误", f"无法读取发票截图：{e}")
            return

        # 3. 根据界面上勾选的复选框，动态生成要提取的字段列表
        fields_to_extract = []
        if self.chk_buyer.isChecked(): fields_to_extract.append("购买方名称")
        if self.chk_tax_id.isChecked(): fields_to_extract.append("购买方税号")
        if self.chk_invoice_id.isChecked(): fields_to_extract.append("发票号码")
        if self.chk_date.isChecked(): fields_to_extract.append("开票日期")
        if self.chk_amount.isChecked(): fields_to_extract.append("总金额")

        fields_str = "、".join(fields_to_extract)
        
        # 构造强指令 Prompt，约束大模型必须返回标准 JSON
        prompt = f"""
        你是一个专业的财务发票数据提取助手。
        请从提供的发票图像中提取以下字段信息：{fields_str}。
        
        要求：
        1. 严格以 JSON 格式输出，不要包含任何额外的问候语、解释性文本或 Markdown 代码块标记（如 ```json ）。
        2. JSON 的键名必须严格使用上述要求提取的字段名称。
        3. 如果某个字段在发票中完全找不到，请将该字段的值设置为 "未找到"。
        """

        # 4. 构造交大 API 请求负载 
        url = "https://models.sjtu.edu.cn/api/v1/chat/completions" # 
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer XXXXXX"  
        }
        
        data = {
            "model": "qwen3vl", # 使用支持图像分析的视觉模型 
            "messages": [
                {
                    "role": "user", # 
                    "content": [
                        {
                            "type": "image_url", # 
                            "image_url": {
                                # 使用标准 data URI 协议直接传递本地图片的 base64 数据
                                "url": f"data:image/jpeg;base64,{base64_image}" 
                            }
                        },
                        {
                            "type": "text", # [cite: 2]
                            "text": prompt # [cite: 2]
                        }
                    ]
                }
            ],
            "stream": False, # [cite: 3, 10]
            "temperature": 0.1 # 极低的温度值可以大幅提高 JSON 格式输出的稳定性和信息提取的准确性
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
            self.input_buyer.setText(parsed_data.get("购买方名称", "未找到"))
            self.input_tax_id.setText(parsed_data.get("购买方税号", "未找到"))
            
            # 恢复界面状态
            self.btn_confirm.setEnabled(True)
            QMessageBox.information(self, "成功", "识别完成，请核对数据！")

        except json.JSONDecodeError:
            QMessageBox.warning(self, "解析失败", "大模型未返回标准的JSON格式数据，请重试。\n返回内容：\n" + content)
            self.btn_confirm.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "API调用错误", f"请求失败（请确保已连接校内网络并填对API Key ）：\n{str(e)}")
            self.btn_confirm.setEnabled(True)

    def save_and_next(self):
        # 1. 获取界面上（可能被用户修改过）的最终数据
        data = {
            "文件路径": self.pdf_files[self.current_index],
            "购买方": self.input_buyer.text(),
            "税号": self.input_tax_id.text()
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InvoiceProcessorApp()
    ex.show()
    sys.exit(app.exec())