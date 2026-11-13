# SEO validation

Run python scripts/build-seo.py to regenerate metadata, sitemap and RSS after rendering. Run python scripts/build-seo.py --check and python scripts/check-seo.py before review. The checker requires one JSON-LD graph per page, production canonical URLs, PNG social cards, complete sitemap coverage and valid RSS. CI checks source output; final deployed-domain readback remains separate.
