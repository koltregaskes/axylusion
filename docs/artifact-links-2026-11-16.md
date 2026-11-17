# Artifact link checks — 16 November 2026

For hub #1908 / #1508. Source links can pass while an allowlisted artifact omits a linked file. `check-internal-links.py --site <directory>` now resolves HTML href/src and fragments exclusively in the requested directory, rejecting missing directories and paths escaping it. Validate Site runs it immediately after building the public artifact, with a regression proving source-pass/artifact-fail, fragment failure, restoration and escape rejection.

Verified locally: 20 routes pass in source and the 246-file artifact; regression passes; diff whitespace check passes. Fixtures are retained. External navigation, redirect hops, JS-created requests, srcset and CSS resources remain covered separately by privacy/media/browser checks; this is not full broken-link acceptance. No Pages-source change or deployment.
