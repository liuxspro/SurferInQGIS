# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Preview.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(588, 300)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        Form.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.data_tableWidget = QtWidgets.QTableWidget(self.groupBox)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        self.data_tableWidget.setFont(font)
        self.data_tableWidget.setObjectName("data_tableWidget")
        self.data_tableWidget.setColumnCount(0)
        self.data_tableWidget.setRowCount(0)
        self.verticalLayout_2.addWidget(self.data_tableWidget)
        self.verticalLayout.addWidget(self.groupBox)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox.setTitle(_translate("Form", "数据预览"))
