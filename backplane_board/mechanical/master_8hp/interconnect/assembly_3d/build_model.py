"""Build the 8 HP master review assembly in mm with FreeCAD's Python interpreter.
Usage: python build_model.py OUTPUT_DIR [existing-component-locations.csv]
Front datum X runs to the right; D goes rearward; Y runs down the front panel.
STEP axes are (X, D, 260.45-Y). Optional mesh/json is used for the drawing views.
"""
from pathlib import Path
import csv, itertools, json, math, sys, zipfile
import FreeCAD as A
import Part, Import
V=A.Vector
here=Path(__file__).resolve().parent
out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=True)
H=260.45
ports=list(csv.DictReader((here.parents[1]/'front_io_centres.csv').open(encoding='utf-8-sig')))
def pt(x,d,y):return V(x,d,H-y)
def b(x,d,y,w,depth,height):return Part.makeBox(w,depth,height,pt(x,d,y+height))
def cx(x,d,y,r,length):return Part.makeCylinder(r,length,pt(x,d,y),V(1,0,0))
def cd(x,d,y,r,length):return Part.makeCylinder(r,length,pt(x,d,y),V(0,1,0))
def comp(parts):return Part.makeCompound(parts)
def tube(points,r):
    q=[pt(*p) for p in points]
    seg=[Part.makeCylinder(r,(v-u).Length,u,v-u) for u,v in zip(q,q[1:])]
    return comp(seg+[Part.makeSphere(r,v) for v in q[1:-1]])
def flat_bundle(points):
    # 16 x 4.2 mm routing envelope, held flat parallel to the plane of M.
    q=8/2.1
    section=tube([(x*q,d,y) for x,d,y in points],8)
    matrix=A.Matrix();matrix.A11=1/q
    return section.transformGeometry(matrix)

palette={'M':'307e64','C':'2869ac','R':'42a4a4','L':'985ea9','E':'d08432','P':'c6a335','F':'a9b7c0','H':'596679'}
names={'M':'01 M - carrier','C':'02 C - controller','R':'03 R - optical receiver','L':'04 L - optical Tx and timing Rx','E':'05 E - Ethernet','P':'06 P - passive PLC','F':'07 metalwork','H':'08 removable harnesses'}
shapes={}; spec={}; boards={}; rows=[]; clash={}; status=[]
def put(key,g,shape,cls,color=None):
    assert not shape.isNull() and shape.isValid(),key
    shapes[key]=shape
    spec[key]={'g':g,'kind':cls,'color':color or palette[g]}
def check(label,a,bsh):
    if a.BoundBox.intersect(bsh.BoundBox):
        inter=a.common(bsh)
        v=0 if inter.isNull() else inter.Volume
    else:v=0
    if v>0.01:clash[label]=round(v,3)
    return v
# Through holes are proposals except the existing controller outline. Sheet metal
# uses plain holes and seat representations, not thread or fastener-detail models.
mounts={'M':[(48,26),(48,229)],'P':[(26,29),(26,139)],'R':[(29,22),(29,182)],
        'L':[(30,154),(30,240)],'E':[(31,195.3),(31,207)]}
def board(g,x,d,y,depth,height,extra=None):
    s=b(x,d,y,1.6,depth,height)
    if extra:s=extra(s)
    for dd,yy in mounts.get(g,[]):s=s.cut(cx(x-1,dd,yy,1.1,4))
    boards[g]=s
    put('PCB_'+g,g,s,'PCB')
    rows.append([g,names[g].split(' - ',1)[1],1,1.6,x,round(x+1.6,2),y,round(y+height,2),d,round(d+depth,2)])
board('M',6.97,0,13.55,160,233.35,lambda s:s.cut(b(6,-1,19,4,33,229)).cut(b(6,-1,31,4,43,50)))
board('C',13.57,48,75,68.4,145.05)
board('R',20.57,0,15,44,174)
board('L',15.57,0,149,44,98)
board('E',21.17,0,190.6,107,21.2)
board('P',14.4,0,24,31,121)
for a,g in itertools.combinations(boards,2):check('PCB '+a+'/'+g,boards[a],boards[g])
locations={'J7':(127,67),'J8':(127,111),'J9':(86,67),'J10':(86,111),'U1':(126,88.8),'U5':(84.22,88.66),
           'U2':(146,94),'J1':(168,98.7),'J3':(161,84.5),'J4':(124,104.5),'J6':(42,61)}
