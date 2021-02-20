#include "I2Cdev.h"

#include "MPU6050_6Axis_MotionApps20.h"

#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    #include "Wire.h"
#endif


MPU6050 mpu;

#define OUTPUT_READABLE_YAWPITCHROLL

#define NUM_SAMPLES 70
#define NUM_AXES 3
//#define TRUNCATE 20
#define MOVE_SENSE 10
#define INTERVAL 20
double baseline[NUM_AXES];
double features[NUM_SAMPLES * NUM_AXES];

#define INTERRUPT_PIN 2  // use pin 2 on Arduino Uno & most boards
#define LED_PIN 13 // (Arduino is 13, Teensy is 11, Teensy++ is 6)
bool blinkState = false;

// MPU control/status vars
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorInt16 aa;         // [x, y, z]            accel sensor measurements
VectorInt16 aaReal;     // [x, y, z]            gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            world-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector

volatile bool mpuInterrupt = false;   
void dmpDataReady() {
    mpuInterrupt = true;
}

int i;
int motion = 0;
int counter = 0;
int btnPin1 = 9;
int precBtn1 = 1;
const int flexPin1 = 0;
const int flexPin2 = 1;
const int flexPin3 = 2;
const int flexPin4 = 3;
float flex[4];
float prevX = 0;
void setup() {
  // join I2C bus (I2Cdev library doesn't do this automatically)
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
        Wire.begin();
        Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
        Fastwire::setup(400, true);
    #endif

    // initialize serial communication
    // (115200 chosen because it is required for Teapot Demo output, but it's
    // really up to you depending on your project)
    Serial.begin(19200);
    while (!Serial); // wait for Leonardo enumeration, others continue immediately

    //Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));


    devStatus = mpu.dmpInitialize();

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu.setXGyroOffset(220);
    mpu.setYGyroOffset(76);
    mpu.setZGyroOffset(-85);
    mpu.setZAccelOffset(1788); // 1688 factory default for my test chip

    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);
    //mpu.PrintActiveOffsets();
    mpu.setDMPEnabled(true);
    mpuIntStatus = mpu.getIntStatus();
    dmpReady = true;
    packetSize = mpu.dmpGetFIFOPacketSize();
    
    pinMode(btnPin1, INPUT_PULLUP);
    Serial.println();
    calibrate();
}

void loop() {

  float x, y, z;
  if (!dmpReady){ 
    return;
  }

  if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) {

//    ypr_read(&x, &y, &z);
//    float x_t = x - baseline[0];
//    y = y - baseline[1];
//    z = z - baseline[2];
//
//    prevX = x;

//    if (!motionDetected(x_t, y, z)) {
//        Serial.println("no motion");
//        delay(INTERVAL);
//        return;
//    }
    recordIMU();
//    calibrate();
  }

}

void calibrate() {
    float x, y, z;
    ypr_read(&x, &y, &z);

    baseline[0] = x;
    baseline[1] = y;
    baseline[2] = z;
    Serial.println("baseline:");
    Serial.println(baseline[0]);
}

void ypr_read(float *x, float *y, float *z) {
    //int16_t _x, _y, _z;
    
    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);

    *x = ypr[0] * 180/M_PI;
    *y = ypr[1] * 180/M_PI;
    *z = ypr[2] * 180/M_PI;
    for(int i = 0; i < 4; i++){
      flex[i] = analogRead(i);
    }
    //Serial.print(ypr[0] * 180/M_PI);
}

void recordIMU() {
    float x, y, z;

    for (int i = 0; i < NUM_SAMPLES; i++) {
        mpu.dmpGetCurrentFIFOPacket(fifoBuffer);
        ypr_read(&x, &y, &z);
        Serial.print(x);
        Serial.print(" "); Serial.print(y);
        Serial.print(" "); Serial.print(z);
        for(int j = 0; j < 4; j++){
          Serial.print(" "); Serial.print(flex[j]);
        }
        Serial.println();
        
        delay(INTERVAL);
    }
}


bool motionDetected(float x, float y, float z) {
  Serial.print("movement:");
  Serial.println(abs(x) + abs(y) + abs(z));
    return (abs(x) + abs(y) + abs(z)) > MOVE_SENSE;
}
