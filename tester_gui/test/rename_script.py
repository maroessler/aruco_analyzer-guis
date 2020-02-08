import shutil
import os

path = os.path.dirname(os.path.realpath(__file__))
print(path)
path = os.path.join(path, 'test')
files = os.listdir(path)
print(files)
for file in files:
    file_path = os.path.join(path, file)
    dst = int(file) + 108
    dst_path = os.path.join(path, str(dst))
    print(file_path)
    print(dst_path)
    shutil.move(file_path, dst_path)