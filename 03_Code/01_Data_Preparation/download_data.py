# Load the Python tools used by this script.
from pathlib import Path
import concurrent.futures, hashlib, json, time, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'02_Data/01_Original'
AUDIT=ROOT/'05_Results/03_Checks'
RAW.mkdir(parents=True,exist_ok=True)
AUDIT.mkdir(parents=True,exist_ok=True)
# These are the six source files and the archive checksums used to verify them.
FILES={
 'aisles.csv':'bc49e521faa60e1542d4a94cac3e3bb0',
 'departments.csv':'18d5219db49bd50b403d39016c3ecdc5',
 'orders.csv':'dd0b2f4ee716409b8e79e7b1c611a0b8',
 'products.csv':'dfcfded9d4af77d8b747913a4cbe6ffc',
 'order_products__prior.csv':'8bca7ad1968ee8e07760b94db74461fb',
 'order_products__train.csv':'5d8f7580855097e3644ea626ee430b75',
}
# Calculate file fingerprints so we can check that a download is complete.
def hashes(path):
    md5=hashlib.md5(); sha=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''): md5.update(chunk);sha.update(chunk)
    return md5.hexdigest(),sha.hexdigest()
# Download one file only if a matching local copy is not already available.
def download(item):
    name,expected=item
    path=RAW/name
    url=f'https://zenodo.org/records/2654444/files/{name}?download=1'
    # Keep incomplete downloads in a temporary file until the checksum passes.
    if not path.exists() or hashes(path)[0]!=expected:
        part=path.with_suffix('.csv.part')
        print(f'Downloading {name}',flush=True)
        request=urllib.request.Request(url,headers={'User-Agent':'Instacart-Portfolio-Learning/1.0'})
        with urllib.request.urlopen(request,timeout=90) as response,part.open('wb') as output:
            while chunk:=response.read(4*1024*1024): output.write(chunk)
        md5,sha=hashes(part)
        if md5!=expected: raise ValueError(f'{name}: archive checksum mismatch')
        part.replace(path)
    md5,sha=hashes(path)
    print(f'Checked {name}: {path.stat().st_size:,} bytes',flush=True)
    return name,{'url':url,'bytes':path.stat().st_size,'md5':md5,'sha256':sha,'archive_md5_match':True}

# Download or check up to three files at the same time.
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    files=dict(pool.map(download,FILES.items()))
# Record the source, retrieval details, limitations and file fingerprints.
manifest={
 'dataset':'The Instacart Online Grocery Shopping Dataset 2017',
 'original_publisher':'Instacart','release_date':'2017-05-03',
 'release_article':'https://tech.instacart.com/3-million-instacart-orders-open-sourced-d40d29ead6f2',
 'dictionary':'https://gist.github.com/jeremystan/c3b39d947d9b88b3ccff3147dbcf6c6b',
 'terms':'https://gist.github.com/jeremystan/582eba13d6ee27ed465c43dc78934700',
 'retrieval_date':datetime.now(ZoneInfo('America/Toronto')).date().isoformat(),'retrieval_archive':'https://zenodo.org/records/2654444',
 'archive_creator':'Xiaoyu Wang; archive uploaded 2019-04-30',
 'retrieval_note':'Original release S3 URL returned HTTP 403. Files retrieved from a third-party Zenodo archive and matched its published MD5 checksums. Original-file equivalence cannot be independently certified against the unavailable publisher download.',
 'sample_warning':'Instacart describes this as a heavily biased subset, not representative of its users/products/purchasing behaviour.',
 'use_note':'Local non-commercial learning project. Do not redistribute raw data or a report containing recoverable row-level data. Retain original attribution and review original terms before public release.',
 'files':files,
}
# Save the source record so the dataset provenance can be checked later.
(AUDIT/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('All six source CSVs downloaded and checked.',flush=True)
