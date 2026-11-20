"""Validate only public static files, including relative paths and HTML anchors."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re

ROOT = Path(__file__).resolve().parents[1] / 'site'
ALLOWED = {'.html', '.css', '.js', '.jpg', '.jpeg', '.png', '.webp', '.svg', '.ico', '.woff', '.woff2'}
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.ids=set(); self.noindex=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        self.refs.extend(a[k] for k in ['href','src'] if a.get(k))
        if tag=='meta' and a.get('name')=='robots': self.noindex='noindex' in a.get('content','')
DEMO_PAGES = ['index.html','jefferys/index.html','creative-clips/index.html','laundermutt/index.html','marlow-moss/index.html','clovercoat/index.html','puddle-puff/index.html']
MARKETING_PAGES = ['index.html','service-guide.html','privacy.html','404.html']

def validate(root=ROOT, marketing=False):
    ROOT = root
    if marketing:
        assert not (ROOT/'demos').exists(), 'Marketing source must not contain the demo destination'
        assert 'Disallow: /' not in (ROOT/'robots.txt').read_text().splitlines(), 'Marketing site must allow crawling'
        assert 'Sitemap: https://bleenky.com/sitemap.xml' in (ROOT/'robots.txt').read_text(), 'Missing sitemap declaration'
        assert (ROOT/'.htaccess').is_file(), 'Missing marketing routing configuration'
    for name in (MARKETING_PAGES if marketing else DEMO_PAGES):
        assert (ROOT/name).is_file(), 'Missing entrypoint: '+name
    count=0
    for p in ROOT.rglob('*'):
        assert not p.is_symlink(), 'Symlink not permitted'
        if not p.is_file(): continue
        assert (marketing and p.relative_to(ROOT).as_posix() in {'.htaccess','robots.txt','contact.php','sitemap.xml'}) or (p.suffix.lower() in ALLOWED and not p.name.startswith('.')), 'Unexpected public file: '+str(p)
        if p.suffix=='.html':
            page=Page();page.feed(p.read_text());refs=page.refs
            if marketing and p.name != '404.html':
                assert not page.noindex, 'Public marketing pages must allow indexing'
                assert 'data-review' not in p.read_text(), 'Remove preview banner before launch'
            else:
                assert page.noindex, 'Demos and error pages must retain noindex'
        elif p.suffix=='.css': refs=re.findall(r'url\([\"\']?([^\)\"\']+)',p.read_text())
        else: refs=[]
        for ref in refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc: continue
            assert marketing or not u.path.startswith('/'), 'Use relative paths: '+ref
            dest=((ROOT/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (p.parent/unquote(u.path))).resolve() if u.path else p.resolve()
            assert dest.is_relative_to(ROOT.resolve()), 'Reference outside site: '+ref
            if dest.is_dir(): dest=dest/'index.html'
            assert dest.is_file(), 'Missing asset: '+str(dest)
            if u.fragment and dest.suffix=='.html':
                target=Page();target.feed(dest.read_text());assert u.fragment in target.ids, 'Missing anchor: '+ref
            count+=1
    print('Validated '+('public marketing site' if marketing else 'three demos and collection')+'; local references:',count)
if __name__=='__main__':
    import sys
    marketing = '--marketing' in sys.argv
    validate(ROOT.parent/'marketing' if marketing else ROOT, marketing)