if len(sys.argv)>2:
    with open(sys.argv[2],encoding='utf-8-sig') as fp: file={r['Reference']:(float(r['X_mm']),float(r['Y_mm'])) for r in csv.DictReader(fp)}
    assert all(math.dist(pos,file[ref])<.001 for ref,pos in locations.items())
def source(ref):
    x,y=locations[ref]
    return 48+121.10-y,75+x-36
def device(ref,w,depth,height,col):
    d,y=source(ref)
    put(ref,'C',b(15.17,d-depth/2,y-height/2,w,depth,height),'device',col)
for r,sz in [('U1',14),('U2',10),('U5',23)]:device(r,1.6,sz,sz,'344352')
for r,depth,height in [('J4',13,9),('J6',10,9)]:device(r,5.1,depth,height,'424750')
# Seated interface bodies occupy the complete board-to-board gap.
mates={'XR':('M','R',8.57,12,38,95,7,24.6),'XL':('M','L',8.57,7,38,191,7,24.6),'XETH':('C','E',15.17,6,92,201.2,24.6,7)}
for r in ['J7','J8','J9','J10']:
    d,y=source(r);mates[r]=('M','C',8.57,5,d,y,6.6,30 if r in ['J9','J10'] else 25)
for r,(g1,g2,x,w,d,y,dep,h) in mates.items():
    s=b(x,d-dep/2,y-h/2,w,dep,h)
    put(r+'-mate',g2,s,'mate','d8c7a5')
    for g in boards:
        if g not in (g1,g2):check(r+' / PCB '+g,s,boards[g])
    for g in (g1,g2):assert s.distToShape(boards[g])[0]<.001,(r,g)
# Legacy J1/J3 are deliberately excluded from the installed assembly. Create a
# separate envelope and check each against the proposed E substrate.
old={}
for r,depth,height in [('J1',17.4,5.75),('J3',5.75,9.9)]:
    d,y=source(r);old[r]=b(15.17,d-depth/2,y-height/2,7,depth,height)
    overlap=old[r].common(boards['E']).Volume
    assert overlap>0
    status.append([r,'existing XH header intersects E',round(d,2),round(y,2),round(overlap,2)])
# Front panel: holes are review envelopes. PLC is an open window for both levers.
face=b(0,-2.2,0,40.34,2.2,H)
face=face.cut(b(4.65,-3,18.7,11,5,130.5))
for r in ports:
    x,y=float(r['x_from_left_mm']),float(r['y_from_top_mm'])
    tag,kind=r['label'],r['group']
    if kind=='PLC':
        g='P'
        sh=b(5.9,-3,y-22.35,8.5,19.5,44.7).cut(b(7.2,-4,y-14.8,5.3,7.7,29.6))
        for i in range(10):
            for j in range(2):
                sh=sh.fuse(b(8.6+j*2.54,-.9,y-11.7+i*2.54,.55,4.8,.55))
        # Lever positions are schematic, maximum operational span is separately checked.
        put(tag+'-PLC',g,sh,'port','435268');continue
    if kind=='RS':
        # Front nose inside the cutout; panel clamping flange behind it.
        face=face.cut(b(x-5.9,-3,y-10.3,11.8,5,20.6))
        for sy in (-12.495,12.495):face=face.cut(cd(x,-3,y+sy,1.5,5))
        shell=b(x-5.5,-4,y-9.6,11,10,19.2)
        shell=shell.fuse(b(x-6.25,0,y-15.4,12.5,1.2,30.8))
        for j,count in enumerate((5,4)):
            for i in range(count):shell=shell.cut(cd(x+(j-.5)*2.74,-5,y+(i-(count-1)/2)*2.74,.76,7))
        for sy in (-12.495,12.495):shell=shell.cut(cd(x,-.2,y+sy,1.5,2))
        put('DE9','H',shell,'port','9aa7af');continue
    if kind=='ETH':
        # Body is tied to the E surface; panel opening follows the existing panel datum.
        face=face.cut(b(x-7.75,-3,y-8.75,15.5,5,17.5))
        sh=b(22.77,-2.2,y-8.1,14.1,25.4,16.2).cut(b(24.4,-3.2,y-6.1,10.7,8,12.2))
        put('ETH-RJ45','E',sh,'port','8e9ba6')
        put('LAN8742A','E',b(22.77,48.5,y-2.25,.95,4.5,4.5),'device','344352');continue
    g='R' if tag.startswith('R') else 'L'
    # Package envelopes registered to panel axes. Exact optical-axis to solder
    # plane offsets must be obtained before a hole pattern can be released.
    w=float(r['body_W_mm_review'])
    h=float(r['body_H_mm_review'])
    dep=28.65 if kind=='SC' else 15.0
    # Hitachi only labels the three values as size. The X/Y/D assignment is provisional.
    if kind=='F06':
        assert sorted((w,h,dep)) == [11.0,13.4,15.0], (tag,w,h,dep)
    face=face.cut(b(x-w/2-.45,-3,y-h/2-.45,w+.9,5,h+.9))
    sh=b(x-w/2,-2.3,y-h/2,w,dep,h)
    if kind=='SC':sh=sh.cut(b(x-3.5,-3,y-4.15,7,7,8.3))
    else:sh=sh.cut(b(x-3.65,-3,y-4.5,7.3,5.2,9))
    if kind=='F06':
        bb=sh.BoundBox
        assert max(abs(v-ref) for v,ref in zip((bb.XLength,bb.ZLength,bb.YLength),(w,h,dep)))<1e-6
    put(tag+'-'+kind,g,sh,'port','38546a' if g=='R' else ('475968' if kind=='SC' else '70524d'))
    # Mount plane allowance, not measured package features.
    rear=22.17 if g=='R' else 15.57
    edge=x-w/2 if g=='R' else x+w/2
    if abs(edge-rear)>.02:
        put(tag+'-seat',g,b(min(edge,rear),4,y-2.2,abs(edge-rear),4,4.4),'seat','a9b2a4')
