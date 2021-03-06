from PyQt5.QtWidgets import QMessageBox
from UI.configCamera import Ui_Dialog
from pypylon import pylon
import cv2
from PyQt5 import QtGui
from PyQt5.QtCore import *
from cameraImgs import CameraImgs
import os
from PyQt5 import QtWidgets,QtCore, QtGui
import threading

class OpenUSB(object):
    def __init__(self,mainUI):
        self.cameraoOneConfigUI = Ui_Dialog()
        self.mainUI = mainUI
        self.USBCameraList = None
        self.b_is_run = False
        self.camera = None

        self.defineConnect()

    def show(self):
        self.cameraoOneConfigUI.qDialog.show()
        self.cameraoOneConfigUI.qDialog.move(self.mainUI.MainWindow.pos().x() - self.cameraoOneConfigUI.qDialog.width(),\
                                                 self.mainUI.MainWindow.pos().y())
        self.cameraoOneConfigUI.qDialog.setWindowTitle("USB相机")
    def defineConnect(self):
        self.cameraoOneConfigUI.pushButton_show_devices.clicked.connect(self.enum_devices)
        self.cameraoOneConfigUI.pushButton_open_device.clicked.connect(self.open_device)
        self.cameraoOneConfigUI.pushButton_close_device.clicked.connect(self.close_device)
        self.cameraoOneConfigUI.pushButton_start_grap.clicked.connect(self.start_grabbing)
        self.cameraoOneConfigUI.pushButton_stop_grap.clicked.connect(self.stop_grapping)
        self.cameraoOneConfigUI.pushButton_get_parameter.clicked.connect(self.getParameter)
        self.cameraoOneConfigUI.pushButton_set_parameter.clicked.connect(self.setParameter)
        self.cameraoOneConfigUI.pushButton_load_model.clicked.connect(self.open_model_dir)

    # ch:枚举相机 | en:enum devices
    def enum_devices(self):
        self.USBCameraList = pylon.TlFactory.GetInstance().EnumerateDevices()
        for i in range(len(self.USBCameraList)):
            self.cameraoOneConfigUI.comboBox_enum_devices.addItem(self.USBCameraList[i].GetFriendlyName())
        self.cameraoOneConfigUI.lineEdit_num_of_deices.setText("{}cameras".format(len(self.USBCameraList)))

        
        #ch:打开相机 | en:open device
    def open_device(self):
        if True == self.b_is_run:
            print('Camera is Running!')
            QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', 'Camera is Running!')
            return
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(
            self.USBCameraList[self.cameraoOneConfigUI.comboBox_enum_devices.currentIndex()])
        )
        self.camera.Open()
        if  self.camera != None:
            self.b_is_run = True
        else:
            self.b_is_run = False
            QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '打开失败')
        QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '打开成功')

    def openvideo(self):
        capture = cv2.VideoCapture("./data/video_14.mp4")
        while(True):
            ret,img = capture.read()
            CameraImgs.setImg(3,img) # 图像数据存在cameraImg类中   
            cv2.waitKey(30)
    def start_grabbing(self):
        # 开始读取图像
        # if self.camera == None or self.b_is_run == False:
        #     QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '相机未打开')
        #     return
        # self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # converter = pylon.ImageFormatConverter()

        # # 转换为OpenCV的BGR彩色格式
        # converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        # converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        # while self.camera.IsGrabbing() and self.b_is_run == True:
        #     grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        #     if grabResult.GrabSucceeded():
        #         # 转换为OpenCV图像格式
        #         image = converter.Convert(grabResult)
        #         img = image.GetArray()
        #         CameraImgs.setImg(3,img) # 图像数据存在cameraImg类中
        #     grabResult.Release()

        # # 关闭相机
        # self.camera.StopGrabbing()
        t  = threading.Thread(target=self.openvideo)
        t.start()

    # ch:停止抓取 | stop grapping
    def stop_grapping(self):
        self.camera.StopGrabbing()
        self.mainUI.label_img_one.clear()

    # ch:关闭设备 | Close device
    def close_device(self):
        self.camera.Close()
        self.b_is_run = False
        QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '关闭成功')

    def getParameter(self):
        if self.camera == None:
            QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '相机未打开')
            return
        self.cameraoOneConfigUI.lineEdit_frame_rate.setText(str(self.camera.AcquisitionFrameRate.Value))
        self.cameraoOneConfigUI.lineEdit_exposeur_time.setText(str(self.camera.ExposureTime.Value))
        self.cameraoOneConfigUI.lineEdit_gain.setText(str(self.camera.Gain.Value))

    def setParameter(self):
        if self.camera == None:
            QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', '相机未打开')
            return
        gain = float(self.cameraoOneConfigUI.lineEdit_gain.text())
        if  gain > 36.0:
            QMessageBox.about(self.cameraoOneConfigUI.qDialog, '提示', 'Gain不可大于36.0，帮您设成36.0')
            gain = 36.0

        self.camera.ExposureTime.SetValue(float(self.cameraoOneConfigUI.lineEdit_exposeur_time.text()))
        self.camera.AcquisitionFrameRate.SetValue(float(self.cameraoOneConfigUI.lineEdit_frame_rate.text()))
        self.camera.Gain.SetValue(gain)

    def showImg(self,img,label):
        res = self.img_resize(img, label)
        img2 = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)  # opencv读取的bgr格式图片转换成rgb格式
        _image = QtGui.QImage(img2[:], img2.shape[1], img2.shape[0], img2.shape[1] * 3,
                              QtGui.QImage.Format_RGB888)  # pyqt5转换成自己能放的图片格式
        jpg_out = QtGui.QPixmap(_image)  # 转换成QPixmap
        label.setPixmap(jpg_out)  # 设置图片显示
        label.setAlignment(Qt.AlignCenter)

    def img_resize(self,image,label):
        '''
        :param image: cv2读取的mat图片
        :param label: 显示在那个label
        :return: 返回处理后适合显示的图片
        '''
        if image is None:
            return
        height, width = image.shape[0], image.shape[1]
        # 设置新的图片分辨率框架
        width_new = label.width()
        height_new = label.height()
        # 判断图片的长宽比率
        if width / height >= width_new / height_new:
            img_new = cv2.resize(image, (width_new, int(height * width_new / width)))
        else:
            img_new = cv2.resize(image, (int(width * height_new / height), height_new))
        return img_new
        
    def is_chinese(self,string):
        """
        检查整个字符串是否包含中文
        :param string: 需要检查的字符串
        :return: bool
        """
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True

        return False


    #添加模型
    def open_model_dir(self):
        DefaultImDir=os.getcwd()
        Model_Dir = QtWidgets.QFileDialog.getExistingDirectory(None,"Paddle -- Open_Model_Dir", DefaultImDir)
        if Model_Dir != '':
            if self.is_chinese(Model_Dir):
                print("有中文")
                warning_box=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, '警告', '暂不支持含有中文的路径!')
                warning_box.exec_()
            else:
                f = open(r'./data/USBCamera_model_dir_paths.txt', 'w', encoding='utf-8')
                f.flush()
                f.write(Model_Dir)
                f.close
                #print(self.List)


    # 加载置信度|矩形框|像素设定
    def load_confidence_set_pix(self):
        DefaultImDir=os.getcwd()
        TxtDir = QtWidgets.QFileDialog.getExistingDirectory(None,"Paddle -- Get_Confidence_Set_Pix", DefaultImDir)
        if TxtDir != '':
            path = glob.glob(os.path.join(TxtDir, '*.json'))
            windows_path = path[0].replace('\\','/')
            print(windows_path)
            with open(windows_path,'r',encoding='utf8')as fp:
                confidence_set_pix = json.load(fp)
            class_num = len(confidence_set_pix["confidence_set_pix"])

        for i in range(class_num):
            if float(confidence_set_pix["confidence_set_pix"][i]["confidence"]) >= 1 or float(confidence_set_pix["confidence_set_pix"][i]["confidence"]) <= 0:
                #warning = 
                warning_box=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, '警告', '请确认 id=%d的类别 置信度为在[0,1]区间内的任意浮点数!'%i)
                warning_box.exec_()
        
        else:
            return confidence_set_pix["confidence_set_pix"]
