from PyQt5.QtWidgets import (QCheckBox, QDialog, QListWidget, QMainWindow,  
                             QVBoxLayout, QWidget, QLineEdit, QTextEdit,
                             QPushButton, QHBoxLayout, QLabel, QApplication,
                             QListWidgetItem, QDialogButtonBox, QFileDialog)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize, Qt
from process import Query_Analyzer
import os

WIDTH, HEIGHT = 300, 150

def main():    
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()
    app.exec_()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.containter_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.containter_widget)
        self.search_dir = os.getcwd()
        self.dir_label = None
        self.checkbox = None
        self.text_edit = None
        self.analyzer = None
        self.result_window = None
        self.init_ui()

    def init_ui(self):
        self.init_window()
        self.init_headlabel()
        self.init_dir_widget()
        self.main_layout.addSpacing(10)
        self.init_textedit()
        self.init_button()
        self.main_layout.addStretch(1)
        self.init_checkbox()

        self.containter_widget.setLayout(self.main_layout)

    def init_window(self):
        self.setWindowTitle("Search engine")
        self.setFixedSize(QSize(WIDTH, HEIGHT))
        self.setCentralWidget(self.containter_widget)

    def init_headlabel(self):
        headlabel = QLabel('Searching directory:')
        headlabel.setFont(QFont('Helvetica', 12, QFont.Bold))
        self.main_layout.addWidget(headlabel)

    def init_dir_widget(self):
        dir_hbox = QHBoxLayout()
        self.dir_label = QLabel(self.search_dir)
        self.dir_label.setFont(QFont('Courier New', 10))
        dir_button = QPushButton('...')
        dir_button.setMaximumSize(QSize(30, 30))
        dir_button.clicked.connect(self.on_dirbutton_click)

        dir_hbox.addWidget(self.dir_label)
        dir_hbox.addWidget(dir_button)
        dir_hbox.addStretch(1)
        self.main_layout.addLayout(dir_hbox)

    def init_textedit(self):
        self.textEdit = QLineEdit()
        self.textEdit.setPlaceholderText('Type in your query')
        self.main_layout.addWidget(self.textEdit)
      
    def init_button(self):
        button = QPushButton()
        button.setText('Search')
        button.clicked.connect(self.on_searchbutton_click)

        button_hbox = QHBoxLayout()
        button_hbox.addStretch(1)
        button_hbox.addWidget(button)
        button_hbox.addStretch(1)
        self.main_layout.addLayout(button_hbox)

    def init_checkbox(self):
        self.checkbox = QCheckBox()
        self.checkbox.setText('Search subdirectories')
        bot_hbox = QHBoxLayout()
        bot_hbox.addStretch(1)
        bot_hbox.addWidget(self.checkbox)
        self.main_layout.addLayout(bot_hbox)

    def on_searchbutton_click(self):
        query = self.textEdit.text()
        if len(query) > 0:
            try:
                if self.need_new_analyzer():
                    self.analyzer = Query_Analyzer(self.search_dir, 
                                                   self.subdirs_enabled())
            except OSError:
                InfoDialog('Could not access the provided directory.').exec()
                return

            self.handle_query(query)
    
    def handle_query(self, query):
        if self.analyzer.n_files == 0:
            InfoDialog('Could not find any file in the provided directory.').exec()
            return

        self.analyzer.analyze_query(query)
        if self.analyzer.files_indices:
            self.result_window = ResultWindow(self.analyzer)
            self.result_window.show()
        else:
            #no term in query is in the bag of words
            InfoDialog('Your search did not match any file.').exec()        

    def on_dirbutton_click(self):
        chosen_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if chosen_dir:
            self.search_dir = chosen_dir
            self.dir_label.setText(chosen_dir)

    def need_new_analyzer(self):
        return (self.analyzer == None or
                self.search_dir != self.analyzer.dir or
                self.subdirs_enabled() != self.analyzer.recursive)

    def subdirs_enabled(self):
        return self.checkbox.isChecked()


class InfoDialog(QDialog):
    def __init__(self, msg, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Search engine')

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(msg))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class ResultWindow(QWidget):
    def __init__(self, analyzer):
        super().__init__()
        self.setWindowTitle('Search engine - results')
        self.analyzer = analyzer
        self.main_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.text_window = None
        
        self.init_list()
        self.setLayout(self.main_layout)

    def init_list(self):
        most_acc = self.analyzer.pop_most_accurate()
        self.append_to_list(most_acc)
        self.list_widget.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.list_widget.itemDoubleClicked.connect(self.on_item_doubleclick)
        self.main_layout.addWidget(self.list_widget)

    def append_to_list(self, filenames):
        for filename in filenames:
            widget = self.make_item_widget(filename)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def on_scroll(self, value):
        if value == self.list_widget.verticalScrollBar().maximum():
            most_acc = self.analyzer.pop_most_accurate(k=5)
            self.append_to_list(most_acc)

    def on_item_doubleclick(self, item):
        filename = self.list_widget.itemWidget(item).text()
        path = self.analyzer.tbd_matrix.filepaths[filename]
        try:
            self.text_window = TextWindow(filename, path)
            self.text_window.show()
        except (PermissionError, FileNotFoundError):
            InfoDialog('Failed to open the file.').exec()

    def make_item_widget(self, filename):
        label = QLabel(filename)
        label.setAlignment(Qt.AlignCenter)
        label.setMargin(5)
        return label


class TextWindow(QWidget):
    def __init__(self, name, path):
        super().__init__()
        self.setWindowTitle(name)
        self.main_layout = QVBoxLayout()

        self.init_content(path)
        self.setLayout(self.main_layout)

    def init_content(self, path):
        content = ''
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(content)
        self.main_layout.addWidget(text_edit)        

        
if __name__ == '__main__':
    main()