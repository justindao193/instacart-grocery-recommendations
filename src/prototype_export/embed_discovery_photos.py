"""Embed illustrative discovery photos without changing recommendations."""
from pathlib import Path
import base64,hashlib,json,re,urllib.request
ROOT=Path(__file__).resolve().parents[2]
PHOTOS={
 '45051':('https://images.pexels.com/photos/20505049/pexels-photo-20505049.jpeg?w=320','https://www.pexels.com/photo/bowl-of-snack-on-table-20505049/','https://www.pexels.com/license/'),
 '37710':('https://images.unsplash.com/photo-1579294087362-3262c0c734c7?w=320&h=320&fit=crop&fm=jpg&q=80','https://unsplash.com/photos/trinity-trail-bXvQL2yvtoE','https://unsplash.com/license'),
 '6184':('https://images.unsplash.com/photo-1543076659-9380cdf10613?w=320&h=320&fit=crop&fm=jpg&q=80','https://unsplash.com/photos/orange-fruits-qSkWlOBHia0','https://unsplash.com/license'),
 '41400':('https://images.pexels.com/photos/3026806/pexels-photo-3026806.jpeg?w=320','https://www.pexels.com/photo/top-view-photo-of-granola-bars-3026806/','https://www.pexels.com/license/')}
def main():
 page=ROOT/'03_Code/05_Prototype/grocery_recommendations_prototype.html'
 old=page.read_text(encoding='utf-8');match=re.search(r'const PHOTOS = (\{.*?\});',old,re.S)
 photos=json.loads(match[1]);entries={}
 # Download and verify real photo bytes, then embed for offline use.
 for pid,(url,source,license) in PHOTOS.items():
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as response:data=response.read()
  assert data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9') and len(data)>1000
  dest=ROOT/'03_Code/05_Prototype/assets'/('discovery_'+pid+'.jpg');dest.write_bytes(data)
  photos[pid]='data:image/jpeg;base64,'+base64.b64encode(data).decode()
  entries[pid]={'source_page':source,'image_url':url,'license':license,'sha256':hashlib.sha256(data).hexdigest(),'usage':'Illustrative product type, not exact branded packaging.'}
 photos['13575']=photos['10326']
 entries['13575']={'reused_existing_photo_for_product':10326,'usage':'Illustrative apples photo, not a verified exact variety.'}
 updated=old[:match.start(1)]+json.dumps(photos,separators=(',',':'))+old[match.end(1):]
 # Compare everything outside the photo map, including all recommendation data.
 new_match=re.search(r'const PHOTOS = (\{.*?\});',updated,re.S)
 assert old[:match.start(1)]==updated[:new_match.start(1)]
 assert old[match.end(1):]==updated[new_match.end(1):]
 page.write_text(updated,encoding='utf-8')
 manifest=ROOT/'01_Project/Assets/prototype_image_sources.json'
 sources=json.loads(manifest.read_text(encoding='utf-8'));sources.setdefault('products',{}).update(entries)
 manifest.write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
 report={'status':'passed','new_photo_ids':list(entries),'images_verified':True,'recommendations_and_other_code_unchanged':True,'discovery_count':5,'note':'Embedded stock photos; source/license links saved in image manifest. No browser visual QA claimed.'}
 (ROOT/'05_Results/03_Checks/discovery_photos.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report)
if __name__=='__main__':main()
