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
def validate():
    for name in ['index.html','jefferys/index.html','creative-clips/index.html','laundermutt/index.html']:
        assert (ROOT/name).is_file(), 'Missing entrypoint: '+name
    count=0
    for p in ROOT.rglob('*'):
        assert not p.is_symlink(), 'Symlink not permitted'
        if not p.is_file(): continue
        assert p.suffix.lower() in ALLOWED and not p.name.startswith('.'), 'Unexpected public file: '+str(p)
        if p.suffix=='.html':
            page=Page();page.feed(p.read_text());refs=page.refs
            assert page.noindex, 'Concept pages must retain noindex'
        elif p.suffix=='.css': refs=re.findall(r'url\([\"\']?([^\)\"\']+)',p.read_text())
        else: refs=[]
        for ref in refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc: continue
            assert not u.path.startswith('/'), 'Use relative paths: '+ref
            dest=(p.parent/unquote(u.path)).resolve() if u.path else p.resolve()
            assert dest.is_relative_to(ROOT.resolve()), 'Reference outside site: '+ref
            if dest.is_dir(): dest=dest/'index.html'
            assert dest.is_file(), 'Missing asset: '+str(dest)
            if u.fragment and dest.suffix=='.html':
                target=Page();target.feed(dest.read_text());assert u.fragment in target.ids, 'Missing anchor: '+ref
            count+=1
    print('Validated three demos and collection; local references:',count)
if __name__=='__main__': validate()
