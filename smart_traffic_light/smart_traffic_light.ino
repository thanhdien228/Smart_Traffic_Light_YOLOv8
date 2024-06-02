// Chân kết nối với IC 74HC595 thứ nhất
const int latchPin1 = 4;  // ST_CP của IC 74HC595 thứ nhất
const int clockPin = 2;   // SH_CP của IC 74HC595 thứ nhất và thứ hai
const int dataPin1 = 3;   // DS của IC 74HC595 thứ nhất

// Chân kết nối với IC 74HC595 thứ hai
const int latchPin2 = 6;  // ST_CP của IC 74HC595 thứ hai
const int dataPin2 = 5;   // DS của IC 74HC595 thứ hai

// Chân kết nối đèn tín hiệu
#define R1 A0
#define Y1 A1
#define G1 A2
#define R2 A3
#define Y2 A4
#define G2 A5

// Chân chọn chữ số cho các LED 7 đoạn
const int digit1SelectPin = 8;  // Chọn chữ số hàng chục của LED 7 đoạn thứ nhất
const int digit2SelectPin = 9;  // Chọn chữ số hàng đơn vị của LED 7 đoạn thứ nhất
const int digit3SelectPin = 10; // Chọn chữ số hàng chục của LED 7 đoạn thứ hai
const int digit4SelectPin = 11; // Chọn chữ số hàng đơn vị của LED 7 đoạn thứ hai

unsigned long previousMillis1 = 0;
unsigned long previousMillis2 = 0;
unsigned long startMillis1 = 0;
unsigned long startMillis2 = 0;
unsigned long lastSerialReceivedTime;
const long serialTimeout = 120000;

int state1 = 0;
int state2 = 0;

int red_time_1 = 23, yellow_time_1 = 3, green_time_1 = 20;
int red_time_2 = 23, yellow_time_2 = 3, green_time_2 = 20;
int choice = 0;

bool serialDataReceived = false;

const byte digitCode[10] = {0xFC, 0x60, 0xDA, 0xF2, 0x66, 0xB6, 0xBE, 0xE0, 0xFE, 0xF6};

