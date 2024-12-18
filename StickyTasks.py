import sys
import os
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                           QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
                           QSystemTrayIcon, QMenu, QAction, QSizeGrip, QScrollArea,
                           QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPoint, QDate
from PyQt5.QtGui import QIcon, QFont, QColor
import yaml

class CellWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_font_size = 12  # 初始字体大小
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 1, 1, 1)  # 单元格左边距设为0
        layout.setSpacing(8)  # 保持水平间距不变
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(2, 0, 2, 0)  # 给按钮容器添加适当的左右边距
        button_layout.setSpacing(1)
        
        # 创建红色删除按钮
        self.delete_btn = QPushButton('×')
        self.delete_btn.setFixedSize(25, 25)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        # 创建绿色完成按钮
        self.complete_btn = QPushButton('✓')
        self.complete_btn.setFixedSize(25, 25)
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.complete_btn)
        button_container.setLayout(button_layout)
        
        # 创建文本编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(100)  # 固定单元格高度
        font = self.text_edit.font()
        font.setPointSize(self.current_font_size)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        # 为文本编辑区添加事件过滤器
        self.text_edit.installEventFilter(self)
        
        layout.addWidget(button_container)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        # 连接信号
        self.complete_btn.clicked.connect(self.toggle_complete)
        self.is_completed = False
        
    def eventFilter(self, obj, event):
        if obj == self.text_edit and event.type() == event.Wheel:
            # 仅处理Ctrl+滚轮事件，用于调整字体大小
            if event.modifiers() == Qt.ControlModifier:
                angle = event.angleDelta().y()
                if angle > 0:
                    self.current_font_size = min(self.current_font_size + 1, 30)
                else:
                    self.current_font_size = max(self.current_font_size - 1, 6)
                
                font = self.text_edit.font()
                font.setPointSize(self.current_font_size)
                self.text_edit.setFont(font)
                return True  # 事件已处理
        return super().eventFilter(obj, event)  # 其他事件交给父类处理

    def toggle_complete(self):
        self.is_completed = not self.is_completed
        if self.is_completed:
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: #777777;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 5px;
                }}
            """)
            self.text_edit.setReadOnly(True)
        else:
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 5px;
                }}
            """)
            self.text_edit.setReadOnly(False)

