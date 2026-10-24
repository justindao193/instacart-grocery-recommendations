# Load the Python tools used by this script.
from pathlib import Path
import re
import posixpath
from urllib.parse import urlsplit, urlunsplit
import mistune
# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]
# Read the existing HTML guide so its custom layout can be preserved.
page=ROOT/'00_START_HERE.html'
text=page.read_text(encoding='utf-8')
# Set up Markdown conversion, including tables and checklist boxes.
render=mistune.create_markdown(escape=True,plugins=['table','task_lists'])
# Find only the editable note sections inside the HTML guide.
pattern=r'<article id="([^"]+)" class="page prose" hidden>(.*?)<p class="file-link"><a href="([^"]+)">Open the editable notes ↗</a></p></article>'
# Rebuild one note section from its Markdown file.
def replace(match):
    section,old_content,path=match.groups()
    content=render((ROOT/path).read_text(encoding='utf-8'))
    # Notes use links relative to their own folder; the guide lives at the root.
    def relocate_link(link):
        attribute,href=link.groups()
        parts=urlsplit(href)
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith('/'):
            return link.group(0)
        target=posixpath.normpath(posixpath.join(posixpath.dirname(path),parts.path))
        return attribute+'="'+urlunsplit(('', '', target, parts.query, parts.fragment))+'"'
    content=re.sub(r'(href|src)="([^"]+)"',relocate_link,content)
    # Give both learning pages visible links to the path and the lesson recap.
    if section in ('learning-plan', 'lesson-notes'):
        links = []
        for target, label in [('learning-plan', 'Learning path'), ('lesson-notes', 'Learning notes')]:
            current = ' aria-current="page"' if target == section else ''
            links.append(f'<a href="#{target}"{current}>{label}</a>')
        tabs = '<nav class="learning-tabs" aria-label="Learning pages">' + ''.join(links) + '</nav>'
        content = re.sub(r'(</h1>)', lambda heading: heading.group(0) + tabs, content, count=1)
    return f'<article id="{section}" class="page prose" hidden>{content}<p class="file-link"><a href="{path}">Open the editable notes ↗</a></p></article>'
# Refresh matching sections and stop if too few were found.
text,count=re.subn(pattern,replace,text,flags=re.S)
assert count==8,f'Expected eight canonical note sections, found {count}'
# Save the refreshed guide without rebuilding the task board.
page.write_text(text,encoding='utf-8')
print('Guide updated from the editable notes.')
