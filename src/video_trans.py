import cv2
import numpy as np

def matTrans():
    import h5py
    path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\blood_vessel_10Hz.mat'
    data = h5py.File(path, 'r')
    mat = data['Y']
    mat = np.array(mat)
    dis = mat.max() - mat.min()
    mat = (mat - mat.min()) / dis * 255
    mat = mat.astype('uint8')

    out_path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\blood_vessel_10Hz.avi'
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    height = 256
    width = 256
    fps = 30
    sav = cv2.VideoWriter(out_path, fourcc, fps, (width, height), isColor=False)

    for frame in mat:
        sav.write(frame.T)
    sav.release()

if __name__ == "__main__":
    # cap = cv2.VideoCapture('C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.mp4')
    # out_path = 'C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.avi'
    # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    # height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # fps = int(cap.get(cv2.CAP_PROP_FPS))
    # sav = cv2.VideoWriter(out_path, fourcc, fps, (width, height), True)
    # #out_frame = np.zeros((height,width,3), 'uint8')
    # while True:
    #     ret, frame = cap.read()
    #
    #     if not ret:
    #         break
    #
    #     #out_frame = cv2.resize(frame, dsize=(200, 150), interpolation=cv2.INTER_CUBIC)
    #     sav.write(frame)
    #
    # cap.release()
    # sav.release()
    matTrans()
    