# Backplane sockets are on the separate backplane. Only mating envelope on M is shown.
for j,y in [('J2',63.55),('J3',196.9)]:
    put('BP-'+j,'M',b(1.77,159.9,y-41,12,11,82),'back','c5bda9')
# The metallic centre web carries load from the three mezzanines and PLC board.
# Enlarged ears connect to the carrier; spacers seat on backs of the front PCBs.
spine=b(17.9,0,9,1.5,32,243)
for d,y in mounts['M']:spine=spine.fuse(b(17.9,30,y-5,1.5,24,10))
for g,ps in mounts.items():
    for d,y in ps:
        spine=spine.cut(cx(16.6,d,y,1,4.5))
        a,bb={'M':(8.57,17.9),'P':(16,17.9),'R':(19.4,20.57),'L':(17.17,17.9),'E':(19.4,21.17)}[g]
        sp=cx(a,d,y,2.35,bb-a).cut(cx(a-.3,d,y,1.05,bb-a+.6))
        put(f'spacer-{g}-{y}','F',sp,'fix','bdab87')
for y in (11,130,249):
    foot=b(17.32,0,y-2.3,3.06,5.8,4.6).cut(cd(18.85,-.3,y,.85,6.4))
    spine=spine.fuse(foot)
    spine=spine.cut(cd(18.85,-.3,y,.85,6.4))
    face=face.cut(cd(18.85,-3,y,1.1,4))
put('support-spine','F',spine.removeSplitter(),'metal','a5adb1')
put('front-panel','F',face,'metal','aab8c1')
# Connectors and in-card harness centre lines. Conductors and crimp contacts
# are not represented. Radii are bundle envelopes, to be checked on the chosen cable.
paths={'H-PI':[(10.3,25,47),(10.45,30,47),(11.2,38,46),(13.5,48,44),(13,57,44)],
       'H-PO':[(10.3,25,113),(10.6,24,108),(10.6,24,76),(10.8,33,71),(13.5,46,64),(13,57,64)],
       'H-RS':[(30.15,5.5,230.8),(30.15,16,230.8),(30.15,51,230.8),(26,55,232),(18,60,236),(12.7,65,238)]}
for name,points in paths.items():
    rad=1.65 if name=='H-RS' else 2.35
    clr={'H-PI':'d9a737','H-PO':'bc7140','H-RS':'5177ae'}[name]
    sh=tube(points,rad) if name=='H-RS' else flat_bundle(points)
    put(name,'H',sh,'harness',clr)
    sy=points[-1][2];dd=68 if name=='H-RS' else 60
    put(name+'-parent','M',b(8.57,dd-3.5,sy-(5 if name=='H-RS' else 9),6,7,(10 if name=='H-RS' else 18)),'socket','68717a')
    if name!='H-RS':
        put(name+'-front','P',b(8.5,21,points[0][2]-9,5.9,8,18),'socket','68717a')
