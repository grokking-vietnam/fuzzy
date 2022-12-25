import glob
import tarfile

with tarfile.open('archive.tar.bz2', 'w:bz2') as tar:
    for file in glob.glob("tmp"):
        tar.add(file)
