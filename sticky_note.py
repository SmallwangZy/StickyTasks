import sys
import os
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                           QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
                           QSystemTrayIcon, QMenu, QAction, QSizeGrip)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QFont

class StickyNote(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.always_on_top = False
        self.current_font_size = 12  # 初始字体大小
        self.resize_margin = 5  # 调整大小的边缘宽度
        self.resizing = False
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.dragPos = None  # 初始化拖动位置
        
        # 获取保存文件路径
        self.notes_file = os.path.expanduser('~/.stickynotes')
        
        # 尝试读取之前保存的内容
        self.load_notes()
        
    def initUI(self):
        # 设置窗口基本属性
        self.setWindowTitle('便签')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 350)  # 初始窗口尺寸
        self.setMinimumSize(200, 150)  # 设置最小窗口尺寸
        
        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mypad.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #fff7e6;")
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)  # 添加边距
        
        # 创建顶部按钮栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)  # 增加按钮之间的间距
        
        # 关闭按钮
        close_btn = QPushButton('×')
        close_btn.setFixedSize(25, 25)  # 增大按钮尺寸
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
        
        # 置顶按钮
        self.pin_btn = QPushButton('📌')
        self.pin_btn.setFixedSize(25, 25)  # 增大按钮尺寸
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
        
        top_bar.addWidget(self.pin_btn)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        
        # 添加文本编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ffd8a8;
                background-color: #fff7e6;
                padding: 10px;
                font-size: 12pt;
                border-radius: 5px;
            }
        """)
        
        # 将部件添加到布局中
        layout.addLayout(top_bar)
        layout.addWidget(self.text_edit)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self)
        size_grip.setStyleSheet("background: transparent;")
        
        # 设置整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fff7e6;
            }
        """)
        
        # 为文本编辑区添加鼠标滚轮事件
        self.text_edit.wheelEvent = self.custom_wheel_event

    def load_notes(self):
        """从文件读取笔记内容"""
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_edit.setPlainText(content)
        except FileNotFoundError:
            # 如果文件不存在，不做任何操作
            pass
        except Exception as e:
            print(f"读取笔记时出错: {e}")

    def save_notes(self):
        """将笔记内容保存到文件"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
        except Exception as e:
            print(f"保存笔记时出错: {e}")

    def custom_wheel_event(self, event):
        # 检查是否按下Ctrl键
        if event.modifiers() == Qt.ControlModifier:
            # 获取滚轮角度
            angle = event.angleDelta().y()
            
            # 根据滚轮方向调整字体大小
            if angle > 0:
                # 向上滚动，增大字体
                self.current_font_size = min(self.current_font_size + 1, 30)
            else:
                # 向下滚动，减小字体
                self.current_font_size = max(self.current_font_size - 1, 6)
            
            # 设置新的字体大小
            font = self.text_edit.font()
            font.setPointSize(self.current_font_size)
            self.text_edit.setFont(font)
            
            # 更新样式表以反映字体大小
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{
                    border: 1px solid #ffd8a8;
                    background-color: #fff7e6;
                    padding: 10px;
                    font-size: {self.current_font_size}pt;
                    border-radius: 5px;
                }}
            """)
        else:
            # 如果没有按Ctrl键，使用默认的滚轮行为
            super(QTextEdit, self.text_edit).wheelEvent(event)

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
    
    def mousePressEvent(self, event):
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
                self.resize_start_pos = event.globalPos()
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
    app.setQuitOnLastWindowClosed(False)  # 防止关闭所有窗口时退出程序
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mypad.ico')
    
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
            note.activateWindow()  # 确保窗口在最前面
    
    def toggle_pin_state():
        # 直接调用现有的置顶方法
        note.toggle_always_on_top()
    
    # 创建应用实例后再注册快捷键
    keyboard.add_hotkey('shift+alt+q', toggle_visibility, suppress=True)
    keyboard.add_hotkey('shift+alt+w', toggle_pin_state, suppress=True)
    
    note.show()  # 先显示一次窗口
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
