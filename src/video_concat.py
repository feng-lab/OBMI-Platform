import cv2, os

def full_video_concat(root_dir, overwrite=False):
    lst = sorted(os.listdir(root_dir))

    for dir in lst:
        path = os.path.join(root_dir, dir)
        print('Working directory:', path)
        dairy_video_concat(path, overwrite)

def dairy_video_concat(root_dir, overwrite=False):
    lst = sorted(os.listdir(root_dir))

    for dir in lst:
        path = os.path.join(root_dir, dir, 'Miniscope')
        print('Working directory:', path)
        if os.path.exists(path):
            video_concat(path, overwrite)
        else:
            print('Directory does not exist:', path)

def video_concat(dir, overwrite=False):
    lst = os.listdir(dir)
    lst = list(filter(lambda x: '.avi' in x, lst))
    lst.sort(key=lambda x: int(x.split('.')[0]))

    if len(lst) > 0:
        out_dir = os.path.join(dir, 'output')
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        out_path = os.path.join(out_dir, 'full_video.avi')

        if not overwrite:
            if os.path.exists(out_path):
                return

        print('Total videos:', len(lst))
        p = os.path.join(dir, lst[0])
        cap = cv2.VideoCapture(p)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

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

if __name__ == '__main__':
    #### 合并单个miniscope文件夹的内容 ####
    dir_path = 'D:\data\\2023_08_16\\2023_08_16\\14_59_15\Miniscope'
    video_concat(dir_path, overwrite=False)     # 传递miniscope文件夹路径，overwrite为是否覆盖已合并过的视频

    #### 合并某个日期文件夹下的所有内容 ####
    dir_path = 'D:\data\\2023_08_16\\2023_08_16'
    dairy_video_concat(dir_path, overwrite=False)   # 传递日期文件夹路径，overwrite同上

    #### 合并所有日期文件夹下的所有内容，所有日期文件夹应放在同一路径下 ####
    dir_path = 'D:\data\\2023_08_16'
    full_video_concat(dir_path, overwrite=False)    # 传递日期文件夹所在的上一级路径，overwrite同上

    #### 以上三种方法按需选取使用 ####