import os

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


def robot_video_generator():
    dir = 'D:\\robotData\imagePng\imagePng'
    # dir = 'D:\\robotData\imagePng'
    files = os.listdir(dir)
    files.sort()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height = 480
    width = 640
    fps = 10

    out_path = 'D:\\robotData\imagePng'
    # rgb_sav = cv2.VideoWriter(os.path.join(out_path, 'rgb.mp4'), fourcc, fps, (width, height), True)
    d_sav = cv2.VideoWriter(os.path.join(out_path, 'd.mp4'), fourcc, fps, (width, height), True)
    for f in files:
        # if '.png' in f:
        #     img = cv2.imread(os.path.join(dir, f), cv2.IMREAD_COLOR)
        #     print(img)
        #     cv2.imshow("img", img)
        #     cv2.waitKey(1)
        #     rgb_sav.write(img)
        if '.raw' in f:
            img = np.fromfile(os.path.join(dir, f), dtype='uint16')
            img = img.reshape(height, width, 1)
            img = img.astype('uint8')
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            print(img.shape)
            cv2.imshow("img", img)
            cv2.waitKey(1)
            for _ in range(200):
                d_sav.write(img)
    d_sav.release()
    # rgb_sav.release()

def loadnpy():
    p = 'C:\\Users\ZJLAB\Documents\WeChat Files\wxid_ciusgv6gvwq222\FileStorage\File\\2023-08\\2023-07-12_trace.npy'
    d = np.load(p)
    print(d)

def video_nto1():
    dir = 'D:\data\\2023_08_16\\2023_08_16\\14_59_15\Miniscope'
    lst = os.listdir(dir)
    lst = list(filter(lambda x: '.avi' in x, lst))
    lst.sort(key=lambda x: int(x.split('.')[0]))

    if len(lst) > 0:
        print('Total videos:', len(lst))
        p = os.path.join(dir, lst[0])
        cap = cv2.VideoCapture(p)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        out_path = os.path.join(dir, 'full_video.avi')
        sav = cv2.VideoWriter(out_path, fourcc, fps, (w, h), True)

        for video in lst:
            print('processing video:', video)
            p = os.path.join(dir, video)
            cap = cv2.VideoCapture(p)
            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                sav.write(frame)
            cap.release()
        sav.release()




if __name__ == "__main__":
    # cap = cv2.VideoCapture('C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.mp4')\
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
    # framedrop()
    #video_concat()
    # robot_video_generator()
    # loadnpy()
    video_nto1()