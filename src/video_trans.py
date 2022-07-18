import cv2
import numpy as np

if __name__ == "__main__":
    cap = cv2.VideoCapture('C:\\Users\\ZJLAB\\Desktop\\movie.avi')
    width = 300
    height = 300
    out_path = 'C:\\Users\\ZJLAB\\Desktop\\out_movie2.avi'
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    sav = cv2.VideoWriter(out_path, fourcc, 30, (width, height), True)
    out_frame = np.zeros((height,width,3), 'uint8')
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        out_frame = frame[:, :300, :]
        print(out_frame.shape)
        sav.write(out_frame)

    cap.release()
    sav.release()