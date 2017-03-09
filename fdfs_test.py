# encoding:utf8
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import os
import time
import shutil


# IP加密秘钥
_ip_crypt_key = 'cetc%^&*()123456'


class prpcrypt():
    """
    加密字段，例如.encrypt('192.168.1.180')  = 'fbc3ea6dc7455db5e01f76d1526d5369'
    """
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        # 这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用
        length = 16
        count = len(text)
        add = length - (count % length)
        text += '\0' * add
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


def _get_file_buffer(path, ext='', timeout=15.0, pool_frequency=0.5):
    """
    从文件夹中获取文件，该文件夹中不包含其他任何文件，且不能多线程
    :param path:
    :param timeout:
    :param pool_frequency:
    :return:
    """
    buf = None
    count = 0
    try:
        wait = timeout/pool_frequency
    except Exception, e:
        print('查找缓存文件参数错误{},{}'.format(path, str(e)))
        return buf

    while count < wait:
        count += 1
        try:
            files = os.listdir(path)
            if len(files) == 0:
                time.sleep(pool_frequency)
                continue

            for file_temp in files:
                file_path = '{}/{}'.format(path, file_temp)
                print 'file_path', file_path
                if file_temp.endswith(ext) and buf is None and os.path.isfile(file_path):
                    file_open = open(file_path, mode='rb')
                    buf = file_open.read()
                    file_open.close()
                os.remove(file_path)
            else:
                break
        except Exception, e:
            print('查找缓存文件过程出现异常{},{}'.format(path, str(e)))
            break

    return buf


def _get_file(path, timeout=15.0, pool_frequency=0.5):
    """
    从文件夹中获取文件，该文件夹中不包含其他任何文件，且不能多线程
    :param path:
    :param timeout:
    :param pool_frequency:
    :return:
    """
    files_result = []
    count = 0
    try:
        wait = timeout/pool_frequency
    except Exception, e:
        print('查找缓存文件参数错误{},{}'.format(path, str(e)))
        return files_result

    while count < wait:
        count += 1
        try:
            files = os.listdir(path)
            if len(files) == 0:
                time.sleep(pool_frequency)
                continue

            for file_temp in files:
                file_path = '{}/{}'.format(path, file_temp)
                files_result.append(file_path)
                print 'file_path', file_path
            else:
                break
        except Exception, e:
            print('查找缓存文件过程出现异常{},{}'.format(path, str(e)))
            break

    return files_result


