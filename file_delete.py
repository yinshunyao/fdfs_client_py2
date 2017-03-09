# encoding: utf8
from fdfs_test import FileClient


if __name__ == '__main__':
    #  file_name = 'f54b358c5d6bb0515f542dcbf43f0b4c/group1/M00/00/A7/CAcbCFhzN2WAAn1kAJPqL047Q_o.10.mp4'
    file_test = FileClient()
    with open('./delete.list', 'r') as delete_list:
        [file_test.delete_file(file_name.strip()) for file_name in delete_list]

