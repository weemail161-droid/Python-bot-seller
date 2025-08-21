# ملف imghdr.py لتجاوز الخطأ
#def what(file, h=None):
  # return None
  
  # imghdr.py
import os

tests = []

def test_jpeg(h, f):
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'
    if h[:2] == b'\xff\xd8':
        return 'jpeg'

tests.append(test_jpeg)

def test_png(h, f):
    if h[:8] == b'\211PNG\r\n\032\n':
        return 'png'

tests.append(test_png)

def what(file, h=None):
    f = None
    try:
        if h is None:
            f = open(file, 'rb')
            h = f.read(32)
        for test in tests:
            res = test(h, f)
            if res:
                return res
    finally:
        if f:
            f.close()
    return None