class FileClient:
    def __init__(self, **kwds):
        self.encryp = prpcrypt(_ip_crypt_key)
        self._upload_client = None
        import sys
        count = 0

        try:
            self.log = open('./log.txt', 'a+')
            self.add = open('./add_success.txt', 'a+')
        except Exception, e:
            print('日志文件打开失败')
            return

        if sys.platform.lower()[:3] == 'win':
            print('客户端在windows上运行')
            from fdfs_client_win.client import Fdfs_client as Client
            _config_path = './fdfs_client_win/client.conf'
        else:
            print('客户端在非windows平台上运行')
            from fdfs_client_linux.client import Fdfs_client as Client
            _config_path = './fdfs_client_linux/client.conf'

        while not self._upload_client and count < 2:
            count += 1
            try:
                self._upload_client = Client(_config_path)
            except Exception, e:
                print('初始化FDFS客户端失败', e)
                self._upload_client = None

    @staticmethod
    def clear_path(path=None):
        if path is None:
            return
        try:
            files = os.listdir(path)
            if len(files) == 0:
                return

            for file_temp in files:
                file_path = '{}/{}'.format(path, file_temp)
                os.remove(file_path)
            else:
                return
        except Exception, e:
            print('清空缓存文件夹过程出现异常{},{}'.format(path, str(e)))
            return

    def save_picture(self, filebuffer=None, path=None, ext='', filename=None):
        """
        buffer直接写入到本地文件存储磁盘中
        :param path:
        :param ext: 扩展名
        :param filebuffer:string; ext:string
        :return:
        """
        if self._upload_client is None:
            print('文件上传客户端加载失败，无法保存截图')
            return False

        if filebuffer is None and path is not None:
            print 'will search the file in ', path, ext
            filebuffer = _get_file_buffer(path=path, ext=ext)

        count = 0
        while count < 1 and filebuffer is not None:
            count += 1
            try:
                if not ext:
                    ret = self._upload_client.upload_by_buffer(filebuffer)
                else:
                    ret = self._upload_client.upload_by_buffer(filebuffer, file_ext_name=ext)
            except Exception, e:
                print('上传文件出现异常,%s' % str(e))
                continue
            else:
                if 'Upload successed' in ret.get('Status'):
                    result =  {
                        'uri': self.encryp.encrypt(ret.get('Storage IP')) + '/' + ret.get('Remote file_id'),
                        'size': ret.get('Uploaded size'),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        # 'group_name': ret.get('Group name')
                    }
                    print result
                    # return True
                else:
                    print('上传文件失败%s' % str(ret))
                    continue
        else:
            return False

    def save_file(self, path=None):
        if self._upload_client is None:
            print('文件上传客户端加载失败，无法保存文件')
            return False

        if path is not None:
            print 'will search the file in ', path
            files = _get_file(path=path)

        self.add.write('{}：尝试添加文件\n'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
        for file_path in files:
            try:
                # 获取后缀
                info = os.path.splitext(file_path)
                if len(info) > 1:
                    ext = info[1][1:]
                else:
                    ext = ''

                print '准备处理文件', info, ext
                meta = {'ext_name':ext}
                # upload_by_filename存在bug，会丢失后缀名，截取的倒数第二个.后面的6位数字
                # fbc3ea6dc7455db5e01f76d1526d5369/group1/M00/03/90/wKgBtFh0whiAc_tPACqmWxYA8YA.118-90',
                # 'name': './upload//58.216.200.118-90.mp4', 'size': '2.00MB'}
                temp_file = file_path
                file_info = file_path.split('.')
                if len(file_info) >= 2 and len(file_info[-1]) + len(file_info[-2]) >= 5:
                    temp_file = '{}/{}.{}'.format(path, time.strftime('%H%M%S'), ext)
                    shutil.copy(file_path, temp_file)
                ret = self._upload_client.upload_by_filename(temp_file, meta_dict=meta)
            except Exception, e:
                print('上传文件出现异常,%s' % str(e))
                self.log.write('上传文件出现异常,%s' % str(e))
            else:
                if 'Upload successed' in ret.get('Status'):
                    result = {
                        'uri': self.encryp.encrypt(ret.get('Storage IP')) + '/' + ret.get('Remote file_id'),
                        'size': ret.get('Uploaded size'),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'name': ret.get('Local file name')
                        # 'group_name': ret.get('Group name')
                    }
                    self.log.write('{} 保存为 {}\n'.format(file_path, result.get('uri')))
                    self.add.write('{}\n'.format(result.get('uri')))
                    print result
                else:
                    print('上传文件失败{}，{}'.format(file_path, str(ret)))
                    self.log.write('上传文件失败{}，{}\n'.format(file_path, str(ret)))
            finally:
                if file_path != temp_file:
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        else:
            return True

    def delete_file(self, remote_file):
        if self._upload_client is None:
            print('文件上传客户端加载失败，无法保存截图')
            return False

        remote_file_info = remote_file.split('/')
        if len(remote_file_info) <= 1:
            print('文件ID索引错误，无法删除，{}'.format(remote_file))
            self.log.write('文件ID索引错误，无法删除，{}\n'.format(remote_file))
            return False

        try:
            self._upload_client.delete_file('/'.join(remote_file_info[1:]))
        except Exception, e:
            print('删除文件过程发生异常，请重试，{}，{}'.format(remote_file, str(e)))
            self.log.write('删除文件过程发生异常，请重试，{}，{}\n'.format(remote_file, str(e)))
            return False
        else:
            print('删除文件{}成功'.format(remote_file))
            self.log.write('删除文件{}成功\n'.format(remote_file))
            return True

    def quit(self):
        self.log.close()
        self.add.close()


if __name__ == '__main__':
    pass
    # file_name = 'f54b358c5d6bb0515f542dcbf43f0b4c/group1/M00/00/A7/CAcbCFhzN2WAAn1kAJPqL047Q_o.10.mp4'
    # filetest.delete_file(file_name)
    # file_name = 'f54b358c5d6bb0515f542dcbf43f0b4c/group1/M00/00/A7/CAcbCFhzOA-AHkdCJ6R3CiGP5d836.rmvb'
