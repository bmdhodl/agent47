"""REGRESSION: maintained HTML uses the shared BMD identity."""
import re
from pathlib import Path

from agentguard.reporting import render_incident_report


def test_incident_report_has_offline_brand_and_readable_tokens():
    rendered = render_incident_report([], output_format="html")
    assert 'class="bmd-mark"' in rendered
    assert 'data:image/png;base64,' in rendered
    assert '--bmd-colors-background: #0a0a0a;' in rendered
    assert 'name="viewport"' in rendered
    assert 'No guard events recorded.' in rendered


def test_every_maintained_site_page_uses_the_same_mark():
    root = Path(__file__).resolve().parents[2]
    for page in (root / 'site').rglob('*.html'):
        text = page.read_text(encoding='utf-8')
        assert 'bmd-loop-mark-512.png' in text, page
        assert re.search(r'<img[^>]+class="bmd-mark"', text), page
        assert 'fonts.googleapis.com' not in text, page

def test_generated_render_assets_match_source():
    import hashlib
    import runpy
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    generator = runpy.run_path(str(root / "scripts/sync_design_assets.py"))
    assert generator["TARGET"].read_text(encoding="utf-8") == generator["expected"]()
    assert hashlib.sha256((root / "bmd-loop-mark-512.png").read_bytes()).hexdigest() == "362d797dd2920fadda6ae91488143780ba6ca2951aefedda3d71061de3a3c1cc"

def test_site_asset_copies_cannot_drift():
    root = Path(__file__).resolve().parents[2]
    assert (root / "site/assets/bmd-loop-mark-512.png").read_bytes() == (root / "bmd-loop-mark-512.png").read_bytes()
    assert (root / "site/assets/design-tokens.css").read_text(encoding="utf-8") == (root / "design-tokens.css").read_text(encoding="utf-8")


def test_readme_badge_preview_uses_shared_identity():
    """REGRESSION: the copyable badge still used a separate red brand."""
    root = Path(__file__).resolve().parents[2]
    markup = (root / 'site/quickstart.html').read_text(encoding='utf-8')
    assert 'shields.io/badge/guarded' not in markup
    assert 'https://bmdpat.com/icons/mark-512.png' in markup
