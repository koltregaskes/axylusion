import unittest,tempfile
from pathlib import Path
from png_contract import validate_png
SOURCE=Path(__file__).resolve().parents[1]/'images/social-default.png'
class PngContract(unittest.TestCase):
 def check(self,data):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'card.png';p.write_bytes(data);validate_png(p)
 def test_valid(self):self.check(SOURCE.read_bytes())
 def test_header_only(self):
  with self.assertRaises(AssertionError):self.check(SOURCE.read_bytes()[:24])
 def test_corrupt_crc(self):
  data=bytearray(SOURCE.read_bytes());data[40]^=1
  with self.assertRaises(AssertionError):self.check(data)
 def test_missing_end(self):
  with self.assertRaises(AssertionError):self.check(SOURCE.read_bytes()[:-12])
 def test_trailing_garbage(self):
  with self.assertRaises(AssertionError):self.check(SOURCE.read_bytes()+b'junk')
if __name__=='__main__':unittest.main()
