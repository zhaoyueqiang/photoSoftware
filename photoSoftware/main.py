#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片处理软件 - 桌面应用
联系人匹配和HTML相册生成功能
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from backend import ContactMatcher


class ProcessThread(QThread):
    """处理线程，避免界面卡顿"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, photos_folder, vcf_path, output_path):
        super().__init__()
        self.photos_folder = photos_folder
        self.vcf_path = vcf_path
        self.output_path = output_path
    
    def run(self):
        try:
            matcher = ContactMatcher()
            result = matcher.process(self.photos_folder, self.vcf_path, self.output_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.photos_folder = ''
        self.vcf_path = ''
        self.output_path = ''
        self.process_thread = None
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('照片处理软件 - 联系人匹配和HTML相册生成')
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel('联系人照片匹配和HTML相册生成工具')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 照片文件夹选择
        photos_group = QWidget()
        photos_layout = QVBoxLayout(photos_group)
        
        photos_label = QLabel('1. 选择包含照片的文件夹（支持人脸识别标记的照片）：')
        photos_label.setStyleSheet("font-weight: bold;")
        photos_layout.addWidget(photos_label)
        
        photos_input_layout = QHBoxLayout()
        self.photos_input = QLineEdit()
        self.photos_input.setPlaceholderText('请选择照片文件夹路径...')
        self.photos_input.setReadOnly(True)
        photos_input_layout.addWidget(self.photos_input)
        
        self.photos_btn = QPushButton('选择照片文件夹')
        self.photos_btn.clicked.connect(self.select_photos_folder)
        photos_input_layout.addWidget(self.photos_btn)
        photos_layout.addLayout(photos_input_layout)
        
        main_layout.addWidget(photos_group)
        
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
        
        # 输出HTML文件选择
        output_group = QWidget()
        output_layout = QVBoxLayout(output_group)
        
        output_label = QLabel('3. 选择输出HTML文件路径：')
        output_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(output_label)
        
        output_input_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText('请选择输出HTML文件路径...')
        self.output_input.setReadOnly(True)
        output_input_layout.addWidget(self.output_input)
        
        self.output_btn = QPushButton('选择输出文件')
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
    
    def select_photos_folder(self):
        """选择照片文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            '选择包含照片的文件夹',
            ''
        )
        if folder:
            self.photos_folder = folder
            self.photos_input.setText(folder)
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
        """选择输出HTML文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '选择输出HTML文件',
            '',
            'HTML文件 (*.html);;所有文件 (*.*)'
        )
        if file_path:
            # 确保文件扩展名是.html
            if not file_path.endswith('.html'):
                file_path += '.html'
            self.output_path = file_path
            self.output_input.setText(file_path)
            self.update_button_state()
    
    def update_button_state(self):
        """更新按钮状态"""
        self.process_btn.setEnabled(
            bool(self.photos_folder) and bool(self.vcf_path) and bool(self.output_path)
        )
    
    def start_processing(self):
        """开始处理"""
        if not self.photos_folder or not self.vcf_path or not self.output_path:
            QMessageBox.warning(self, '错误', '请先选择照片文件夹、VCF文件和输出HTML文件')
            return
        
        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.photos_btn.setEnabled(False)
        self.vcf_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.status_label.setText('处理中，请稍候...')
        self.result_text.clear()
        
        # 创建处理线程
        self.process_thread = ProcessThread(self.photos_folder, self.vcf_path, self.output_path)
        self.process_thread.finished.connect(self.on_processing_finished)
        self.process_thread.error.connect(self.on_processing_error)
        self.process_thread.start()
    
    def on_processing_finished(self, result):
        """处理完成"""
        # 恢复按钮
        self.process_btn.setEnabled(True)
        self.photos_btn.setEnabled(True)
        self.vcf_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.status_label.setText('处理完成')
        
        # 显示结果
        output = []
        output.append("=" * 50)
        output.append("处理结果")
        output.append("=" * 50)
        output.append(f"\n匹配成功: {result['matched_count']} 张照片")
        output.append(f"匹配到: {result.get('matched_contact_count', 0)} 位联系人")
        output.append(f"总联系人: {result['total_contacts']} 个")
        output.append(f"总照片数: {result['total_photos']} 张")
        output.append(f"HTML相册: {result['html_path']}")
        
        if result['matched_contacts']:
            output.append("\n匹配详情：")
            output.append("-" * 50)
            # 按联系人分组统计
            contact_count = {}
            for match in result['matched_contacts']:
                contact_name = match['contact']['name']
                if contact_name not in contact_count:
                    contact_count[contact_name] = 0
                contact_count[contact_name] += 1
            
            for i, (name, count) in enumerate(contact_count.items(), 1):
                output.append(f"{i}. {name}: {count} 张照片")
        
        # 显示每张照片提取到的标签（调试信息）
        if 'photo_tags_info' in result and result['photo_tags_info']:
            output.append("\n" + "=" * 50)
            output.append("照片标签提取结果（调试信息）：")
            output.append("=" * 50)
            
            # 按文件名排序显示
            sorted_photos = sorted(result['photo_tags_info'].items(), 
                                  key=lambda x: x[1]['filename'])
            
            for photo_path, info in sorted_photos:
                filename = info['filename']
                tags = info['tags']
                
                output.append(f"\n📷 {filename}")
                if tags:
                    tags_str = '、'.join(tags) if tags else '无'
                    output.append(f"   提取到标签: {tags_str}")
                else:
                    output.append(f"   提取到标签: 无")
        
        if result['unmatched_photos']:
            output.append("\n" + "=" * 50)
            output.append(f"未匹配的照片 ({len(result['unmatched_photos'])} 张):")
            output.append("=" * 50)
            for photo in result['unmatched_photos'][:10]:  # 只显示前10个
                output.append(f"  - {os.path.basename(photo)}")
            if len(result['unmatched_photos']) > 10:
                output.append(f"  ... 还有 {len(result['unmatched_photos']) - 10} 张未显示")
        
        if result['unmatched_contacts']:
            output.append(f"\n未匹配的联系人 ({len(result['unmatched_contacts'])} 个):")
            output.append("-" * 50)
            for contact in result['unmatched_contacts']:
                output.append(f"  - {contact['name']} ({contact.get('org', '无单位')})")
        
        output.append("\n" + "=" * 50)
        output.append("HTML相册功能：")
        output.append("1. 显示联系人信息和照片")
        output.append("2. 搜索联系人（姓名、单位、电话、邮箱）")
        output.append("3. 点击照片可放大查看")
        output.append("=" * 50)
        
        self.result_text.setText('\n'.join(output))
        
        # 显示成功消息并询问是否打开HTML
        reply = QMessageBox.question(
            self,
            '处理完成',
            f'处理完成！\n\n匹配成功: {result["matched_count"]} 张照片\n\n'
            f'HTML相册已保存到:\n{result["html_path"]}\n\n'
            f'是否在浏览器中打开？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(result['html_path']))
    
    def on_processing_error(self, error_msg):
        """处理错误"""
        # 恢复按钮
        self.process_btn.setEnabled(True)
        self.photos_btn.setEnabled(True)
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
