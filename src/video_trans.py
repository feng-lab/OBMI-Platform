import cv2
import numpy as np

if __name__ == "__main__":
    cap = cv2.VideoCapture('C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo.avi')
    out_path = 'C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo_out.avi'
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    sav = cv2.VideoWriter(out_path, fourcc, 30, (256, 256), True)
    #out_frame = np.zeros((height,width,3), 'uint8')
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        out_frame = cv2.resize(frame, dsize=(256, 256), interpolation=cv2.INTER_CUBIC)
        print(out_frame.shape)
        sav.write(out_frame)

    cap.release()
    sav.release()