"""
The Generator and the Dicriminator Classes for the model:
"""

import torch
import torch.nn as nn
import torchvision.transforms.functional as TF
from torchvision import models
from torchsummary import summary

# Double conv is Clear!!
class DoubleConv(nn.Module):
    def __init__(self,in_channels, out_channels,K=3):
        super(DoubleConv,self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels,kernel_size=K,stride=1,padding=1,bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2),
            nn.Conv2d(out_channels, out_channels,kernel_size=K,stride=1,padding=1,bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2),
        )

    def forward(self, x):
        return self.conv(x)

# Down-sampling the Image!!
class Down(nn.Module):
    """Downscaling with maxpool then double conv"""

    def __init__(self, in_channels, out_channels):
        super(Down,self).__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(kernel_size=2,stride=2),
            DoubleConv(in_channels, out_channels)
        )

    def forward(self, x):
        return self.maxpool_conv(x)

# Up-Scaling the image!!
class Up(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(Up,self).__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv = DoubleConv(2*out_channels,out_channels);

    def forward(self, DownImg, BackImg):
        print('in_img: ',DownImg.shape)
        print('back_img: ',BackImg.shape)
        TransposeImg = self.up(DownImg)
        print('Transposed: ',TransposeImg.shape)
        if BackImg.shape != TransposeImg.shape:
            TransposeImg = TF.resize(TransposeImg,size=BackImg.shape[2:])
        
        ConcatImg = torch.cat((TransposeImg,BackImg),dim=1)
        print('Concatenated: ',ConcatImg.shape)
        x = self.conv(ConcatImg)
        return x
    
# Final Convolutional Layer!!
class OutConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)


class UNET(nn.Module):
    def __init__(
            self,in_channels,out_channels,## Will have to take care weather the inchannels are 3 or 6.
    ):
        super(UNET,self).__init__()
        self.first = DoubleConv(in_channels,32)
        self.D1 = Down(32,64)
        self.D2 = Down(64,64)
        self.D3 = Down(64,128)
        self.Bottleneck = Down(128,256)
        self.U1 = Up(256,128)
        self.U2 = Up(128,64)
        self.U3 = Up(64,64)
        self.U4 = Up(64,32)
        self.out = OutConv(32,out_channels)

    def forward(self,x):
        back_inputs = []
        x = self.first(x)
        back_inputs.append(x) # 1
        # print('first: ',x.shape)
        x =self.D1(x) 
        back_inputs.append(x) # 2
        # print('D1: ',x.shape)
        x =self.D2(x)
        back_inputs.append(x) # 3
        # print('D2: ',x.shape)
        x =self.D3(x)
        back_inputs.append(x) # 4
        # print('D3: ',x.shape)

        x = self.Bottleneck(x)
        # print('BottleNeck: ',x.shape)
        back_inputs = back_inputs[::-1]## Reversing the list
        # for img in back_inputs:
        #     print(img.shape)

        x =self.U1(x,back_inputs[0])
        # print('U1: ',x.shape)
        x =self.U2(x,back_inputs[1])
        # print('U2: ',x.shape)
        x =self.U3(x,back_inputs[2])
        # print('U3: ',x.shape)
        x =self.U4(x,back_inputs[3])
        # print('U4: ',x.shape)
        x =self.out(x)
        # print('out: ',x.shape)
        return x

# def test():
#     x  = torch.randn((3,3,165,165))## batchsize,in_channels,H, W
#     model = UNET(in_channels=3,out_channels=3)
#     preds = model(x)
#     print(preds.shape)
#     print(x.shape)
#     assert preds.shape == x.shape

# if __name__ == "__main__":
#     test()