# Check all separate PCBs against foreign installed bodies, all harnesses and the metalwork.
for k,s in shapes.items():
    kind=spec[k]['kind']
    if kind not in ('device','port','fix','metal','harness','back','socket'):continue
    for g,pcb in boards.items():
        if spec[k]['g']!=g:check(k+' / PCB '+g,s,pcb)
for h in paths:
    for k,s in shapes.items():
        if k==h or k in (h+'-parent',h+'-front') or h=='H-RS' and k=='DE9':continue
        if spec[k]['kind'] in ('mate','metal','socket','back','port','device','harness','fix'):check(h+' / '+k,shapes[h],s)
for k,sh in shapes.items():
    if spec[k]['kind'] in ('port','mate','device','socket','back','seat'):
        for metal in ('front-panel','support-spine'):check(k+' / '+metal,sh,shapes[metal])
# Physical intersection of other seated components, excluding conductive contact
# within the same group, the deliberate mate/host and RJ jack/board contacts.
for k,j in itertools.combinations([k for k in shapes if spec[k]['kind'] in ('port','mate','device','socket','back')],2):
    if spec[k]['g']!=spec[j]['g']:check(k+' / '+j,shapes[k],shapes[j])
service=[]
for a,c in itertools.combinations(ports,2):
    gap=[]
    for v,attr in [('x_from_left_mm','service_W_mm'),('y_from_top_mm','service_H_mm')]:
        gap.append(max(0,abs(float(a[v])-float(c[v]))-(float(a[attr])+float(c[attr]))/2))
    service.append((round(math.hypot(*gap),3),a['label'],c['label']))
service.sort()
watch=[('H-PO','XR-mate'),('H-PO','PCB_P'),('H-PO','support-spine'),('H-PI','PCB_P'),('H-RS','PCB_L'),('PCB_R','PCB_E'),('PCB_M','PCB_C'),('PCB_C','PCB_E')]
clearance={a+' / '+b:round(shapes[a].distToShape(shapes[b])[0],3) for a,b in watch}
report={'F06_housing_review_X_Y_D_mm':[11.0,13.4,15.0], 'F06_axis_assignment':'provisional; catalog does not identify axes', 'selected_clearances_mm':clearance,'pcbs':rows,'removed_header_envelopes':status,'front_service_min':service[:8],'unexpected_intersections_mm3':clash,
        'route_mm_without_slack':{h:round(sum(math.dist(a,bp) for a,bp in zip(p,p[1:])),1) for h,p in paths.items()},
        'board_pairs_checked':15,'fx10_fx8c_interfaces_checked':len(mates)}
(out/'fit_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'))
print(report,flush=True)
assert not clash,'Unexpected overlaps; inspect fit_report.json.'
def rgb_hex(s):return tuple(int(s[i:i+2],16)/255 for i in (0,2,4))
doc=A.newDocument('Master8HP')
asm=doc.addObject('App::Part','Assembly');asm.Label='PSCONT master 8 HP - packaging concept'
groups={}
for g,title in names.items():
    obj=doc.addObject('App::Part','Group'+g);obj.Label=title;asm.addObject(obj);groups[g]=obj
mesh={}
for k,s in shapes.items():
    a=doc.addObject('Part::Feature','Item');a.Label=k;a.Shape=s;groups[spec[k]['g']].addObject(a)
    if a.ViewObject:a.ViewObject.ShapeColor=rgb_hex(spec[k]['color'])
for k,s in {**shapes,**{'old_'+r:t for r,t in old.items()}}.items():
    vs,fs=s.tessellate(.18)
    mesh[k]={**spec.get(k,{'g':'OLD','kind':'old','color':'e54f40'}),
             'v':[[round(p.x,3),round(p.y,3),round(p.z,3)] for p in vs],'f':fs}
(out/'review_mesh.json').write_text(json.dumps(mesh,separators=(',',':')),encoding='utf8')
doc.recompute()
step=out/'master_8hp.step'
Import.export([asm],str(step))
test=Part.read(str(step));assert test.isValid() and len(test.Solids)==sum(len(s.Solids) for s in shapes.values())
with zipfile.ZipFile(out/'master_8hp_STEP.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(step,step.name)
print('STEP round-trip:',len(test.Solids),'solids',test.BoundBox,flush=True)
