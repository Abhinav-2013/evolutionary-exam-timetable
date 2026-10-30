from PIL import Image, ImageDraw
from pathlib import Path
p=Path('output/exam_timetable_project_presentation')
files=sorted(p.glob('slide-*.png'),key=lambda f:int(f.stem.split('-')[1]))
out=Image.new('RGB',(1320,5*400),(245,247,250)); d=ImageDraw.Draw(out)
for i,f in enumerate(files):
    im=Image.open(f).convert('RGB'); im.thumbnail((640,360))
    x=10+(i%2)*655; y=10+(i//2)*400
    out.paste(im,(x,y+22)); d.text((x,y),f.name,fill=(30,40,60))
out.save('output/slides_montage.png')
