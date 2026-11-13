"""Scanner admission tests use synthetic strings constructed in memory only."""
import runpy, unittest
from pathlib import Path
class ScannerTests(unittest.TestCase):
    def test_supported_formats_and_negative_control(self):
        count=runpy.run_path(str(Path(__file__).with_name("scan-source-secrets.py")))["candidate_count"]
        values=["sk_"+"live_"+"a"*24, "rk_"+"live_"+"a"*24, "xox"+"b-"+"a"*24, "AI"+"za"+"a"*35, "gh"+"p_"+"a"*36]
        for value in values: self.assertGreater(count(value),0)
        self.assertEqual(count("Use the provider key by name; no credentials here."),0)
if __name__ == "__main__": unittest.main()
