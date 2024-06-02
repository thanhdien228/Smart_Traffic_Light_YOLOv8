import sys
import time
import threading
import serial
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QFileDialog, QPushButton
from PyQt5.QtGui import QPixmap, QFont, QPainter, QImage
from PyQt5.QtCore import Qt, QTimer
import cv2
import pandas as pd
from ultralytics import YOLO
import cvzone
import math

# Load YOLO model for object detection
model = YOLO('yolov8s.pt')

class Tracker:
    def __init__(self):
        self.center_points = {}  # Store the center points of objects
        self.id_count = 0  # Count the number of tracked objects

    def update(self, objects_rect):
        objects_bbs_ids = []

        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2  # Calculate center x
            cy = (y + y + h) // 2  # Calculate center y

            same_object_detected = False
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])  # Calculate Euclidean distance

                if dist < 35:
                    self.center_points[id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, id])
                    same_object_detected = True
                    break

            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1

        new_center_points = {obj_bb_id[4]: self.center_points[obj_bb_id[4]] for obj_bb_id in objects_bbs_ids}
        self.center_points = new_center_points
        return objects_bbs_ids

my_file = open("coco.txt", "r")
data = my_file.read()
class_list = data.split("\n")

cy1 = 320
offset = 6
tracker1 = Tracker()
tracker2 = Tracker()

# defaultGreen = {0: 14, 1: 14, 2: 14, 3: 14}
# defaultRed = 20
# defaultYellow = 3

signals = []
noOfSignals = 4

