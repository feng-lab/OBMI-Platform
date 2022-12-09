import torch
from torch.nn import functional as F

class ApplyShifts():
    def __init__(self,output):
        self.output=output
        self.W=self.output.shape[1]
        self.H=self.output.shape[0]

        #Search the highest NCC score in the NCC map in the central region,
        #the half size of the region should be larger than the maximum offsets in the video.
        #w and h are the width and height of the region.
        self.w_crop=60
        self.h_crop=60


    def get_position(self):
        #Find the highest correlation in the NCC map.

        index=torch.argmax(self.output[int((self.H/2)-int(self.h_crop/2)):int((self.H/2)+int(self.h_crop/2)),
                           int((self.W/2)-int(self.w_crop/2)):int((self.W/2)+int(self.w_crop/2))])
        index=torch.tensor(index, dtype=torch.float)

        row_index=torch.floor(index/self.w_crop)
        col_index=index%self.w_crop

        return row_index, col_index

    def compute_offset(self):
        row_index, col_index=self.get_position()
        sub_x, sub_y=self.sub_pixel(row_index, col_index)

        offset_y = int(self.h_crop / 2) - row_index - sub_y
        offset_x = int(self.w_crop / 2) - col_index - sub_x

        return offset_y, offset_x

    def sub_pixel(self, row_index, col_index):

        #To reach sub-pixel level precision
        highest_position_x=col_index+(self.W-self.w_crop)/2
        highest_position_y=row_index+(self.H-self.h_crop)/2

        y_up=self.output[int(highest_position_y-1), int(highest_position_x)]
        y_down=self.output[int(highest_position_y+1), int(highest_position_x)]
        x_left=self.output[int(highest_position_y), int(highest_position_x-1)]
        x_right=self.output[int(highest_position_y), int(highest_position_x+1)]

        gaussian=1
        if gaussian==0:
        #parabola fitting
            sub_pixel_x=(x_left-x_right)/(2*x_left+2*x_right-4*self.output[int(highest_position_y), int(highest_position_x)])
            sub_pixel_y=(y_up-y_down)/(2*y_up+2*y_down-4*self.output[int(highest_position_y), int(highest_position_x)])

        #gaussian fitting
        else:
            sub_pixel_x = (torch.log(x_left) - torch.log(x_right)) / (
                    2 * torch.log(x_left) + 2 * torch.log(x_right) - 4 * torch.log(
                self.output[int(highest_position_y), int(highest_position_x)]))
            sub_pixel_y = (torch.log(y_up) - torch.log(y_down)) / (
                    2 * torch.log(y_up) + 2 * torch.log(y_down) - 4 * torch.log(
                self.output[int(highest_position_y), int(highest_position_x)]))
        return sub_pixel_x, sub_pixel_y

    def apply_shift(self, frame, theta):

        offset_y, offset_x=self.compute_offset()
        # theta=torch.tensor([
        #     [1,0,-offset_x*2/frame.shape[1]],
        #     [0,1,-offset_y*2/frame.shape[0]]
        # ], dtype=torch.float32)
        theta[0,2]=-offset_x*2/frame.shape[1]
        theta[1,2]=-offset_y*2/frame.shape[0]

        grid=F.affine_grid(theta.unsqueeze(0),frame.unsqueeze(0).unsqueeze(0).size())
        output=F.grid_sample(frame.unsqueeze(0).unsqueeze(0), grid)
        new_img_torch=output[0]
        return new_img_torch ,offset_y ,offset_x


