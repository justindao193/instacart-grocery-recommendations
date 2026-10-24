"""Embed illustrative product photos and the official carrot without changing recommendations."""
from pathlib import Path
import base64
import concurrent.futures
import hashlib
import json
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / '03_Code/05_Prototype/buy_again_prototype.html'
CARROT_URL = 'https://c-p.rmcdn.net/63d2c2d8d65c47001a318829/Favicon-26d90009-2b46-42df-aa7a-811d4a683751_144.png'

# Stock images illustrate the product type; they aren't exact branded pack shots.
NEW_PHOTOS = {
    '196': ('photo-1629654613528-5d0a2e4166de', 'https://unsplash.com/s/photos/cola-glass'),
    '46149': ('photo-1629654613528-5d0a2e4166de', 'https://unsplash.com/s/photos/cola-glass'),
    '12427': ('photo-1652209695374-7a91c243f12f', 'https://unsplash.com/photos/nlBelQEqwZQ'),
    '10258': ('photo-1772986754122-06ea7269829d', 'https://unsplash.com/photos/a-pile-of-shelled-pistachios-on-a-white-background-jTS_QwTU_b4'),
    '25133': ('photo-1635407723462-10c0871194a1', 'https://unsplash.com/s/photos/string-cheese'),
    '13032': ('photo-1766185387810-913a19970398', 'https://unsplash.com/photos/bowl-of-cereal-with-milk-and-scattered-pieces-PFiQjQCGFz4'),
    '15680': ('photo-1761281161391-09114b626538', 'https://unsplash.com/photos/many-red-plastic-cups-arranged-on-a-surface-ExuGV-lcpNc'),
    '26088': ('photo-1512149177596-f817c7ef5d4c', 'https://unsplash.com/photos/photo-of-popcorn-kernels-PvAAYZx-yf8'),
    '26405': ('photo-1632334994199-cc2ba6538141', 'https://unsplash.com/s/photos/paper-towel'),
    '30450': ('photo-1654747780295-aa29ff49f5c0', 'https://unsplash.com/photos/a-jar-of-almonds-next-to-a-jar-of-peanut-butter-6ULWRSeAMaU'),
    '39657': ('photo-1646151067116-80a86e5eee69', 'https://unsplash.com/s/photos/chocolate-almonds'),
}
REUSE = {'14084': '24838', '35951': '24838', '10326': '45066',
         '17122': '45066', '38928': '24535', '41787': '22825'}


def read_url(url):
    with urllib.request.urlopen(url, timeout=25) as response:
        data = response.read()
    assert len(data) > 1000
    return data


def main():
    # Keep the existing styles and embedded real-history data exactly as supplied.
    page = PAGE.read_text(encoding='utf-8')
    styles = re.findall(r'<style\b[^>]*>.*?</style>', page, re.S)
    data_block = re.search(r'/\* DEMO_DATA_START.*?/\* DEMO_DATA_END \*/', page, re.S).group(0)
    payload = json.loads(re.search(r'const DEMO_DATA = (.*?);\n', page).group(1))
    photo_match = re.search(r'const PHOTOS = (\{.*?\});', page, re.S)
    photos = json.loads(photo_match.group(1))
    old_photos = dict(photos)

    # Download each distinct photo once and embed it for offline use.
    urls = {photo: f'https://images.unsplash.com/{photo}?w=320&h=320&fit=crop&auto=format&q=75&fm=jpg'
            for photo, source in NEW_PHOTOS.values()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        downloaded = dict(zip(urls, pool.map(read_url, urls.values())))
    manifest = {}
    for product_id, (photo, source) in NEW_PHOTOS.items():
        data = downloaded[photo]
        assert data.startswith(b'\xff\xd8')
        photos[product_id] = 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
        manifest[product_id] = {'source_page': source, 'image_url': urls[photo],
                                'sha256': hashlib.sha256(data).hexdigest()}
    for product_id, old_id in REUSE.items():
        assert old_id in photos
        photos[product_id] = photos[old_id]
        manifest[product_id] = {'reused_existing_photo_for_product': int(old_id)}
    page = page[:photo_match.start(1)] + json.dumps(photos, separators=(',', ':')) + page[photo_match.end(1):]

    # Reuse the official wordmark when saved locally; keep the carrot as the browser icon.
    carrot = read_url(CARROT_URL)
    assert carrot.startswith(b'\x89PNG\r\n\x1a\n')
    (ROOT / '03_Code/05_Prototype/assets/instacart_carrot.png').write_bytes(carrot)
    icon = 'data:image/png;base64,' + base64.b64encode(carrot).decode()
    logo = (f'<a class="logo" href="#" data-home="true" aria-label="Home">'
            f'<img src="{icon}" alt="" width="28" height="28" style="margin-right:8px">'
            '<span class="txt">instacart</span></a>')
    logo_file = ROOT / '03_Code/05_Prototype/assets/instacart_logo.svg'
    if logo_file.exists():
        official = base64.b64encode(logo_file.read_bytes()).decode()
        logo = (f'<a class="logo" href="#" data-home="true" aria-label="Home">'
                f'<img src="data:image/svg+xml;base64,{official}" alt="Instacart" width="150" height="24"></a>')
    page, count = re.subn(r'<a class="logo".*?</a>', lambda _: logo, page, count=1, flags=re.S)
    assert count == 1
    page = re.sub(r'<link\b[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*>\s*', '', page, flags=re.I)
    page = page.replace('</title>', f'</title>\n<link rel="icon" type="image/png" href="{icon}">', 1)
    assert re.findall(r'<style\b[^>]*>.*?</style>', page, re.S) == styles
    assert re.search(r'/\* DEMO_DATA_START.*?/\* DEMO_DATA_END \*/', page, re.S).group(0) == data_block
    assert all(photos[key] == value for key, value in old_photos.items() if key not in NEW_PHOTOS and key not in REUSE)
    candidates = {str(item[0]) for shopper in payload['shoppers'].values() for item in shopper['ranked']}
    assert candidates <= photos.keys()
    PAGE.write_text(page, encoding='utf-8')

    # Save source notes, without including any additional customer history.
    sources = {'photo_usage': 'Illustrative product-type photos under the Unsplash License, not exact packaging. Cheese, cereal and chocolate photos show the category rather than the exact format.',
               'license': 'https://unsplash.com/license', 'products': manifest,
               'carrot': {'source_page': 'https://heyitsinstacart.com/logo/',
                          'asset_url': CARROT_URL, 'sha256': hashlib.sha256(carrot).hexdigest(),
                          'note': 'Unmodified official public brand-site carrot icon, also used as the browser-tab icon.'}}
    existing_sources = ROOT / '01_Project/Assets/prototype_image_sources.json'
    if existing_sources.exists():
        previous = json.loads(existing_sources.read_text(encoding='utf-8'))
        if 'header_logo' in previous:
            sources['header_logo'] = previous['header_logo']
    (ROOT / '01_Project/Assets/prototype_image_sources.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'passed', 'real_candidate_photos': len(candidates),
                      'photo_entries_added_or_updated': len(manifest), 'carrot_embedded': True,
                      'recommendations_unchanged': True, 'styles_unchanged': True}))


if __name__ == '__main__':
    main()
