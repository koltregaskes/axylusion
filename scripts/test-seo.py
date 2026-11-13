"""Regression checks for graph identity and metadata freshness."""
import json,re,unittest
from seo import ROOT,enhance_html,canonical
class MetadataTests(unittest.TestCase):
    def test_identity_and_changed_title(self):
        for relative in ("about.html", "gallery.html", "tools.html"):
            with self.subTest(page=relative):
                text=(ROOT / relative).read_text(encoding="utf-8")
                text=re.sub(r"<title>.*?</title>","<title>Changed title</title>",text,flags=re.S)
                result=enhance_html(text,relative)
                blocks=re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',result,re.S)
                self.assertEqual(len(blocks),1)
                nodes=json.loads(blocks[0])["@graph"]
                types={"WebPage","AboutPage","ImageGallery","CreativeWork","CollectionPage"}
                pages=[n for n in nodes if n.get("@type") in types and (n.get("url")==canonical(relative) or str(n.get("@id","")).split("#")[0]==canonical(relative))]
                self.assertEqual(len(pages),1)
                self.assertEqual(pages[0]["name"],"Changed title")
                self.assertEqual(enhance_html(result,relative),result)
if __name__ == "__main__": unittest.main()