# Different timing sets based on traffic density
timing_sets = {
    1: {'red': 14, 'green': 24, 'yellow': 3},
    2: {'red': 24, 'green': 35, 'yellow': 3},
    3: {'red': 75, 'green': 83, 'yellow': 3},
    4: {'red': 23, 'green': 20, 'yellow': 3},
}

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        self.blinking_yellow = 6  # 6 seconds of blinking yellow for all signals


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.black = Qt.black
        self.white = Qt.white
        self.screenWidth = 1400
        self.screenHeight = 900

        self.ser = serial.Serial('COM6', 115200)

        self.vehicle_second1 = 0
        self.vehicle_second2 = 0
        self.current_time = 0
        self.time_set = 4
        self.choice = 0
        self.end_video = False
        self.cycle_complete = True  # To check if the current signal cycle is complete
        self.ser_data_sent = False

        self.initUI()

    def initUI(self):
        self.setWindowTitle("SIMULATION")
        self.setGeometry(0, 0, self.screenWidth, self.screenHeight)

        self.background = QLabel(self)
        self.background.setPixmap(QPixmap('images/intersection.png'))

        self.redSignal = QPixmap('images/signals/red.png')
        self.yellowSignal = QPixmap('images/signals/yellow.png')
        self.greenSignal = QPixmap('images/signals/green.png')

        self.font = QFont()
        self.font.setPointSize(15)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.updateSignals)
        self.updateTimer.start(1000)

        self.startButton = QPushButton('Start', self)
        self.startButton.setGeometry(650, 300, 70, 40)
        self.startButton.clicked.connect(self.startVideos)

        self.endButton = QPushButton('End', self)
        self.endButton.setGeometry(650, 500, 70, 40)
        self.endButton.clicked.connect(self.endVideos) 

        self.selectMainVideoButton = QPushButton('Video 1', self)
        self.selectMainVideoButton.setGeometry(20, 10, 70, 40)
        self.selectMainVideoButton.clicked.connect(self.selectMainVideo)

        self.mainVideoLabel = QLabel(self)
        self.mainVideoLabel.setGeometry(100, 5, 320, 320)

        self.selectParallelVideoButton = QPushButton('Video 2', self)
        self.selectParallelVideoButton.setGeometry(20, 550, 70, 40)
        self.selectParallelVideoButton.clicked.connect(self.selectParallelVideo)

        self.parallelVideoLabel = QLabel(self)
        self.parallelVideoLabel.setGeometry(100, 550, 320, 320)

        self.mainVideoCounterLabel = QLabel(self)
        self.mainVideoCounterLabel.setGeometry(440, 50, 200, 40)

        self.parallelVideoCounterLabel = QLabel(self)
        self.parallelVideoCounterLabel.setGeometry(440, 590, 200, 40)

        self.labelVehicleSecond1 = QLabel(self)
        self.labelVehicleSecond1.setGeometry(440, 10, 200, 40)

        self.labelVehicleSecond2 = QLabel(self)
        self.labelVehicleSecond2.setGeometry(440, 550, 200, 40)

        self.mainVideoTimerLabel = QLabel(self)
        self.mainVideoTimerLabel.setGeometry(440, 30, 200, 40)

        self.parallelVideoTimerLabel = QLabel(self)
        self.parallelVideoTimerLabel.setGeometry(440, 570, 200, 40)

        self.resultTraffic = QLabel(self)
        self.resultTraffic.setGeometry(620, 400, 200, 40)

        self.EWLabel = QLabel(self)
        self.EWLabel.setGeometry(100, 450, 200, 40)
        self.EWLabel.setText('ĐIỆN BIÊN PHỦ - ĐÔNG TÂY')

        self.SNLabel = QLabel(self)
        self.SNLabel.setGeometry(630, 100, 200, 40)
        self.SNLabel.setText('XÔ VIẾT NGHỆ TĨNH\n BẮC NAM')


        self.show()

    def setSignalTiming(self, timing_set, choice):
        global signals
        timing = timing_sets[timing_set]

        # Đặt thời gian và màu sắc cho tất cả các tín hiệu dựa trên sự lựa chọn
        for i in range(noOfSignals):
            if choice == 0:  # Choice 0: tín hiệu 0 và 2 hoạt động, tín hiệu 1 và 3 chờ
                if i in [0, 2]:
                    signals[i].red = timing['red']
                    signals[i].yellow = timing['yellow']
                    signals[i].green = timing['green']
                else:
                    signals[i].red = timing['green'] + timing['yellow'] + 1
                    signals[i].yellow = timing['yellow']
                    signals[i].green = timing['red'] - timing['yellow']

            elif choice == 1:  # Choice 1: tín hiệu 1 và 3 hoạt động, tín hiệu 0 và 2 chờ
                if i in [1, 3]:
                    signals[i].red = timing['red']
                    signals[i].yellow = timing['yellow']
                    signals[i].green = timing['green']
                else:
                    signals[i].red = timing['green'] + timing['yellow'] + 1
                    signals[i].yellow = timing['yellow']
                    signals[i].green = timing['red'] - timing['yellow'] 

    def selectMainVideo(self):
        self.mainVideoFile = self.getVideoFile()

    def selectParallelVideo(self):
        self.parallelVideoFile = self.getVideoFile()

    def getVideoFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "All Files (*);;MP4 Files (*.mp4)", options=options)
        return fileName

    def startVideos(self):
        if hasattr(self, 'mainVideoFile') and hasattr(self, 'parallelVideoFile'):
            self.end_video = False
            threading.Thread(target=self.displayVideo, args=(
                self.mainVideoFile, self.mainVideoLabel, self.mainVideoCounterLabel, self.mainVideoTimerLabel,
                self.labelVehicleSecond1, tracker1, True)).start()
            threading.Thread(target=self.displayVideo, args=(
                self.parallelVideoFile, self.parallelVideoLabel, self.parallelVideoCounterLabel,
                self.parallelVideoTimerLabel, self.labelVehicleSecond2, tracker2, False)).start()

    def endVideos(self):
        self.end_video = True
        self.resultTraffic.setText('')
        self.ser_data_sent = False

    def displayVideo(self, fileName, videoLabel, counterLabel, timerLabel, vehicleSecond, tracker, isMainVideo):
        count = 0
        counter1 = []
        counter2 = []
        start_time = time.time()
        cap = cv2.VideoCapture(fileName)
        width = int(videoLabel.frameGeometry().width())
        height = int(videoLabel.frameGeometry().height())
        fps = cap.get(cv2.CAP_PROP_FPS)

        while self.end_video == False:
            ret, frame = cap.read()
            if not ret:
                break

            count += 1


            results = model.predict(frame)
            a = results[0].boxes.data
            px = pd.DataFrame(a.cpu()).astype("float")

            list1 = []
            car = []
            for index, row in px.iterrows():
                x1 = int(row[0])
                y1 = int(row[1])
                x2 = int(row[2])
                y2 = int(row[3])
                d = int(row[5])
                c = class_list[d]
                if c in ['car', 'motorcycle', 'truck']:
                    list1.append([x1, y1, x2, y2])
                    car.append(c)

            bbox1_idx = tracker.update(list1)
            for bbox1 in bbox1_idx:
                for i in car:
                    x3, y3, x4, y4, id1 = bbox1
                    cxm = int(x3 + x4) // 2
                    cym = int(y3 + y4) // 2
                    if cym < (cy1 + offset) and cym > (cy1 - offset):
                        cv2.circle(frame, (cxm, cym), 4, (0, 255, 0), -1)
                        cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 1)
                        cvzone.putTextRect(frame, f'{id1}', (x3, y3), 1, 1)
                        if counter1.count(id1) == 0:
                            counter1.append(id1)
                            counter2.append(id1)

            cv2.line(frame, (0, cy1), (frame.shape[1], cy1), (0, 0, 255), 2)

            vehicle_counter = len(counter1)
            vehicle_second = len(counter2)

            self.current_time = int(time.time() - start_time)
            if self.current_time == 60:
                if isMainVideo:
                    self.vehicle_second1 = len(counter2)
                else:
                    self.vehicle_second2 = len(counter2)

            elif self.current_time > 60:
                start_time = time.time()
                vehicle_second = 0
                counter2 = []
            
            counterLabel.setText(f'Vehicle: {vehicle_counter}')
            vehicleSecond.setText(f'Vehicle/minute: {vehicle_second}')
            timerLabel.setText(f'Time: {self.current_time}')

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (width, height))
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            videoLabel.setPixmap(pixmap)
            time.sleep(1 / fps)

            # if cv2.waitKey(1) & (self.end_video == True): 
            #     break
    
        cap.release()
        cv2.destroyAllWindows()

    def updateSignals(self):
        # Tự động chọn thời gian dựa trên số lượng xe
        if self.current_time >= 60:
            # if self.vehicle_second1 - self.vehicle_second2 <= 5 & self.vehicle_second1 - self.vehicle_second2>= -5:
            #     self.time_set = 4
            #     self.choice = 0
            #     self.resultTraffic.setText('Lưu lượng giao thông 2 hướng \nxấp xỉ bằng nhau')
            if self.vehicle_second1 > self.vehicle_second2:
                self.choice = 0
                if self.vehicle_second1 <= 50:
                    self.time_set = 1
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Bắc_Nam mức 1')
                elif 50 < self.vehicle_second1 <= 100:
                    self.time_set = 2
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Bắc_Nam mức 2')
                else:
                    self.time_set = 3
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Bắc_Nam mức 3')
            elif self.vehicle_second1 <= self.vehicle_second2:
                self.choice = 1
                if self.vehicle_second2 <= 50:
                    self.time_set = 1
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Đông_Tây mức 1')
                elif 50 < self.vehicle_second2 <= 100:
                    self.time_set = 2
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Đông_Tây mức 2')
                else:
                    self.time_set = 3
                    self.resultTraffic.setText('Lưu lượng giao thông \nhướng Đông_Tây mức 3')
           
        if self.cycle_complete:
            self.updateCurrentCycle()

        #self.sendDataToSerial()
        self.update()

    def updateCurrentCycle(self):
        currentSignal0 = signals[0]
        currentSignal2 = signals[2]
        otherSignal1 = signals[1]
        otherSignal3 = signals[3]

        # Handle the blinking yellow phase
        if currentSignal0.blinking_yellow > 0:
            for signal in signals:
                signal.blinking_yellow -= 1
            self.update()
            return
        if self.choice == 0:
            # Đèn 0 và 2
            if currentSignal0.green > 0:
                currentSignal0.green -= 1
                currentSignal2.green -= 1
            elif currentSignal0.yellow > 0:
                currentSignal0.yellow -= 1
                currentSignal2.yellow -= 1
            elif currentSignal0.red > 0:
                currentSignal0.red -= 1
                currentSignal2.red -= 1
            else:
                self.setSignalTiming(self.time_set, self.choice)
                self.ser_data_sent = False

            # Đèn 1 và 3
            if otherSignal1.red > 0:
                otherSignal1.red -= 1
                otherSignal3.red -= 1
            elif otherSignal1.green > 0:
                otherSignal1.green -= 1
                otherSignal3.green -= 1
            elif otherSignal1.yellow > 0:
                otherSignal1.yellow -= 1
                otherSignal3.yellow -= 1
            else:
                self.setSignalTiming(self.time_set, self.choice)
                self.ser_data_sent = False
                if (
                        otherSignal1.yellow == 0 and otherSignal3.yellow == 0 and currentSignal0.red == 0 and currentSignal2.red == 0):
                    self.cycle_complete = False
        elif self.choice == 1:
            # Đèn 1 và 3
            if otherSignal1.green > 0:
                otherSignal1.green -= 1
                otherSignal3.green -= 1
            elif otherSignal1.yellow > 0:
                otherSignal1.yellow -= 1
                otherSignal3.yellow -= 1
            elif otherSignal1.red > 0:
                otherSignal1.red -= 1
                otherSignal3.red -= 1
            else:
                self.setSignalTiming(self.time_set, self.choice)
                self.cycle_complete = False
                self.ser_data_sent = False

            # Đèn 0 và 2
            if currentSignal0.red > 0:
                currentSignal0.red -= 1
                currentSignal2.red -= 1
            elif currentSignal0.green > 0:
                currentSignal0.green -= 1
                currentSignal2.green -= 1
            elif currentSignal0.yellow > 0:
                currentSignal0.yellow -= 1
                currentSignal2.yellow -= 1
            else:
                self.setSignalTiming(self.time_set, self.choice)
                self.ser_data_sent = False
                self.cycle_complete = False

        # red_time_1 = signals[0].red
        # yellow_time_1 = signals[0].yellow
        # green_time_1 = signals[0].green

        # red_time_2 = signals[1].red
        # yellow_time_2 = signals[1].yellow
        # green_time_2 = signals[1].green
        # data_to_send = f"{red_time_1},{yellow_time_1},{green_time_1};{red_time_2},{yellow_time_2},{green_time_2}\n"
        # self.ser.write(data_to_send.encode())

        # self.cycle_complete = True

        if not self.ser_data_sent:
            self.sendDataToSerial()
            self.ser_data_sent = True  # Đặt biến kiểm tra thành True sau khi dữ liệu đã được gửi
        self.cycle_complete = True
        self.update()
        
    def sendDataToSerial(self):
        if not self.ser_data_sent:
            red_time_1 = signals[0].red
            yellow_time_1 = signals[0].yellow
            green_time_1 = signals[0].green

            red_time_2 = signals[1].red
            yellow_time_2 = signals[1].yellow
            green_time_2 = signals[1].green
            time.sleep(1)
            data_to_send = f"{red_time_1},{yellow_time_1},{green_time_1};{red_time_2},{yellow_time_2},{green_time_2},{self.choice}\n"
            self.ser.write(data_to_send.encode())
            print(data_to_send)

            self.ser_data_sent = True  # Đặt biến kiểm tra thành True sau khi dữ liệu đã được gửi

            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.background.pixmap())
        signal_positions = [(550, 230), (self.screenWidth - 600, 330),
                            (self.screenWidth - 610, self.screenHeight - 350), (550, self.screenHeight - 470)]

        for i in range(noOfSignals):
            currentSignal = signals[i]
            if currentSignal.blinking_yellow > 0:
                painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.yellowSignal)
                currentSignal.signalText = str(currentSignal.blinking_yellow)
            elif self.choice == 0:
                if i == 0 or i == 2:
                    if currentSignal.green > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.greenSignal)
                        currentSignal.signalText = str(currentSignal.green)
                    elif currentSignal.yellow > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.yellowSignal)
                        currentSignal.signalText = str(currentSignal.yellow)
                    else:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.redSignal)
                        currentSignal.signalText = str(currentSignal.red)
                else:
                    if currentSignal.red > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.redSignal)
                        currentSignal.signalText = str(currentSignal.red)
                    elif currentSignal.green > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.greenSignal)
                        currentSignal.signalText = str(currentSignal.green)
                    else:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.yellowSignal)
                        currentSignal.signalText = str(currentSignal.yellow)

            elif self.choice == 1:
                if i == 1 or i == 3:
                    if currentSignal.red > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.redSignal)
                        currentSignal.signalText = str(currentSignal.red)
                    elif currentSignal.green > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.greenSignal)
                        currentSignal.signalText = str(currentSignal.green)
                    else:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.yellowSignal)
                        currentSignal.signalText = str(currentSignal.yellow)                
                else:
                    if currentSignal.green > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.greenSignal)
                        currentSignal.signalText = str(currentSignal.green)
                    elif currentSignal.yellow > 0:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.yellowSignal)
                        currentSignal.signalText = str(currentSignal.yellow)
                    else:
                        painter.drawPixmap(signal_positions[i][0], signal_positions[i][1], self.redSignal)
                        currentSignal.signalText = str(currentSignal.red)
            painter.setFont(self.font)
            painter.setPen(Qt.white)
            painter.drawText(signal_positions[i][0], signal_positions[i][1] - 10, currentSignal.signalText)


def initialize():  
    global signals
    for i in range(noOfSignals):
        # ts = TrafficSignal(timing_sets[4]['red'] , timing_sets[4]['yellow'], timing_sets[4]['red'] - timing_sets[4]['yellow'] )
        ts = TrafficSignal(0,0,0)
        signals.append(ts)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    initialize()
    main = Main()
    sys.exit(app.exec_())