void setup() {
  Serial.begin(115200);
  pinMode(latchPin1, OUTPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(dataPin1, OUTPUT);
  pinMode(latchPin2, OUTPUT);
  pinMode(dataPin2, OUTPUT);
  pinMode(R1, OUTPUT);
  pinMode(Y1, OUTPUT);
  pinMode(G1, OUTPUT);
  pinMode(R2, OUTPUT);
  pinMode(Y2, OUTPUT);
  pinMode(G2, OUTPUT);
  pinMode(digit1SelectPin, OUTPUT);
  pinMode(digit2SelectPin, OUTPUT);
  pinMode(digit3SelectPin, OUTPUT);
  pinMode(digit4SelectPin, OUTPUT);

  flashLights();
}

void flashLights() {
  for (int i = 3; i > 0; i--) {
    // Hiển thị số i trên LED 7 đoạn
    digitalWrite(digit1SelectPin, LOW);
    digitalWrite(digit3SelectPin, LOW);
    displayNumber(i, i, latchPin1, dataPin1, clockPin, latchPin2, dataPin2, clockPin);

    digitalWrite(Y1, HIGH);
    digitalWrite(Y2, HIGH);
    delay(1000);  // Đợi 1 giây

    digitalWrite(Y1, LOW);
    digitalWrite(Y2, LOW);
    delay(1000);  // Đợi 1 giây
  
  }
}

void controlLightsLane1() {
  unsigned long currentMillis = millis();
  if(choice == 0){
    switch (state1) {
      case 0: // Green
        digitalWrite(R1, LOW);
        digitalWrite(Y1, LOW);
        digitalWrite(G1, HIGH);
        if ((currentMillis - startMillis1) / 1000 >= green_time_1) {
          state1 = 1;
          startMillis1 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 1: // Yellow
        digitalWrite(R1, LOW);
        digitalWrite(Y1, HIGH);
        digitalWrite(G1, LOW);
        if ((currentMillis - startMillis1) / 1000 >= yellow_time_1) {
          state1 = 2;
          startMillis1 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 2: // Red
        digitalWrite(R1, HIGH);
        digitalWrite(Y1, LOW);
        digitalWrite(G1, LOW);
        if ((currentMillis - startMillis1) / 1000 >= red_time_1) {
          state1 = 0;
          startMillis1 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
    }    
  }else if(choice == 1){
    switch (state1) {
      case 0: // Red
        digitalWrite(R1, HIGH);
        digitalWrite(Y1, LOW);
        digitalWrite(G1, LOW);
        if ((currentMillis - startMillis1) / 1000 >= red_time_1) {
          state1 = 1;
          startMillis1 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 1: // Green
        digitalWrite(R1, LOW);
        digitalWrite(Y1, LOW);
        digitalWrite(G1, HIGH);
        if ((currentMillis - startMillis1) / 1000 >= green_time_1) {
          state1 = 2;
          startMillis1= currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 2: // Yellow
        digitalWrite(R1, LOW);
        digitalWrite(Y1, HIGH);
        digitalWrite(G1, LOW);
        if ((currentMillis - startMillis1) / 1000 >= yellow_time_1) {
          state1 = 0;
          startMillis1 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
    }    
  }

}

void controlLightsLane2() {
  unsigned long currentMillis = millis();
  if(choice == 0){
    switch (state2) {
      case 0: // Red
        digitalWrite(R2, HIGH);
        digitalWrite(Y2, LOW);
        digitalWrite(G2, LOW);
        if ((currentMillis - startMillis2) / 1000 >= red_time_2) {
          state2 = 1;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 1: // Green
        digitalWrite(R2, LOW);
        digitalWrite(Y2, LOW);
        digitalWrite(G2, HIGH);
        if ((currentMillis - startMillis2) / 1000 >= green_time_2) {
          state2 = 2;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 2: // Yellow
        digitalWrite(R2, LOW);
        digitalWrite(Y2, HIGH);
        digitalWrite(G2, LOW);
        if ((currentMillis - startMillis2) / 1000 >= yellow_time_2) {
          state2 = 0;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
    }    
  }else if(choice == 1){
    switch (state2) {
      case 0: // Green
        digitalWrite(R2, LOW);
        digitalWrite(Y2, LOW);
        digitalWrite(G2, HIGH);
        if ((currentMillis - startMillis2) / 1000 >= green_time_2) {
          state2 = 1;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 1: // Yellow
        digitalWrite(R2, LOW);
        digitalWrite(Y2, HIGH);
        digitalWrite(G2, LOW);
        if ((currentMillis - startMillis1) / 1000 >= yellow_time_2) {
          state2 = 2;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
      case 2: // Red
        digitalWrite(R2, HIGH);
        digitalWrite(Y2, LOW);
        digitalWrite(G2, LOW);
        if ((currentMillis - startMillis2) / 1000 >= red_time_2) {
          state2 = 0;
          startMillis2 = currentMillis; // Cập nhật thời gian bắt đầu mới
        }
        break;
    } 
  }
}

void clearDisplay(int latchPin, int dataPin, int clockPin) {
  digitalWrite(latchPin, LOW);
  shiftOut(dataPin, clockPin, LSBFIRST, B00000000); // Gửi một byte không có bit nào được đặt
  digitalWrite(latchPin, HIGH);
}

void displayNumber(int num1, int num2, int latchPin1, int dataPin1, int clockPin1, int latchPin2, int dataPin2, int clockPin2) {
  clearDisplay(latchPin1, dataPin1, clockPin1);
  clearDisplay(latchPin2, dataPin2, clockPin2);

  int tens_1 = num1 / 10;    // Chữ số hàng chục LED 1
  int units_1 = num1 % 10;   // Chữ số hàng đơn vị LED 1
  int tens_2 = num2 / 10;    // Chữ số hàng chục LED 2
  int units_2 = num2 % 10;   // Chữ số hàng đơn vị LED 2

  // Hiển thị chữ số hàng chục LED 1 nếu khác 0, ngược lại ẩn đi
  if (tens_1 != 0) {
    digitalWrite(digit1SelectPin, HIGH);
    digitalWrite(digit2SelectPin, LOW);
    digitalWrite(latchPin1, LOW);
    shiftOut(dataPin1, clockPin1, LSBFIRST, digitCode[tens_1]);
    digitalWrite(latchPin1, HIGH);
    delay(5);
  }

  // Hiển thị chữ số hàng đơn vị LED 1
  digitalWrite(digit1SelectPin, LOW);
  digitalWrite(digit2SelectPin, HIGH);
  digitalWrite(latchPin1, LOW);
  shiftOut(dataPin1, clockPin1, LSBFIRST, digitCode[units_1]);
  digitalWrite(latchPin1, HIGH);
  delay(5);

  // Hiển thị chữ số hàng chục LED 2 nếu khác 0, ngược lại ẩn đi
  if (tens_2 != 0) {
    digitalWrite(digit3SelectPin, HIGH);
    digitalWrite(digit4SelectPin, LOW);
    digitalWrite(latchPin2, LOW);
    shiftOut(dataPin2, clockPin2, LSBFIRST, digitCode[tens_2]);
    digitalWrite(latchPin2, HIGH);
    delay(5);
  }

  // Hiển thị chữ số hàng đơn vị LED 2
  digitalWrite(digit3SelectPin, LOW);
  digitalWrite(digit4SelectPin, HIGH);
  digitalWrite(latchPin2, LOW);
  shiftOut(dataPin2, clockPin2, LSBFIRST, digitCode[units_2]);
  digitalWrite(latchPin2, HIGH);
  delay(5);
}

void loop() {
  unsigned long currentMillis = millis();

  if (Serial.available() > 0) {
    lastSerialReceivedTime = currentMillis;
    String data = Serial.readStringUntil('\n');
    if(data != "") { //Nếu có dữ liệu nhận được
      serialDataReceived = true;
      //Ép kiểu số nguyên cho các dữ liệu
      sscanf(data.c_str(), "%d,%d,%d;%d,%d,%d,%d", &red_time_1, &yellow_time_1, &green_time_1, &red_time_2, &yellow_time_2, &green_time_2, &choice);
      startMillis1 = millis();
      startMillis2 = millis();
      previousMillis1 = millis();
      previousMillis2 = millis();
      state1 = 0;
      state2 = 0;
    }
  }

  if (currentMillis - lastSerialReceivedTime >= serialTimeout) {
    serialDataReceived = false;
  }

  if(choice == 0){
     // Tính thời gian còn lại cho mỗi màu đèn của làn 1
    int remainingTime1 = 0;
    switch (state1) {
      case 0:
        remainingTime1 = green_time_1 - (currentMillis - startMillis1) / 1000;
        break;
      case 1:
        remainingTime1 = yellow_time_1 - (currentMillis - startMillis1) / 1000;
        break;
      case 2:
        remainingTime1 = red_time_1 - (currentMillis - startMillis1) / 1000;
        break;
    }
  
    // Tính thời gian còn lại cho mỗi màu đèn của làn 2
    int remainingTime2 = 0;
    switch (state2) {
      case 0:
        remainingTime2 = red_time_2 - (currentMillis - startMillis2) / 1000;
        break;
      case 1:
        remainingTime2 = green_time_2 - (currentMillis - startMillis2) / 1000;
        break;
      case 2:
        remainingTime2 = yellow_time_2 - (currentMillis - startMillis2) / 1000;
        break;
    }
    controlLightsLane1();
    controlLightsLane2();
    displayNumber(remainingTime1, remainingTime2, latchPin1, dataPin1, clockPin, latchPin2, dataPin2, clockPin);
  } else if (choice == 1){
     // Tính thời gian còn lại cho mỗi màu đèn của làn 2
    int remainingTime2 = 0;
    switch (state2) {
      case 0:
        remainingTime2 = green_time_2 - (currentMillis - startMillis2) / 1000;
        break;
      case 1:
        remainingTime2 = yellow_time_2 - (currentMillis - startMillis2) / 1000;
        break;
      case 2:
        remainingTime2 = red_time_2 - (currentMillis - startMillis2) / 1000;
        break;
    }
  
    // Tính thời gian còn lại cho mỗi màu đèn của làn 1
    int remainingTime1 = 0;
    switch (state1) {
      case 0:
        remainingTime1 = red_time_1 - (currentMillis - startMillis1) / 1000;
        break;
      case 1:
        remainingTime1 = green_time_1 - (currentMillis - startMillis1) / 1000;
        break;
      case 2:
        remainingTime1 = yellow_time_1 - (currentMillis - startMillis1) / 1000;
        break;
    }
    controlLightsLane1();
    controlLightsLane2();
    displayNumber(remainingTime1, remainingTime2, latchPin1, dataPin1, clockPin, latchPin2, dataPin2, clockPin);
  }
}
