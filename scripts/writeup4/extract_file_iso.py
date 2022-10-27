import sys
import pycdlib
from PySquashfsImage import SquashFsImage

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

if len(sys.argv) != 3:
    print('Usage: %s <file> <iso>' % (sys.argv[0]))
    sys.exit(1)

print("Extract filesystem.squashfs from the iso ...")
iso = pycdlib.PyCdlib()
iso.open(sys.argv[2])
extracted = BytesIO()
iso.get_file_from_iso_fp(extracted, iso_path='/CASPER/FILESYSTEM.SQUASHFS;1')
iso.close()
file = open('filesystem.squashfs', 'wb')
file.write(extracted.getvalue())
file.close()

file_path = sys.argv[1]
print(f"Downloading {file_path}...")
image = SquashFsImage('filesystem.squashfs')
for file in image.root.findAll():
    if file.getPath() == file_path:
        with open(file_path.split('/')[-1], 'wb') as f:
            f.write(file.getContent())
image.close()
