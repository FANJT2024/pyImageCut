from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import sys
import os
import time
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import QEventLoop, QTimer, Qt, QBasicTimer
from PyQt5.QtWidgets  import QMessageBox
import datetime
from PIL import Image
import numpy as np
import re
import imghdr
from pdf2image import convert_from_path, convert_from_bytes
import tempfile
import fitz
from PyPDF2 import PdfFileReader, PdfFileWriter
import xlrd
from xlutils.copy import copy
from UI_TZM import Ui_MainWindow


class EmittingStr(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)  # 定义一个发送str的信号

    def write(self, text):
        self.textWritten.emit(str(text))
        loop = QEventLoop()
        QTimer.singleShot(1, loop.quit)
        loop.exec_()


class ControlBoard(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(ControlBoard, self).__init__()
        self.setupUi(self)
        # 下面将输出重定向到textBrowser中
        sys.stdout = EmittingStr(textWritten=self.outputWritten)
        sys.stderr = EmittingStr(textWritten=self.outputWritten)

        self.step = 0
        self.path_ok = 0
        self.frame_bfb.setVisible(False)

        self.btn_path_in_change.clicked.connect(lambda: self.chengpath("in"))
        self.btn_path_out_change.clicked.connect(lambda: self.chengpath("out"))
        self.btn_path_in_open.clicked.connect(lambda: self.openDir("in"))
        self.btn_path_out_open.clicked.connect(lambda: self.openDir("out"))

        self.radioButton_xs.toggled.connect(self.radiobntstate)
        self.radioButton_bfb.toggled.connect(self.radiobntstate)

        self.groupBox_cut.toggled.connect(self.selectCheck)
        self.groupBox_convert.toggled.connect(self.selectCheck)
        self.groupBox_rezise.toggled.connect(self.selectCheck)
        self.groupBox_arrs.toggled.connect(self.selectCheck)

        self.btn_cut_do.clicked.connect(lambda: self.bClicked("cut"))
        self.btn_convert_do.clicked.connect(lambda: self.bClicked("convert"))
        self.btn_resize_do.clicked.connect(lambda: self.bClicked("resize"))
        self.btn_arss_do.clicked.connect(lambda: self.bClicked("arrs"))
        self.btn_group.clicked.connect(lambda: self.bClicked("combination"))
        self.btn_clear_info.clicked.connect(self.clear_event)

        self.timer = QBasicTimer()
        self.step = 0
        self.Method = 0
        self.DPI.setEnabled(True)
        self.label_3.setEnabled(True)
        self.zoomxy.setEnabled(False)
        self.label_4.setEnabled(False)

        self.bnt_convert_ok.clicked.connect(self.bClicked_pdf)
        self.bnt_select_file.clicked.connect(self.selectfiles)
        self.radioButton.toggled.connect(lambda: self.radiobntstate_pdf(self.radioButton))
        self.radioButton_2.toggled.connect(lambda: self.radiobntstate_pdf(self.radioButton_2))

        self.btn_pdf_merge.clicked.connect(self.getText)

        self.DPI.textChanged.connect(lambda: self.write_excel(0,str(self.DPI.text())))
        self.file_name.textChanged.connect(lambda: self.write_excel(1, str(self.file_name.text())))

        self.lineEdit_path_in.textChanged.connect(lambda: self.write_excel(2, str(self.lineEdit_path_in.text())))

        self.lineEdit_path_out.textChanged.connect(lambda: self.write_excel(3, str(self.lineEdit_path_out.text())))
        self.lineEdit_x0.textChanged.connect(lambda: self.write_excel(4, str(self.lineEdit_x0.text())))
        self.lineEdit_x1.textChanged.connect(lambda: self.write_excel(5, str(self.lineEdit_x1.text())))
        self.lineEdit_y0.textChanged.connect(lambda: self.write_excel(6, str(self.lineEdit_y0.text())))

        self.lineEdit_y1.textChanged.connect(lambda: self.write_excel(7, str(self.lineEdit_y1.text())))
        self.lineEdit_zoomx.textChanged.connect(lambda: self.write_excel(8, str(self.lineEdit_zoomx.text())))

        self.lineEdit_zoomxy.textChanged.connect(lambda: self.write_excel(9, str(self.lineEdit_zoomxy.text())))
        self.lineEdit_zoomy.textChanged.connect(lambda: self.write_excel(10, str(self.lineEdit_zoomy.text())))
        self.Merge_name.textChanged.connect(lambda: self.write_excel(11, str(self.Merge_name.text())))
        self.bg_zoomx.textChanged.connect(lambda: self.write_excel(12, str(self.bg_zoomx.text())))
        self.bg_zoomy.textChanged.connect(lambda: self.write_excel(13, str(self.bg_zoomy.text())))
        self.cj = 0
        if self.cj == 0:
            self.read_excel()

        self.bnt_getbgcolor.clicked.connect(self.getBgColor)
        self.r = 192
        self.g = 192
        self.b = 192
        self.btn_resize_bg.clicked.connect(self.centr_Image)
        self.btn_resize_bg1.clicked.connect(self.centr1_Image)
    def getBgColor(self):
        color = QColorDialog.getColor()
        r,g,b = color.red(), color.green(), color.blue()
        inverted_r,inverted_g,inverted_b = 255-color.red(), 255-color.green(), 255-color.blue()
        print("背景颜色：",color.name())
        print("背景颜色：",r,",",g,",",b)
        #self.Bgcolor.setAutoFillBackground(True)
        self.bnt_getbgcolor.setAutoFillBackground(True)
        #self.Bgcolor.setStyleSheet('QWidget {background-color:rgb(%s,%s,%s)}' % (r,g,b))
        #self.Bgcolor.setStyleSheet('QWidget {background-color:%s}' % color.name())
        self.bnt_getbgcolor.setStyleSheet('QWidget {color:rgb(%s,%s,%s);background-color:%s}' % (inverted_r, inverted_g, inverted_b,color.name()))
        self.r = r
        self.g = g
        self.b = b
    def read_excel(self):
        fname = "media\pr_name.xlsx"
        #path = 'D:\PycharmProjects\Learning'
        path = os.getcwd()
        filename = os.path.join(path, fname)
        #print(filename)

        try:
            work = xlrd.open_workbook(filename, encoding_override="utf-8")
        except IOError:
            print("open %s failed" % filename)
        else:
            sheet = work.sheet_by_index(0)
            self.DPI.setText(str(sheet.row_values(0)[1]))
            self.file_name.setText(str(sheet.row_values(1)[1]))
            self.lineEdit_path_in.setText(str(sheet.row_values(2)[1]))
            self.lineEdit_path_out.setText(str(sheet.row_values(3)[1]))
            self.lineEdit_x0.setText(str(sheet.row_values(4)[1]))
            self.lineEdit_x1.setText(str(sheet.row_values(5)[1]))
            self.lineEdit_y0.setText(str(sheet.row_values(6)[1]))
            self.lineEdit_y1.setText(str(sheet.row_values(7)[1]))
            self.lineEdit_zoomx.setText(str(sheet.row_values(8)[1]))
            self.lineEdit_zoomxy.setText(str(sheet.row_values(9)[1]))
            self.lineEdit_zoomy.setText(str(sheet.row_values(10)[1]))
            self.Merge_name.setText(str(sheet.row_values(11)[1]))
            self.bg_zoomx.setText(str(sheet.row_values(12)[1]))
            self.bg_zoomy.setText(str(sheet.row_values(13)[1]))
            self.cj = 1

    def write_excel(self,row,text):
        fname = "media\pr_name.xlsx"
        #path = 'D:\PycharmProjects\Learning'
        path = os.getcwd()
        filename = os.path.join(path, fname)
        #print(filename)
        try:
            rb = xlrd.open_workbook(filename, encoding_override="utf-8")
        except IOError:
            print("open %s failed" % filename)
        else:
            wb = copy(rb)

            ws = wb.get_sheet(0)
            ws.write(row, 1, text)
            wb.save(filename)


    def outputWritten(self, text):
        self.cursor = self.textBrowser.textCursor()
        self.cursor.movePosition(QtGui.QTextCursor.End)
        self.cursor.insertText(text)
        self.textBrowser.setTextCursor(self.cursor)
        self.textBrowser.ensureCursorVisible()

    def selectfiles(self):
        in_path = self.file_name.text()
        self.fileName, self.fileType = QtWidgets.QFileDialog.getOpenFileName(
            self, "选取文件", in_path , "所有文件(*.*)")
        if self.fileName != "":
            self.file_name.setText(self.fileName)
        else:
            pass
        print(self.fileName)
    def radiobntstate_pdf(self, bnt):
        if bnt.text() == "方法一":
            if bnt.isChecked() == True:
                self.DPI.setEnabled(True)
                self.label_3.setEnabled(True)
                self.zoomxy.setEnabled(False)
                self.label_4.setEnabled(False)
                self.Method = 0
            else:
                self.DPI.setEnabled(False)
                self.label_3.setEnabled(False)
                self.zoomxy.setEnabled(True)
                self.label_4.setEnabled(True)
        if bnt.text() == "方法二":
            if bnt.isChecked() == True:
                self.DPI.setEnabled(False)
                self.label_3.setEnabled(False)
                self.zoomxy.setEnabled(True)
                self.label_4.setEnabled(True)
                self.Method = 1
            else:
                self.DPI.setEnabled(True)
                self.label_3.setEnabled(True)
                self.zoomxy.setEnabled(False)
                self.label_4.setEnabled(False)
        print("Method=",self.Method)

    def processbar_ok(self):
        self.step = self.step + 1
        self.progressBar.setValue(self.step)
        time.sleep(0.001)
        QApplication.processEvents()

    def bClicked_pdf(self):
        """Runs the main function."""
        print('Begin')
        self.setdisab()
        if self.Method == 0:
            self.pdf2image2()
        if self.Method == 1:
            self.pdf2image3()
        self.setenab()
        print("End")

    def bClicked(self, type_value):
        print('Begin')
        self.setdisab()
        self.batchImage(type_value)
        self.setenab()
        print("End")

    def clear_event(self):
        self.textBrowser.clear()

    def chengpath(self, linex):
        open_1 = QFileDialog()

        if linex == "in":
            self.path = open_1.getExistingDirectory(
                self, "选取文件夹", self.lineEdit_path_in.text())
            self.lineEdit_path_in.setText(self.path)
            print("输入路径：", self.path)
        if linex == "out":
            self.path = open_1.getExistingDirectory(
                self, "选取文件夹", self.lineEdit_path_out.text())
            self.lineEdit_path_out.setText(self.path)
            print("输出路径：", self.path)

    def openDir(self, linex):  # 打开文件夹
        if linex == "in":
            folder = self.lineEdit_path_in.text()
        if linex == "out":
            folder = self.lineEdit_path_out.text()
        os.startfile(folder)

    def radiobntstate(self):
        if self.radioButton_xs.text() == "按像素调整":
            if self.radioButton_xs.isChecked():
                self.frame_xs.setVisible(True)
                self.frame_bfb.setVisible(False)
            else:
                self.frame_xs.setVisible(False)
                self.frame_bfb.setVisible(True)
        if self.radioButton_bfb.text() == "按百分比调整":
            if self.radioButton_bfb.isChecked():
                self.frame_xs.setVisible(False)
                self.frame_bfb.setVisible(True)
            else:
                self.frame_xs.setVisible(True)
                self.frame_bfb.setVisible(False)

    def selectCheck(self):
        if self.groupBox_cut.isChecked() or self.groupBox_convert.isChecked(
        ) or self.groupBox_rezise.isChecked() or self.groupBox_arrs.isChecked():
            self.btn_group.setEnabled(True)
        else:
            self.btn_group.setEnabled(False)

    def makedirs_f(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print("成功创建文件夹：", path)
        else:
            print("文件夹已存在无需重新创建！！！")

    def samepath(self, in_path, out_path):
        #in_path = self.lineEdit_path_in.text()
        #out_path = self.lineEdit_path_out.text()

        filePath = in_path + '/' + 'out'
        if in_path == out_path:
            self.reply = QMessageBox.information(
                self,
                "确认窗口",
                "输出与输入路径一致，选是将在本目录下创建一个新的文件夹，选否将强制给输出对象文件加前缀！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes)
            if self.reply == QMessageBox.Yes:
                self.makedirs_f(filePath)
                out_path = filePath
                self.lineEdit_path_out.setText(out_path)
                print("成功创建文件夹：", out_path)
                QApplication.processEvents()
            else:
                self.checkBox_add_New.setChecked(True)
                self.checkBox_add_New.setEnabled(False)
                QApplication.processEvents()
        else:
            print("路径设置正确")

    def restart_s(self):
        print("请先设置参数，点击《执行》开始批量处理....")
        self.setenab()

    def setenab(self):
        self.groupBox.setEnabled(True)
        self.groupBox_3.setEnabled(True)
        self.btn_clear_info.setEnabled(True)
        self.Merge_name.setEnabled(True)
        self.btn_pdf_merge.setEnabled(True)

    def setdisab(self):
        self.groupBox.setEnabled(False)
        self.groupBox_3.setEnabled(False)
        self.btn_clear_info.setEnabled(False)
        self.Merge_name.setEnabled(False)
        self.btn_pdf_merge.setEnabled(False)

    def pathcheck(self, in_path, out_path):  # 路径检查
        #in_path = self.lineEdit_path_in.text()
        #out_path = self.lineEdit_path_out.text()
        if not os.path.exists(in_path):
            print("输入文件夹不存在，请重新选择！")
            self.err = QMessageBox.warning(
                self, "警告", "输入文件夹不存在，请重新选择！", QMessageBox.Ok)
            if self.err == QMessageBox.Ok:
                self.restart_s()
                return
        else:
            self.path_ok = 1
        if not os.path.exists(out_path):
            print("输出文件夹不存在，即将新建！")
            os.makedirs(out_path)
            print("成功创建文件夹：", out_path)

    def progress_start(slef, num_max):
        strs = str("总共需要处理" + str(num_max) + "个图片")
        print(strs)

        strs = str("批量处理开始......")
        print(strs)

    def progress_fineshed(self, num):
        strs = str("批量处理结束################################")
        print(strs)
        hwnd = "总共完成" + str(num) + "个图像处理"
        print(hwnd)
        hfjt = QMessageBox.information(self, "提示", str(hwnd), QMessageBox.Ok)
        if hfjt == QMessageBox.Ok:
            self.step = 0
            self.restart_s()
            self.progressBar.setValue(self.step)
            QApplication.processEvents()
            self.setenab()

    def centr1_Image(self):  # 图片居中留边-单文件
        file_path = self.file_name.text()
        out_path = self.lineEdit_path_out.text()
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        print("程序开始")
        print("正在加载图片文件，请稍等。。。。。。")
        bg_zoomx = int(self.bg_zoomx.text())
        bg_zoomy = int(self.bg_zoomy.text())
        imgType_list = {
            '.jpg',
            '.bmp',
            '.png',
            '.jpeg',
            '.rgb',
            '.tif',
            '.pgm',
            '.tiff',
            '.webp',
            '.gif'}
        file_name, file_extension = os.path.splitext(file_path)
        filename = os.path.basename(file_path)
        image_output_fullname = out_path + '/' + filename
        if file_extension in imgType_list:
            img = Image.open(file_path)
            new_img = Image.new("RGB", (bg_zoomx, bg_zoomy), (self.r, self.g, self.b))
            img_width = img.width
            img_height = img.height
            x = (int(self.bg_zoomx.text()) - img_width) / 2.0
            y = (int(self.bg_zoomy.text()) - img_height) / 2.0
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            new_img.paste(img, (int(x), int(y)))

            new_img.save(image_output_fullname)

            # print('{0} crop done.'.format(each_image))
            strs = str(filename + " done")
            print(strs)

            hwnd = file_path+"图像处理完成"
            print(hwnd)
            hfjt = QMessageBox.information(self, "提示", str(hwnd), QMessageBox.Ok)
            if hfjt == QMessageBox.Ok:
                self.step = 0
                self.restart_s()
                self.progressBar.setValue(self.step)
                QApplication.processEvents()
                self.setenab()
        else:
            print("文件格式错误，请检查！！！")
            QMessageBox.warning(self, "警告", "文件格式错误，请检查！！！", QMessageBox.Ok)
    def centr_Image(self): #图片居中留边-批量
        in_path = self.lineEdit_path_in.text()
        out_path = self.lineEdit_path_out.text()
        bg_zoomx = int(self.bg_zoomx.text())
        bg_zoomy = int(self.bg_zoomy.text())
        num = 0
        # 检查输入文件夹是否存在
        self.pathcheck(in_path, out_path)
        if self.path_ok == 0:
            return
        else:
            self.samepath(in_path, out_path)  # 输入输出同路径处理
            out_path = self.lineEdit_path_out.text()
            print("输出路径确认：", out_path)

        num_max = 0
        for each_image in os.listdir(in_path):
            # 每个图像全路径
            image_input_fullname = in_path + '/' + each_image
            if not os.path.isdir(image_input_fullname):
                num_max += 1
        self.max_step = num_max
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(self.max_step)
        self.progress_start(num_max)  # 程序开始
        startTime_batch = datetime.datetime.now()  # 开始时间
        for each_image in os.listdir(in_path):
            image_input_fullname = in_path + '/' + each_image
            image_output_fullname = out_path + '/' + each_image
            if not os.path.isdir(image_input_fullname):
                img = Image.open(image_input_fullname)
                new_img = Image.new("RGB", (bg_zoomx,bg_zoomy), (self.r, self.g, self.b))
                img_width = img.width
                img_height = img.height
                x = (int(self.bg_zoomx.text())-img_width)/2.0
                y = (int(self.bg_zoomy.text())-img_height)/2.0
                if x<0:
                    x=0
                if y<0:
                    y=0
                new_img.paste(img,(int(x),int(y)))

                new_img.save(image_output_fullname)

                # print('{0} crop done.'.format(each_image))
                strs = str(each_image + " done")
                print(strs)
                num += 1
                time.sleep(0.01)
                self.processbar_ok()
                #else:
                    #pass
            else:
                pass
        endTime_batch = datetime.datetime.now()  # 开始时间
        print('批处理总耗时=', (endTime_batch - startTime_batch).seconds, "秒")
        self.progress_fineshed(num)  # 程序完成
    def batchImage(self, type_value):
        in_path = self.lineEdit_path_in.text()
        out_path = self.lineEdit_path_out.text()

        BOX_LEFT = int(self.lineEdit_x0.text())
        BOX_UP = int(self.lineEdit_y0.text())
        BOX_RIGHT = int(self.lineEdit_x1.text())
        BOX_DOWN = int(self.lineEdit_y1.text())
        #print(in_path, out_path, BOX_LEFT, BOX_UP, BOX_RIGHT, BOX_DOWN)

        num = 0
        # 检查输入文件夹是否存在
        self.pathcheck(in_path, out_path)
        if self.path_ok == 0:
            return
        else:

            self.samepath(in_path, out_path)  # 输入输出同路径处理
            out_path = self.lineEdit_path_out.text()
            print("输出路径确认：", out_path)
            if self.checkBox_add_New.isChecked():
                cuted = "New_"
            else:
                cuted = ""

            imgType_list = {
                'jpg',
                'bmp',
                'png',
                'jpeg',
                'rgb',
                'tif',
                'pgm',
                'tiff',
                'webp',
                'gif'}
            num_max = 0
            for each_image in os.listdir(in_path):
                # 每个图像全路径
                image_input_fullname = in_path + '/' + each_image
                if not os.path.isdir(image_input_fullname):
                    if imghdr.what(image_input_fullname) in imgType_list:
                        num_max += 1
            self.max_step = num_max
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(self.max_step)
            self.progress_start(num_max)  # 程序开始
            startTime_batch = datetime.datetime.now()  # 开始时间
            for each_image in os.listdir(in_path):
                image_input_fullname = in_path + '/' + each_image
                if not os.path.isdir(image_input_fullname):
                    if imghdr.what(image_input_fullname) in imgType_list:
                        type = "."+imghdr.what(image_input_fullname)
                        #filename = os.path.basename(image_input_fullname).split(".")[0]
                        filename = os.path.basename(image_input_fullname).rstrip(type)
                        img = Image.open(image_input_fullname)
                        oldtype = os.path.splitext(image_input_fullname)[-1]
                        newtype = oldtype  # 如果不进行格式转换，则格式不变
                        new_img = Image.new("RGB", img.size, (255, 255, 255))
                        new_img.paste(img)
                        if type_value == "cut" or (
                                self.groupBox_cut.isChecked() and type_value == "combination"):
                            box = (BOX_LEFT, BOX_UP, BOX_RIGHT, BOX_DOWN)
                            new_img = img.crop(box)
                            if self.groupBox_cut.isChecked() and type_value == "combination":
                                img = Image.new(
                                    "RGB", new_img.size, (255, 255, 255))
                                img.paste(new_img)
                        if type_value == "convert" or (
                                self.groupBox_convert.isChecked() and type_value == "combination"):
                            newtype = '.' + self.comboBox.currentText().lower()
                            new_img = Image.new(
                                "RGB", img.size, (255, 255, 255))
                            new_img.paste(img)
                            if self.groupBox_convert.isChecked() and type_value == "combination":
                                img = Image.new(
                                    "RGB", new_img.size, (255, 255, 255))
                                img.paste(new_img)
                        if type_value == "resize" or (
                                self.groupBox_rezise.isChecked() and type_value == "combination"):
                            (x0, y) = img.size
                            if self.radioButton_xs.isChecked():
                                x_s = int(self.lineEdit_zoomx.text())
                                y_s = int(self.lineEdit_zoomy.text())
                            else:
                                x_s = int(
                                    x0 * int(self.lineEdit_zoomxy.text()) / 100.0)
                                y_s = int(
                                    y * int(self.lineEdit_zoomxy.text()) / 100.0)
                            new_img = img.resize((x_s, y_s), Image.ANTIALIAS)
                            if self.groupBox_rezise.isChecked() and type_value == "combination":
                                img = Image.new(
                                    "RGB", new_img.size, (255, 255, 255))
                                img.paste(new_img)
                        if type_value == "arrs" or (
                                type_value == "combination" and self.groupBox_arrs.isChecked()):
                            matrix = 255 - np.asarray(img)  # 图像转矩阵 并反色
                            new_img = Image.fromarray(matrix)  # 矩阵转图像

                        new_img.save(
                            os.path.join(
                                out_path,
                                re.sub(
                                    "\\" +
                                    oldtype,
                                    newtype,
                                    cuted +
                                    each_image)))

                        #print('{0} crop done.'.format(each_image))
                        strs = str(filename + " done")
                        print(strs)
                        num += 1
                        time.sleep(0.01)
                        self.processbar_ok()
                    else:
                        pass
                else:
                    pass
            endTime_batch = datetime.datetime.now()  # 开始时间
            print('批处理总耗时=', (endTime_batch - startTime_batch).seconds, "秒")
            self.progress_fineshed(num)  # 程序完成
    def pdf2image3(self):

        file_path = self.file_name.text()
        dir_path = self.lineEdit_path_out.text()
        filetype =".pdf"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        print("程序开始")
        print("正在加载PDF文件，请稍等。。。。。。")
        if filetype in file_path:
        #filetype = os.path.basename(file_path).split(".")[-1]
            filename = os.path.basename(file_path).rstrip(".pdf")
            print(filename)
            zoom_x = float(self.zoomxy.text())
            zoom_y = float(self.zoomxy.text())
            rotation_angle = 0

            startTime_pdf2img = datetime.datetime.now()  # 开始时间
            pdf = fitz.open(file_path)
            self.max_step = pdf.pageCount
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(self.max_step)
            print("总共有", self.max_step, "页图像需要转换")

            print("转换开始...")
            print("输出路径：", dir_path)
            # 逐页读取PDF
            for pg in range(0, pdf.pageCount):
                page = pdf[pg]
                # 设置缩放和旋转系数
                trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotation_angle)
                pm = page.getPixmap(matrix=trans, alpha=False)
                # 开始写图像
                out_fullname = dir_path + '/' + filename + '_' + str(pg)
                pm.writePNG(out_fullname + ".png")
                print(out_fullname, "done")
                self.processbar_ok()
            pdf.close()
            endTime_pdf2img = datetime.datetime.now()  # 结束时间
            print("转换结束")
            print('pdf2img时间=', (endTime_pdf2img - startTime_pdf2img).seconds)
            reply = QMessageBox.information(None, "确认", "转换完成！", QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.step = 0
                self.progressBar.setValue(self.step)
                QApplication.processEvents()
        else:
            print("文件不存在")
            QMessageBox.warning(
                self, "警告", "输入文件不存在，请重新选择！", QMessageBox.Ok)
            return
    def pdf2image2(self):
        file_path = self.file_name.text()
        dir_path = self.lineEdit_path_out.text()
        filetype = ".pdf"
        dpi = int(self.DPI.text())
        startTime_pdf2img = datetime.datetime.now()  # 开始时间
        print("程序开始")
        print("正在加载PDF文件，请稍等。。。。。。")
        if filetype in file_path:
            type = "." + os.path.basename(file_path).split(".")[-1]
            filename = os.path.basename(file_path).rstrip(type)
            print(filename)
            with tempfile.TemporaryDirectory() as path:
                images = convert_from_path(file_path, output_folder=path , dpi=dpi)
                self.max_step = len(images)
                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(self.max_step)
                print("总共有", self.max_step, "页图像需要转换")
                print("转换开始...")
                for image in images:
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)
                    str_info = filename + "_" + f'{images.index(image)}.png'
                    image.save(dir_path + "/" + str_info, 'png')
                    print(str_info, "done")

                    self.processbar_ok()
            endTime_pdf2img = datetime.datetime.now()  # 结束时间
            print("转换结束")
            print('pdf2img时间=', (endTime_pdf2img - startTime_pdf2img).seconds)
            reply = QMessageBox.information(None, "确认", "转换完成！", QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.step = 0
                self.progressBar.setValue(self.step)
                QApplication.processEvents()
        else:
            print("文件不存在")
            QMessageBox.warning(
                self, "警告", "输入文件不存在，请重新选择！", QMessageBox.Ok)
            return

    def restart_s2(self):
        print("请先设置参数，点击《开始》开始批量合并....")
        self.Merge_name.setEnabled(True)
        self.btn_pdf_merge.setEnabled(True)

    def pathcheck2(self,in_path):  # 路径检查
        if not os.path.exists(in_path):
            print("输入文件夹不存在，请重新选择！")
            err = QMessageBox.warning(
                self, "警告", "输入文件不存在，请重新选择！", QMessageBox.Ok)
            print(err)
            if err == QMessageBox.Ok:
                self.restart_s2()
                return "ok"
        else:
            pass

    def GetFileName(self,dir_path, file_name):
        file_list = [os.path.join(dirpath, filesname) \
                     for dirpath, dirs, files in os.walk(dir_path) \
                     for filesname in files]

        for pdf_file in file_list:
            if file_name in pdf_file:
                print(pdf_file, "已被删除")
                os.remove(pdf_file)

        file_list = [os.path.join(dirpath, filesname) \
                     for dirpath, dirs, files in os.walk(dir_path) \
                     for filesname in files]

        return file_list

    def MergePDF(self,dir_path, file_name):
        output = PdfFileWriter()
        outputPages = 0
        file_list = self.GetFileName(dir_path, file_name)

        for pdf_file in file_list:
            if file_name in pdf_file:
                print(pdf_file, "已被删除")
                os.remove(pdf_file)
            print("文件：%s" % pdf_file.split('\\')[-1], end=' ')

            self.max_step = len(file_list)
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(self.max_step)
            # 读取PDF文件
            input = PdfFileReader(open(pdf_file, "rb"))
            # 获得源PDF文件中页面总数
            pageCount = input.getNumPages()
            outputPages += pageCount
            strs = str(pdf_file.split('\\')[-1]) + "页数：" + str(pageCount)
            print(strs)
            # 分别将page添加到输出output中
            for iPage in range(pageCount):
                output.addPage(input.getPage(iPage))
            self.processbar_ok()

        # 写入到目标PDF文件
        print("PDF文件正在合并，请稍等......")
        with open(os.path.join(dir_path, file_name), "wb") as outputfile:
            # 注意这里的写法和正常的上下文文件写入是相反的
            output.write(outputfile)

        strs = str("PDF文件合并完成，" + "总共合并" + str(len(file_list)) + "个PDF文件")
        print(strs)
        print("\n合并后的总页数:%d" % outputPages)
        hfjt = QMessageBox.information(self, "提示", str(strs), QMessageBox.Ok)
        if hfjt == QMessageBox.Ok:
            self.step = 0
            self.restart_s2()
            self.progressBar.setValue(self.step)
            QApplication.processEvents()
            self.setenab()

    def getText(self):
        dir_path = self.lineEdit_path_in.text()
        # 目标文件的名字
        file_name = self.Merge_name.text() + ".pdf"
        # 检查文件夹是否存在
        err = self.pathcheck2(dir_path)
        if err == "ok":
            return
        else:
            self.setdisab()
            self.MergePDF(dir_path, file_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ControlBoard()
    win.show()
    sys.exit(app.exec_())
