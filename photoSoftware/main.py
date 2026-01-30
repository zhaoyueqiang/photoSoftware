#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片处理软件 - 桌面应用
联系人匹配和照片打包功能
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from backend import ContactMatcher


class ProcessThread(QThread):
    """处理线程，避免界面卡顿"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, folder_path, vcf_path, output_path):
        super().__init__()
        self.folder_path = folder_path
        self.vcf_path = vcf_path
        self.output_path = output_path
    
    def run(self):
        try:
            matcher = ContactMatcher()
            result = matcher.process(self.folder_path, self.vcf_path, self.output_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.folder_path = ''
        self.vcf_path = ''
        self.output_path = ''
        self.process_thread = None
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('照片处理软件 - 联系人匹配')
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel('联系人匹配和照片打包工具')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 文件夹路径选择
        folder_group = QWidget()
        folder_layout = QVBoxLayout(folder_group)
        
        folder_label = QLabel('1. 选择包含子文件夹的基础文件夹（源文件夹）：')
        folder_label.setStyleSheet("font-weight: bold;")
        folder_layout.addWidget(folder_label)
        
        folder_input_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText('请选择源文件夹路径...')
        self.folder_input.setReadOnly(True)
        folder_input_layout.addWidget(self.folder_input)
        
        self.folder_btn = QPushButton('选择文件夹')
        self.folder_btn.clicked.connect(self.select_folder)
        folder_input_layout.addWidget(self.folder_btn)
        folder_layout.addLayout(folder_input_layout)
        
        main_layout.addWidget(folder_group)
        
        # VCF文件选择
        vcf_group = QWidget()
        vcf_layout = QVBoxLayout(vcf_group)
        
        vcf_label = QLabel('2. 选择VCF联系人文件：')
        vcf_label.setStyleSheet("font-weight: bold;")
        vcf_layout.addWidget(vcf_label)
        
        vcf_input_layout = QHBoxLayout()
        self.vcf_input = QLineEdit()
        self.vcf_input.setPlaceholderText('请选择VCF文件...')
        self.vcf_input.setReadOnly(True)
        vcf_input_layout.addWidget(self.vcf_input)
        
        self.vcf_btn = QPushButton('选择VCF文件')
        self.vcf_btn.clicked.connect(self.select_vcf)
        vcf_input_layout.addWidget(self.vcf_btn)
        vcf_layout.addLayout(vcf_input_layout)
        
        main_layout.addWidget(vcf_group)
        
        # 输出目录选择
        output_group = QWidget()
        output_layout = QVBoxLayout(output_group)
        
        output_label = QLabel('3. 选择输出目录（保存处理结果）：')
        output_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(output_label)
        
        output_input_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText('请选择输出目录...')
        self.output_input.setReadOnly(True)
        output_input_layout.addWidget(self.output_input)
        
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output)
        output_input_layout.addWidget(self.output_btn)
        output_layout.addLayout(output_input_layout)
        
        main_layout.addWidget(output_group)
        
        # 处理按钮
        self.process_btn = QPushButton('开始处理')
        self.process_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        main_layout.addWidget(self.process_btn)
        
        # 结果显示区域
        result_label = QLabel('处理结果：')
        result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText('处理结果将显示在这里...')
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        main_layout.addWidget(self.result_text)
        
        # 状态栏
        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # 更新按钮状态
        self.update_button_state()
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            '选择包含子文件夹的基础文件夹',
            ''
        )
        if folder:
            self.folder_path = folder
            self.folder_input.setText(folder)
            self.update_button_state()
    
    def select_vcf(self):
        """选择VCF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择VCF联系人文件',
            '',
            'VCF文件 (*.vcf);;所有文件 (*.*)'
        )
        if file_path:
            self.vcf_path = file_path
            self.vcf_input.setText(file_path)
            self.update_button_state()
    
    def select_output(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(
            self,
            '选择输出目录',
            ''
        )
        if folder:
            self.output_path = folder
            self.output_input.setText(folder)
            self.update_button_state()
    
    def update_button_state(self):
        """更新按钮状态"""
        self.process_btn.setEnabled(
            bool(self.folder_path) and bool(self.vcf_path) and bool(self.output_path)
        )
    
    def start_processing(self):
        """开始处理"""
        if not self.folder_path or not self.vcf_path or not self.output_path:
            QMessageBox.warning(self, '错误', '请先选择源文件夹、VCF文件和输出目录')
            return
        
        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.vcf_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.status_label.setText('处理中，请稍候...')
        self.result_text.clear()
        
        # 创建处理线程
        self.process_thread = ProcessThread(self.folder_path, self.vcf_path, self.output_path)
        self.process_thread.finished.connect(self.on_processing_finished)
        self.process_thread.error.connect(self.on_processing_error)
        self.process_thread.start()
    
    def on_processing_finished(self, result):
        """处理完成"""
        # 恢复按钮
        self.process_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.vcf_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.status_label.setText('处理完成')
        
        # 显示结果
        output = []
        output.append("=" * 50)
        output.append("处理结果")
        output.append("=" * 50)
        output.append(f"\n匹配成功: {result['matched_count']} 个联系人")
        output.append(f"总联系人: {result['total_contacts']} 个")
        output.append(f"总文件夹: {result['total_folders']} 个")
        output.append(f"输出目录: {result['output_path']}")
        
        if result['matched_contacts']:
            output.append("\n匹配详情：")
            output.append("-" * 50)
            for i, match in enumerate(result['matched_contacts'], 1):
                folder_name = os.path.basename(match['folder'])
                contact_name = match['contact']['name']
                contact_org = match['contact'].get('org', '无')
                output.append(f"{i}. 文件夹: {folder_name}")
                output.append(f"   联系人: {contact_name}")
                output.append(f"   单位: {contact_org}")
                output.append("")
        
        if result['unmatched_folders']:
            output.append(f"\n未匹配的文件夹 ({len(result['unmatched_folders'])} 个):")
            output.append("-" * 50)
            for folder in result['unmatched_folders']:
                output.append(f"  - {os.path.basename(folder)}")
        
        if result['unmatched_contacts']:
            output.append(f"\n未匹配的联系人 ({len(result['unmatched_contacts'])} 个):")
            output.append("-" * 50)
            for contact in result['unmatched_contacts']:
                output.append(f"  - {contact['name']} ({contact.get('org', '无单位')})")
        
        output.append("\n" + "=" * 50)
        output.append("输出目录结构说明：")
        output.append("输出目录/")
        output.append("├── 联系人名称/")
        output.append("│   ├── 联系人名称.txt  (联系人信息)")
        output.append("│   └── photo/  (照片文件夹)")
        output.append("│       └── 图片文件...")
        output.append("=" * 50)
        
        self.result_text.setText('\n'.join(output))
        
        # 显示成功消息
        QMessageBox.information(
            self,
            '处理完成',
            f'处理完成！\n\n匹配成功: {result["matched_count"]} 个联系人\n\n'
            f'结果已保存到:\n{result["output_path"]}'
        )
    
    def on_processing_error(self, error_msg):
        """处理错误"""
        # 恢复按钮
        self.process_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.vcf_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.status_label.setText('处理失败')
        
        # 显示错误
        self.result_text.setText(f'错误: {error_msg}')
        QMessageBox.critical(self, '处理失败', f'处理过程中发生错误：\n\n{error_msg}')


def main():
    """主函数"""
    # 设置应用程序属性（Mac 专用）
    if sys.platform == 'darwin':
        os.environ.setdefault('QT_MAC_WANTS_LAYER', '1')
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName('照片处理软件')
    app.setOrganizationName('PhotoSoftware')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
