from hnccorr import Movie, HNCcorrConfig, HNCcorr
from hnccorr.example import load_example_data
import matplotlib.pyplot as plt
import numpy as np
import cv2


class VLoader:

    def load_video(self, path):
        capture = cv2.VideoCapture(path)

        frames = []
        while True:
            ret, tmp_frame = capture.read()

            if not ret:
                break

            frame = cv2.cvtColor(tmp_frame, cv2.COLOR_RGB2GRAY)
            frames.append(frame)

        capture.release()

        res = np.array(frames)  # shape: (frame, height, width)
        return res

class Hncc:
    def auto_roi(self):
        # loader = VLoader()
        # filepath = "C:\\Users\\ZJLAB\\Downloads\\Video"
        # file = filepath + "\\msCam4.avi"
        # data = loader.load_video(file)
        # movie = Movie("Example movie", data)

        DATA_DIR = "D:\\0_Project\\20211217_neurofinder\\neurofinder.00.00"
        image_dir = DATA_DIR + "\\neurofinder.00.00" + "\\images"
        num_images = 3024
        movie = Movie.from_tiff_images("Example movie", image_dir, num_images)

        # (800, 512, 512), data has 800 frames, each of 512 x 512 pixels
        # print("data.shape: ", data.shape)
        # plt.figure(figsize=(6, 6))
        # # see one frame
        # plt.imshow(data[600, :, :])  # 600th frame

        config = HNCcorrConfig(percentage_of_seeds=0.025)
        H = HNCcorr.from_config(config)
        H.segment(movie)

        h = H.segmentations  # List of identified cells
        # for segmentation in h:
        #     for (x, y) in list(segmentation.selection):
        #         # print(f"x: {x}, y: {y}")
        #         # according to the results of imshow, so is y, x
        #         plt.scatter(y, x, c='r', s=1, alpha=1 / 10)

        res = H.segmentations_to_list()  # Export list of cells (for Neurofinder)]

        # A = np.zeros(movie.pixel_shape)
        # for segmentation in h:
        #     for i, j in segmentation.selection:
        #         A[i, j] += 1

        res = []
        for segmentation in h:
            xsum = 0
            ysum = 0
            xmax = 0
            ymax = 0
            xmin = 9999
            ymin = 9999
            for j, i in segmentation.selection:
                xsum += i
                ysum += j
                if i > xmax:
                    xmax = i
                if j > ymax:
                    ymax = j
                if i < xmin:
                    xmin = i
                if j < ymin:
                    ymin = j

            centX = xsum / len(segmentation.selection)
            centY = ysum / len(segmentation.selection)
            size = max(xmax-xmin, ymax-ymin)
            res.append([centX, centY, size])

        return res