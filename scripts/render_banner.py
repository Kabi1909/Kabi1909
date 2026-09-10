from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
W,H = 1200,460
FONT_DIR = Path("C:/Windows/Fonts")
def font(n,bold=False):
    return ImageFont.truetype(str(FONT_DIR / ("seguibl.ttf" if bold else "segoeui.ttf")),n)
Y,X=np.mgrid[0:H,0:W]
glow=np.exp(-((X-950)**2/210000+(Y-150)**2/70000))
bg=np.zeros((H,W,3),dtype=np.uint8)
for k,(a,b) in enumerate([(9,15),(16,16),(31,39)]): bg[:,:,k]=a+b*glow
base=Image.fromarray(bg)
d=ImageDraw.Draw(base)
d.rounded_rectangle((1,1,W-2,H-2),radius=22,outline="#293953",width=2)
for x in range(780,1200,38):
    for y in range(40,425,38): d.ellipse((x,y,x+2,y+2),fill="#29314b")
d.text((64,42),"K / 19",font=font(22,True),fill="#8be8ef")
d.text((175,48),"DEVELOPER PROFILE",font=font(15),fill="#97a7bd")
d.rounded_rectangle((844,38,1136,77),radius=19,fill="#152d35",outline="#26515c")
d.ellipse((863,53,871,61),fill="#73e7bd")
d.text((884,46),"OPEN TO INTERNSHIPS",font=font(16,True),fill="#a5efd6")
d.text((67,110),"HELLO, I'M",font=font(19,True),fill="#a2b4cb")
d.text((67,285),"Aspiring Full-Stack Developer",font=font(29,True),fill="#edf5ff")
d.text((67,331),"IT undergraduate  /  University of Vavuniya",font=font(22),fill="#9babbe")
d.line((65,391,1135,391),fill="#29344b",width=1)
d.text((67,412),"MERN STACK",font=font(15,True),fill="#77dbe8")
d.text((245,412),"THOUGHTFUL INTERFACES. USEFUL SOFTWARE.",font=font(15),fill="#93a4bd")
d.text((1020,412),"Kabi1909",font=font(15),fill="#93a4bd")
mask=Image.new("L",(750,150))
ImageDraw.Draw(mask).text((0,-22),"KABIjAKE".upper(),font=font(124,True),fill=255)
bbox=mask.getbbox()
mask=mask.crop(bbox)
tw,th=mask.size
# A shared text mask is projected through a moving 3D plane. Multiple
# depth slices form the extrusion; a moving light sweeps across the face.
def project(x,y,z,angle):
    xx=x*math.cos(angle)+z*math.sin(angle)
    zz=-x*math.sin(angle)+z*math.cos(angle)
    yy=y*math.cos(-.12)-zz*math.sin(-.12)
    zz=y*math.sin(-.12)+zz*math.cos(-.12)
    s=1400/(1400+zz)
    return (405+xx*s,206+yy*s)
def coeffs(dst,src):
    rows=[]; vals=[]
    for (x,y),(u,v) in zip(dst,src):
        rows += [[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]
        vals += [u,v]
    return np.linalg.solve(np.array(rows),np.array(vals))
def warp(layer,z,a):
    src=[(0,0),(tw,0),(tw,th),(0,th)]
    dst=[project(x-tw/2,y-th/2,z,a) for x,y in src]
    return layer.transform((W,H),Image.Transform.PERSPECTIVE,coeffs(dst,src),Image.Resampling.BICUBIC)
def cube(draw,cx,cy,size,t):
    pts=[]
    for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
        xx=x*math.cos(t)+z*math.sin(t); zz=-x*math.sin(t)+z*math.cos(t)
        yy=y*.86-zz*.5; zz=y*.5+zz*.86
        s=4/(4+zz*.25)
        pts.append((cx+xx*size*s,cy+yy*size*s,zz))
    faces=[([0,1,2,3],"#203452"),([4,5,6,7],"#345374"),([0,1,5,4],"#507995"),([2,3,7,6],"#2c385b"),([1,2,6,5],"#426380"),([0,3,7,4],"#253753")]
    for idx,col in sorted(faces,key=lambda f:sum(pts[i][2] for i in f[0]),reverse=True):
        xy=[pts[i][:2] for i in idx]
        draw.polygon(xy,fill=col)
        draw.line(xy+[xy[0]],fill="#7dcbdc",width=2)
frames=[]
for i in range(80):
    t=i/80*2*math.pi
    a=-.12+.09*math.sin(t)
    im=base.copy().convert("RGBA")
    # Perspective floor and floating architectural geometry.
    dd=ImageDraw.Draw(im)
    dd.ellipse((870,302,1130,331),fill="#101a2e",outline="#283a56",width=2)
    dd.arc((866,177,1138,282),0,360,fill="#3c4c71",width=2)
    cube(dd,1001,219+9*math.sin(t),65,.5+t)
    cube(dd,865,152+6*math.sin(t+1),19,-t*.5)
    cube(dd,1122,300+5*math.sin(t+2),14,t*.5)
    for z in range(20,-1,-2):
        col=(31+z,67+z,109+z,255)
        layer=Image.new("RGBA",(tw,th),col);layer.putalpha(mask)
        im.alpha_composite(warp(layer,z,a))
    yy,xx=np.mgrid[0:th,0:tw]
    light=np.exp(-((xx/tw-(.5+.45*math.sin(t)))/.17)**2)
    face=np.zeros((th,tw,4),dtype=np.uint8)
    for k,(top,bottom) in enumerate([(211,82),(244,154),(255,226)]):
        face[:,:,k]=np.clip(top+(bottom-top)*(yy/th)+28*light,0,255)
    face[:,:,3]=np.array(mask)
    im.alpha_composite(warp(Image.fromarray(face),0,a))
    rgb=im.convert("RGB")
    frames.append(rgb)
# Use a single palette to avoid frame-to-frame color flicker.
palette=frames[0].quantize(colors=128,method=Image.Quantize.MEDIANCUT)
indexed=[fr.quantize(palette=palette,dither=Image.Dither.NONE) for fr in frames]
indexed[0].save(OUT/"kabijake-3d.gif",save_all=True,append_images=indexed[1:],duration=80,loop=0,optimize=True,disposal=1)
frames[0].save(OUT/"kabijake-3d.png")
print(f"Created {len(frames)} frames; GIF: {(OUT/'kabijake-3d.gif').stat().st_size:,} bytes")
