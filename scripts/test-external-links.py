"""Response-policy regression tests without third-party requests."""
import runpy, unittest
from pathlib import Path
class PolicyTests(unittest.TestCase):
    def test_status_and_network_outcomes(self):
        classify=runpy.run_path(str(Path(__file__).with_name("check-external-links.py")))["classify"]
        for status in (404,410): self.assertEqual(classify(status)[0],"broken")
        for status in (301,302,304,400,401,403,408,429,500,502,503): self.assertEqual(classify(status)[0],"unverified")
        self.assertEqual(classify(error="TimeoutError")[0],"unverified")
        self.assertEqual(classify(200,final_url="http://example.com")[0],"unverified")
        self.assertEqual(classify(200,final_url="https://example.com")[0],"verified")
if __name__ == "__main__": unittest.main()
