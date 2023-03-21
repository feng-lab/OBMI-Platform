import cv2
import numpy as np


def matTrans():
    import h5py
    # path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\blood_vessel_10Hz.mat'
    path = 'C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz.mat'
    data = h5py.File(path, 'r')
    mat = data['Y']
    mat = np.array(mat)
    dis = mat.max() - mat.min()
    mat = (mat - mat.min()) / dis * 255
    mat = mat.astype('uint8')

    # out_path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\blood_vessel_10Hz.avi'
    out_path = 'C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz.avi'
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    height = 256
    width = 256
    fps = 30
    sav = cv2.VideoWriter(out_path, fourcc, fps, (width, height), isColor=False)

    for frame in mat:
        sav.write(frame.T)
    sav.release()

def framedrop():
    cap = cv2.VideoCapture('C:\\Users\ZJLAB\Desktop\文档材料\demo\offline_demo_full.mp4')
    out_path = 'C:\\Users\ZJLAB\Desktop\文档材料\demo\offline_demo_short.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(height, width)
    start_frame = 0
    total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    sav = cv2.VideoWriter(out_path, fourcc, fps, (width, height), True)
    i = 0
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if i > start_frame:
            if i % 3 == 0:
                i += 1
                continue

        if i % 1000 == 0:
            print(f'processing {i}, {i/total_frame*100}%')

        sav.write(frame)
        i += 1


    cap.release()
    sav.release()


def videocut():
    cap = cv2.VideoCapture('C:\\Users\ZJLAB\caiman_data\example_movies\\2.mp4')
    out_path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\behavior.avi'
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(height, width)
    sav = cv2.VideoWriter(out_path, fourcc, fps, (int(width/2), height), True)
    out_frame = np.zeros((height,int(width/2),3), 'uint8')
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        out_frame = frame[:,:int(width/2),:]
        #out_frame = cv2.resize(frame, dsize=(200, 150), interpolation=cv2.INTER_CUBIC)
        sav.write(out_frame)

    cap.release()
    sav.release()

def video_concat():
    paths = ['C:\\Users\ZJLAB\Desktop\材料\\offline1.mp4',
             'C:\\Users\ZJLAB\Desktop\材料\\offline2.mp4',
             'C:\\Users\ZJLAB\Desktop\材料\\offline3.mp4']
    out_path = 'C:\\Users\ZJLAB\caiman_data\example_movies\\offline_concat.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    cap = cv2.VideoCapture(paths[0])
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    sav = cv2.VideoWriter(out_path, fourcc, fps, (width, height), True)

    for path in paths:
        print('processing file:', path)
        cap.release()
        cap = cv2.VideoCapture(path)
        while True:
            ret, frame = cap.read()

            if not ret:
                break
            sav.write(frame)

    cap.release()
    sav.release()
    print('process done')
    print('out path:', out_path)
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
    #matTrans()
    #videocut()
    framedrop()
    #video_concat()

