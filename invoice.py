import sys
import os
import fitz
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
from PyQt6.QtWidgets import QApplication, QMessageBox
import json


class InvoiceProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("发票智能处理系统")
        self.setFixedSize(1000, 500)
        
        self.target_files = []      # 待处理的文件列表
        self.current_index = 0      # 当前处理的索引
        self.results_data = []      # 已确认的数据
        self.current_image_path = "temp_invoice.png" # UI显示
        
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        root_layout = QVBoxLayout(main_widget)

        content_layout = QHBoxLayout()
        
        # 图像显示
        left_layout = QVBoxLayout()
        
        self.image_label = QLabel("发票预览将显示在这里")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0;")
        left_layout.addWidget(self.image_label)
        
        # 控制与数据表单
        right_layout = QVBoxLayout()
        
        # 1. 操作区
        self.btn_select_dir = QPushButton("选择发票文件夹")
        self.btn_select_dir.setMinimumHeight(40)
        self.btn_select_dir.clicked.connect(self.load_folder)
        right_layout.addWidget(self.btn_select_dir)
        
        #  2. 字段选择与数据修改区
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

        # 4. 项目名称
        self.chk_project = QCheckBox()
        self.chk_project.setChecked(True)
        self.input_project = QLineEdit()
        self.fields_layout.addWidget(self.chk_project, 4, 0)
        self.fields_layout.addWidget(QLabel("项目名称:"), 4, 1)
        self.fields_layout.addWidget(self.input_project, 4, 2)

        # 5. 总金额
        self.chk_amount = QCheckBox()
        self.chk_amount.setChecked(True)
        self.input_amount = QLineEdit()
        self.fields_layout.addWidget(self.chk_amount, 5, 0)
        self.fields_layout.addWidget(QLabel("总金额:"), 5, 1)
        self.fields_layout.addWidget(self.input_amount, 5, 2)

        # 列宽比例
        self.fields_layout.setColumnStretch(0, 0) # 复选框列
        self.fields_layout.setColumnStretch(1, 0) # 标签列
        self.fields_layout.setColumnStretch(2, 1) # 输入框列延展

        right_layout.addLayout(self.fields_layout)
       
        # 4. 底部控制按钮区
        btn_layout = QHBoxLayout()

        self.btn_confirm = QPushButton("确认并处理下一张")
        self.btn_confirm.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_confirm.clicked.connect(self.save_and_next)
        self.btn_confirm.setEnabled(False)
        
        self.btn_skip = QPushButton("跳过本张发票")
        self.btn_skip.setStyleSheet("background-color: #FFC107; color: black; font-weight: bold; padding: 10px;")
        self.btn_skip.clicked.connect(self.skip_invoice)
        self.btn_skip.setEnabled(False)

        self.btn_end = QPushButton("结束")
        self.btn_end.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 10px;")
        self.btn_end.clicked.connect(self.end_processing)

        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_skip)

        right_layout.addLayout(btn_layout)
        right_layout.addWidget(self.btn_end)
        

        content_layout.addLayout(left_layout, 5)  
        content_layout.addLayout(right_layout, 3)
        
        root_layout.addLayout(content_layout)
        
        self.progress_label = QLabel("共找到 0 张，当前处理第 0 张")
        line_height = self.progress_label.fontMetrics().height()
        self.progress_label.setFixedHeight(int(line_height * 1.5)) # 限制高度
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.progress_label) 

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20) 
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #ccc; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #4CAF50; }")
        root_layout.addWidget(self.progress_bar)


        self.name_label = QLabel("作者：https://github.com/Haoyi-SJTU")
        line_height = self.name_label.fontMetrics().height()
        self.name_label.setFixedHeight(int(line_height * 1.5)) 
        self.name_label.setStyleSheet("font-size: 10px; color: #333;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self.name_label) 
        
        self.load_api()
        
    def load_api(self):
        key_path = "key.txt"
        if not os.path.exists(key_path):
            QMessageBox.critical(self, "缺少API Key", "请在软件同级目录下创建一个 key.txt 文件，并将您的 API Key 粘贴进去！")
            self.btn_skip.setEnabled(True)
            return
            
        with open(key_path, "r", encoding="utf-8") as f:
            self.api_key = f.read().strip()
            
        if not self.api_key:
            QMessageBox.critical(self, "API Key无效", "key.txt 文件为空，请填入有效的 API Key！")
            self.btn_skip.setEnabled(True)
            return

    def load_api(self):
        key_path = "key.json"
        if not os.path.exists(key_path):
            QMessageBox.critical(self, "缺少配置文件", "请在软件同级目录下创建一个 key.json 文件，并配置大模型的 key 和 link！")
            self.btn_skip.setEnabled(True)
            return
            
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                
            # 使用 get 方法安全获取字典内容，防止抛出 KeyError
            self.api_key = config_data.get("key", "").strip()
            self.base_url = config_data.get("link", "").strip()
            
            if not self.api_key or not self.base_url:
                QMessageBox.critical(self, "配置无效", "key.json 文件中缺少 'key' 或 'link' 字段，或者字段内容为空！")
                self.btn_skip.setEnabled(True)
                return
                
        except json.JSONDecodeError:
            QMessageBox.critical(self, "格式错误", "key.json 文件格式不正确，请确保它符合标准的 JSON 格式要求（如使用双引号）。")
            self.btn_skip.setEnabled(True)
            return
        except Exception as e:
            QMessageBox.critical(self, "读取错误", f"读取配置文件时发生未知错误：\n{str(e)}")
            self.btn_skip.setEnabled(True)
            return

    def update_progress_label(self):
        total = len(self.target_files)
        current = self.current_index + 1 if self.current_index < total else total
        self.progress_label.setText(f"共找到 {total} 张，当前处理第 {current} 张")

        if total > 0:
            self.progress_bar.setValue(min(self.current_index, total))

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含发票的文件夹")

        if folder_path:
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

        self.btn_confirm.setEnabled(False)
        self.btn_skip.setEnabled(False)

        self.update_progress_label()

        if self.current_index >= len(self.target_files):
            QMessageBox.information(self, "完成", "所有发票处理完毕，请点击“结束并写入EXCEL”。")
            self.setWindowTitle("发票智能处理系统 - 完成")
            self.btn_confirm.setEnabled(False)
            self.btn_skip.setEnabled(False)
            return

        file_path = self.target_files[self.current_index]
        
        # UI 
        if file_path.lower().endswith('.pdf'):
            doc = fitz.open(file_path)
            page = doc[0] # 取第一页
            pix = page.get_pixmap(dpi=150)
            pix.save(self.current_image_path)
            pixmap = QPixmap(self.current_image_path)
        else:
            pixmap = QPixmap(file_path)

        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.call_llm_api(file_path)




    def call_llm_api(self, file_path):

        self.btn_confirm.setEnabled(False)
        self.btn_skip.setEnabled(False)
        self.setWindowTitle("发票智能处理系统 - 正在处理，请稍候")
        QApplication.processEvents() # 刷新界面
        
        if file_path.lower().endswith('.pdf'):
            target_file_to_encode = self.current_image_path
            mime_type = "image/png"
            print("识别到PDF文件，正在读取其渲染图...")
        else:
            target_file_to_encode = file_path
            mime_type = "image/png" if file_path.lower().endswith('.png') else "image/jpeg"
            print(f"识别到图像文件，正在读取原生文件: {file_path}")

        # 转Base64
        try:
            with open(target_file_to_encode, "rb") as file_data:
                base64_file = base64.b64encode(file_data.read()).decode('utf-8')
        except Exception as e:
            QMessageBox.critical(self, "文件错误", f"无法读取文件进行编码：{e}")
            self.btn_skip.setEnabled(True)
            return

        # 构造请求字段
        fields_to_extract = []
        if self.chk_buyer.isChecked(): fields_to_extract.append("购买方")
        if self.chk_tax_id.isChecked(): fields_to_extract.append("税号")
        if self.chk_project.isChecked(): fields_to_extract.append("项目名称") 
        if self.chk_invoice_id.isChecked(): fields_to_extract.append("发票号码")
        if self.chk_date.isChecked(): fields_to_extract.append("开票日期")
        if self.chk_amount.isChecked(): fields_to_extract.append("总金额")

        fields_str = "、".join(fields_to_extract)
        
        prompt = f"""
        你是一个专业的财务发票数据提取助手。
        请从提供的文件中提取以下字段信息：{fields_str}。
        
        严格要求：
        1. 严格以 JSON 格式输出，不要包含任何额外的问候语或 Markdown 标记（如 ```json ）。
        2. JSON 的键名必须完全使用上述提取的字段名称。如果未找到请填"未找到"。
        3. 若要求提取“项目名称”，只提取发票上项目明细的【第一行】即可，舍弃多余的行数。
        4. 若要求提取“总金额”，必须去读取发票上的【价税合计（大写）】，并将其转换为【阿拉伯数字】输出（如将"壹佰圆整"输出为"100.00"）。
        """
        
        url = self.base_url
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"  
        }
        
        data = {
            "model": "qwen-vl-ocr-latest", 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_file}"}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "stream": False,
            "temperature": 0.1 
        }

        try:
            response = requests.post(url, headers=headers, json=data) 
            response.raise_for_status() 
            result = response.json()
            content = result['choices'][0]['message']['content'].strip() 
            
            content = content.replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(content)

            mapping = {
                "buyer": "购买方",
                "tax_id": "税号",
                "project": "项目名称", 
                "invoice_id": "发票号码",
                "date": "开票日期",
                "amount": "总金额"
            }            
            
            for attr, json_key in mapping.items():
                checkbox = getattr(self, f"chk_{attr}")
                input_box = getattr(self, f"input_{attr}")
                if checkbox.isChecked():
                    input_box.setText(str(parsed_data.get(json_key, "未找到")))
                else:
                    input_box.clear()

            self.btn_confirm.setEnabled(True)
            self.btn_skip.setEnabled(True)        
            self.setWindowTitle("发票智能处理系统")

        except json.JSONDecodeError:
            QMessageBox.warning(self, "解析失败", "大模型未返回标准的JSON格式数据，请重试。\n返回内容：\n" + content)
            self.btn_confirm.setEnabled(True)
            self.btn_skip.setEnabled(True) 
            self.setWindowTitle("发票智能处理系统")
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err_json = e.response.json()
                    if 'error' in err_json and 'message' in err_json['error']:
                        err_msg += f"\n详细原因: {err_json['error']['message']}"
                except:
                    err_msg += f"\n详细原因: {e.response.text}"
            
            QMessageBox.critical(self, "API调用错误", f"请求失败：\n{err_msg}")
            self.btn_confirm.setEnabled(True)
            self.btn_skip.setEnabled(True) 
            self.setWindowTitle("发票智能处理系统")


    def save_and_next(self):

        self.btn_confirm.setEnabled(False)
        self.btn_skip.setEnabled(False)

        # 1. 获取界面上（可能被用户修改过）的最终数据
        data = {
            "购买方": self.input_buyer.text(),
            "税号": self.input_tax_id.text(),
            "发票号码": self.input_invoice_id.text(),
            "开票日期": self.input_date.text(),
            "项目名称": self.input_project.text(),
            "总金额": self.input_amount.text()
        }
        
        # 2. 追加写入 Excel
        excel_path = "发票汇总.xlsx"
        df = pd.DataFrame([data])
        try:
            if not os.path.exists(excel_path):
                df.to_excel(excel_path, index=False)
            else:
                with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    start_row = writer.book['Sheet1'].max_row
                    df.to_excel(writer, index=False, header=False, startrow=start_row)
            print(f"数据已写入")
        except Exception as e:
            QMessageBox.critical(self, "写入错误", f"无法写入Excel文件，请检查是否被其他程序占用：\n{e}")
            self.btn_confirm.setEnabled(True)
            self.btn_skip.setEnabled(True)
            return

        # 3. 清空输入框并进入下一张
        self.clear_inputs()
        self.current_index += 1
        self.process_current_invoice()

    def clear_inputs(self):
        self.input_buyer.clear()
        self.input_tax_id.clear()
        self.input_invoice_id.clear()
        self.input_date.clear()
        self.input_amount.clear()

    def skip_invoice(self):
        self.clear_inputs()
        self.current_index += 1
        self.process_current_invoice()

    def end_processing(self):
        msg = f"处理已结束。所有点击过“确认”的数据已实时写入表格文件。"
        QMessageBox.information(self, "退出程序", msg)
        
        if os.path.exists(self.current_image_path):
            try:
                os.remove(self.current_image_path)
            except:
                pass
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InvoiceProcessorApp()
    ex.show()
    sys.exit(app.exec())