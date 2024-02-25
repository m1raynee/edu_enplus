import time
import serial


arduino = serial.Serial("COM6", 9600)
print("waiting...")
time.sleep(2)
print("done.")

while True:
    print(1)
    for i in range(10):
        arduino.write("1".encode())
        time.sleep(0.1)

    print(0)
    for i in range(10):
        arduino.write("0".encode())
        time.sleep(0.1)