class StickyNote(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.always_on_top = False
        self.current_font_size = 12
        self.resize_margin = 5
        self.resizing = False
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.dragPos = None
        
        # 获取保存文件路径
        self.notes_file = os.path.expanduser('~/.stickynotes.xml')
        
        # 尝试读取之前保存的内容
        self.load_notes()
        
        # 如果没有任何单元格，才创建第一个单元格
        if self.cells_layout.count() == 1:  # 只有stretch项时
            self.add_cell()
        
    def initUI(self):
        self.setWindowTitle('便签')
        self.setWindowFlags(Qt.FramelessWindowHint)  # 无边框窗口
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置透明背景，这样圆角才能显示
        self.setGeometry(100, 100, 400, 500)
        self.setMinimumSize(300, 200)
        
        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #ffd8a8,
                    stop: 0.3 #ffe8cc,
                    stop: 0.6 #fff3e0,
                    stop: 1 #fff9db
                );
                border-radius: 10px;
            }
        """)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(1, 5, 5, 5)  # 左边距减小到1像素
        
        # 创建顶部按钮栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
       
        
        # 添加日期标签
        from datetime import datetime
        date_label = QLabel(datetime.now().strftime("%Y-%m-%d"))
        date_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 14px;
                font-weight: 500;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 8px;
            }
        """)
        
         # 导出Markdown按钮
        export_btn = QPushButton('📝')
        export_btn.setFixedSize(25, 25)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                border: none;
                color: white;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
        export_btn.clicked.connect(self.export_markdown)  # 连接导出功能
        
        # 置顶按钮
        self.pin_btn = QPushButton('📌')
        self.pin_btn.setFixedSize(25, 25)
        self.pin_btn.clicked.connect(self.toggle_always_on_top)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                border: none;
                color: white;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)

        # 添加新单元格按钮
        add_btn = QPushButton('+')
        add_btn.setFixedSize(25, 25)
        add_btn.clicked.connect(self.add_cell)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffd43b;
                border: none;
                color: white;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fcc419;
            }
        """)
        
        
        # 关闭按钮
        close_btn = QPushButton('×')
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                border: none;
                color: white;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        
        top_bar.addWidget(date_label)  # 添加日期标签
        top_bar.addWidget(self.pin_btn)  # 钉住按钮
        top_bar.addWidget(add_btn)      # 添加按钮
        top_bar.addWidget(export_btn)  # 将导出按钮添加到布局
        top_bar.addStretch()
        top_bar.addWidget(close_btn)    # 关闭按钮
        
        self.main_layout.addLayout(top_bar)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(241, 243, 245, 0.6);
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(173, 181, 189, 0.8);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(134, 142, 150, 0.9);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 为滚动区域添加事件过滤器
        self.scroll_area.viewport().installEventFilter(self)
        
        # 创建单元格容器
        self.cells_widget = QWidget()
        self.cells_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.cells_layout = QVBoxLayout(self.cells_widget)
        self.cells_layout.setSpacing(10)
        self.cells_layout.addStretch()  # 添加弹性空间
        
        self.scroll_area.setWidget(self.cells_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        self.show()
    
    def add_cell(self):
        cell = CellWidget()
        cell.delete_btn.clicked.connect(self.create_delete_handler(cell))
        # 在最后一个单元格之前插入新单元格（保持stretch在最后）
        self.cells_layout.insertWidget(self.cells_layout.count() - 1, cell)
    
    def create_delete_handler(self, cell):
        """创建删除处理器"""
        def delete_handler():
            index = self.cells_layout.indexOf(cell)
            if index != -1:  # 确保单元格存在
                self.cells_layout.itemAt(index).widget().deleteLater()
                self.save_notes()  # 删除后保存笔记
        return delete_handler
    
    def delete_cell(self, cell):
        """已弃用的删除方法"""
        pass

    def save_notes(self):
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element("stickynotes")
        
        for i in range(self.cells_layout.count()):
            cell = self.cells_layout.itemAt(i).widget()
            if cell:
                # 获取单元格文本内容并去除首尾空白
                text_content = cell.text_edit.toPlainText().strip()
                # 只保存非空单元格
                if text_content:
                    note = ET.SubElement(root, "note")
                    text = ET.SubElement(note, "text")
                    # 保存原始文本（包括中间的换行和空格），只去除首尾空白
                    text.text = text_content
                    completed = ET.SubElement(note, "completed")
                    completed.text = str(cell.is_completed)
        
        # 创建格式化的XML字符串
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
        
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                f.write(xml_str)
        except Exception as e:
            print(f"保存笔记时出错: {e}")

    def load_notes(self):
        import xml.etree.ElementTree as ET
        
        try:
            if os.path.exists(self.notes_file):
                tree = ET.parse(self.notes_file)
                root = tree.getroot()
                
                for note in root.findall('note'):
                    text = note.find('text').text or ""
                    completed = note.find('completed').text.lower() == 'true'
                    
                    cell = CellWidget()
                    cell.delete_btn.clicked.connect(self.create_delete_handler(cell))
                    cell.text_edit.setText(text)
                    if completed:
                        cell.toggle_complete()
                    self.cells_layout.insertWidget(self.cells_layout.count() - 1, cell)
        except Exception as e:
            print(f"加载笔记时出错: {e}")

    def load_config(self):
        config_path = os.path.expanduser('./config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                export_path = config.get('export_path', '~/')
                # 检查路径是否有效
                if not os.path.isdir(os.path.normpath(export_path)):
                    return '~/'
                return os.path.normpath(export_path)
        return '~/'

    def export_markdown(self):
        # 合并所有单元格内容并导出为Markdown文件
        date_str = QDate.currentDate().toString("yyyy-MM-dd")
        content = "# {}任务\n\n".format(date_str)
        for i in range(self.cells_layout.count()):
            cell = self.cells_layout.itemAt(i).widget()
            if cell:
                text_content = cell.text_edit.toPlainText().strip()
                if text_content:
                    content += f"## 任务 {i+1}\n\n{text_content}\n\n"
        export_path = self.load_config()  # 从配置文件加载导出路径
        print(export_path)
        export_path = os.path.expanduser(export_path)  # 处理~符号
        file_path = os.path.join(export_path, f'{date_str}.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        QMessageBox.information(self, '导出成功', f'已导出为 {file_path}')

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        if self.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.pin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff922b;
                    border: none;
                    color: white;
                    border-radius: 12px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #fd7e14;
                }
            """)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.pin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4dabf7;
                    border: none;
                    color: white;
                    border-radius: 12px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #339af0;
                }
            """)
        self.show()
    
    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == event.Wheel:
            # 仅处理Shift+滚轮事件，用于滚动整个区域
            if event.modifiers() == Qt.ShiftModifier:
                # 创建一个新的滚轮事件，不带修饰键
                new_event = QWheelEvent(
                    event.pos(),
                    event.globalPos(),
                    event.pixelDelta(),
                    event.angleDelta(),
                    event.buttons(),
                    Qt.NoModifier,  # 移除修饰键
                    event.phase(),
                    event.inverted()
                )
                # 将事件发送给滚动区域
                return self.scroll_area.wheelEvent(new_event)
            elif event.modifiers() == Qt.ControlModifier:
                # 阻止Ctrl+滚轮事件影响滚动
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        # self.rect() 窗口大小
        # self.pos() 窗口位置
        if event.button() == Qt.LeftButton:
            # 获取窗口边缘
            rect = self.rect()
            pos = event.pos()
            # 主要检查右边和下边的调整区域
            if pos.x() >= rect.width() - self.resize_margin:  # 右边缘
                if pos.y() >= rect.height() - self.resize_margin:  # 右下角
                    self.resize_edge = 'bottom-right'
                    self.resizing = True
                else:  # 右边
                    self.resize_edge = 'right'
                    self.resizing = True
            elif pos.y() >= rect.height() - self.resize_margin:  # 下边缘
                self.resize_edge = 'bottom'
                self.resizing = True
            else:
                self.resizing = False
                self.dragPos = event.globalPos()  # 初始化拖动位置
            
            # 记录初始大小和位置
            if self.resizing:
                self.resize_start_pos = event.globalPos() # 确保拖动位置被初始化
                self.resize_start_geometry = self.geometry() 
            else:
                self.dragPos = event.globalPos()  # 确保拖动位置被初始化

    def mouseMoveEvent(self, event):
        # 获取鼠标位置和窗口大小
        pos = event.pos()
        rect = self.rect()
        
        # 更新鼠标光标
        if pos.x() >= rect.width() - self.resize_margin:  # 右边缘
            if pos.y() >= rect.height() - self.resize_margin:  # 右下角
                self.setCursor(Qt.SizeFDiagCursor)  # 对角调整光标
            else:
                self.setCursor(Qt.SizeHorCursor)  # 水平调整光标
        elif pos.y() >= rect.height() - self.resize_margin:  # 下边缘
            self.setCursor(Qt.SizeVerCursor)  # 垂直调整光标
        else:
            self.setCursor(Qt.ArrowCursor)  # 默认光标
        
        if self.resizing and event.buttons() == Qt.LeftButton:
            # 计算鼠标移动的距离
            diff = event.globalPos() - self.resize_start_pos
            new_geo = self.resize_start_geometry
            
            # 根据拖动边缘调整窗口大小
            if self.resize_edge == 'right':
                new_width = new_geo.width() + diff.x()
                if new_width >= self.minimumWidth():
                    new_geo.setWidth(new_width)
            elif self.resize_edge == 'bottom':
                new_height = new_geo.height() + diff.y()
                if new_height >= self.minimumHeight():
                    new_geo.setHeight(new_height)
            elif self.resize_edge == 'bottom-right':
                new_width = new_geo.width() + diff.x()
                new_height = new_geo.height() + diff.y()
                if new_width >= self.minimumWidth() and new_height >= self.minimumHeight():
                    new_geo.setWidth(new_width)
                    new_geo.setHeight(new_height)
            
            # 应用新的几何信息
            self.setGeometry(new_geo)
        elif event.buttons() == Qt.LeftButton and not self.resizing and self.dragPos is not None:
            # 移动窗口
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_edge = None
            self.dragPos = None  # 重置拖动位置
            # 重置光标
            self.setCursor(Qt.ArrowCursor)

    def enterEvent(self, event):
        self.setCursor(Qt.ArrowCursor)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    
    # 创建系统托盘图标
    tray_icon = QSystemTrayIcon()
    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    
    # 创建系统托盘菜单
    tray_menu = QMenu()
    
    # 创建便签实例
    note = StickyNote()
    
    # 显示便签动作
    show_action = QAction("显示便签", tray_menu)
    show_action.triggered.connect(note.show)
    tray_menu.addAction(show_action)
    
    # 隐藏便签动作
    hide_action = QAction("隐藏便签", tray_menu)
    hide_action.triggered.connect(note.hide)
    tray_menu.addAction(hide_action)
    
    # 退出程序动作
    exit_action = QAction("退出", tray_menu)
    def exit_app():
        # 在退出前保存笔记
        note.save_notes()
        app.quit()
    exit_action.triggered.connect(exit_app)
    tray_menu.addAction(exit_action)
    
    # 设置托盘菜单
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    def toggle_visibility():
        if note.isVisible():
            note.hide()
        else:
            note.show()
            note.activateWindow()  
    
    def toggle_pin_state():
        # 直接调用现有的置顶方法
        note.toggle_always_on_top()
    
    # 创建应用实例后再注册快捷键
    keyboard.add_hotkey('ctrl+alt+q', toggle_visibility, suppress=True)
    keyboard.add_hotkey('ctrl+alt+w', toggle_pin_state, suppress=True)
    
    note.show()  
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
