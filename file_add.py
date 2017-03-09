# encoding: utf8
from fdfs_test import FileClient


if __name__ == '__main__':
    #  file_name = 'f54b358c5d6bb0515f542dcbf43f0b4c/group1/M00/00/A7/CAcbCFhzN2WAAn1kAJPqL047Q_o.10.mp4'
    file_test = FileClient()
    file_test.save_file('./upload/')
