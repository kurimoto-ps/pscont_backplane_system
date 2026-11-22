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
names={'M':'01 M - optical carrier','C':'02 C - controller','E':'03 E - Ethernet','P':'04 P - passive PLC','F':'05 metalwork','H':'06 removable harnesses'}
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
mounts={'M':[(48,26),(39,143),(48,243)],'P':[(26,29),(26,139)],'E':[(31,195.3),(31,207)]}

def board(g,x,d,y,depth,height,extra=None):
    s=b(x,d,y,1.6,depth,height)
    if extra:s=extra(s)
    for dd,yy in mounts.get(g,[]):s=s.cut(cx(x-1,dd,yy,1.1,4))
    boards[g]=s
    put('PCB_'+g,g,s,'PCB')
    rows.append([g,names[g].split(' - ',1)[1],1,1.6,x,round(x+1.6,2),y,round(y+height,2),d,round(d+depth,2)])
board('M',6.97,0,13.55,160,233.35)
board('C',13.57,48,75,68.4,145.05)
board('E',22.17,0,190.6,107,21.2)
board('P',36.25,0,24,31,121)
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
mates={'XETH':('C','E',15.17,7,92,201.2,24.6,7)}
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
    assert overlap<0.001 and old[r].distToShape(boards['E'])[0]<0.001
    status.append([r,'nominal clearance to E = 0 mm; relocate for tolerance and mating',round(d,2),round(y,2),round(overlap,2)])
# Front panel: holes are review envelopes. PLC is an open window for both levers.
face=b(0,-2.2,0,40.34,2.2,H)
face=face.cut(b(26.5,-3,18.7,11,5,130.5))
for r in ports:
    x,y=float(r['x_from_left_mm']),float(r['y_from_top_mm'])
    tag,kind=r['label'],r['group']
    if kind=='PLC':
        g='P'
        sh=b(27.75,-3,y-22.35,8.5,19.5,44.7).cut(b(29.05,-4,y-14.8,5.3,7.7,29.6))
        for i in range(10):
            for j in range(2):
                sh=sh.fuse(b(30.45+j*2.54,-.9,y-11.7+i*2.54,.55,4.8,.55))
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
        sh=b(23.77,-2.2,y-8.1,14.1,25.4,16.2).cut(b(25.4,-3.2,y-6.1,10.7,8,12.2))
        put('ETH-RJ45','E',sh,'port','8e9ba6')
        put('LAN8742A','E',b(23.77,48.5,y-2.25,.95,4.5,4.5),'device','344352');continue
    g='M'
    w=float(r['body_W_mm_review'])
    h=float(r['body_H_mm_review'])
    if kind=='F06':
        # DR9300 Rev.0, p.4. The board stands perpendicular to the panel;
        # the package width lies along panel Y, its seated height along X.
        # Reuse the receiver outline provisionally for the three DS transmitters.
        assert (w,h)==(13.4,11)
        center_x=float(r['body_center_X_mm_review'])
        nose=float(r['nose_span_Y_mm_review'])
        mounted_x=boards[g].BoundBox.XMax
        assert abs(center_x-(mounted_x+w/2))<1e-6 and nose==9
        front=-2.3
        dep=15
        shoulder=7.1
        # Use the enclosing rear step for the short transition to the full width.
        sh=b(mounted_x,front,y-nose/2,w,shoulder,nose).fuse(
            b(mounted_x,front+shoulder,y-h/2,w,dep-shoulder,h)).removeSplitter()
        # Only the narrow nose crosses the panel. This is a packaging study cut.
        face=face.cut(b(mounted_x-.45,-3,y-nose/2-.45,w+.9,5,nose+.9))
        assert sh.distToShape(boards[g])[0]<1e-6
        bb=sh.BoundBox
        assert max(abs(v-ref) for v,ref in zip((bb.XLength,bb.ZLength,bb.YLength),(w,h,dep)))<1e-6
        put(tag+'-'+kind,g,sh,'port','467893' if tag.startswith('R') else 'a56449')
        continue
    dep=28.65
    face=face.cut(b(x-w/2-.45,-3,y-h/2-.45,w+.9,5,h+.9))
    sh=b(x-w/2,-2.3,y-h/2,w,dep,h).cut(b(x-3.5,-3,y-4.15,7,7,8.3))
    put(tag+'-'+kind,g,sh,'port','475968')
    assert sh.distToShape(boards['M'])[0]<1e-6
# Backplane sockets are on the separate backplane. Only mating envelope on M is shown.
for j,y in [('J2',63.55),('J3',196.9)]:
    put('BP-'+j,'M',b(1.77,159.9,y-41,12,11,82),'back','c5bda9')
# A front bracket supports P and the carrier near the optical bank. Two
# separate lower brackets leave the SC bodies and the Ethernet jack clear.
brackets=[
    ('upper',24.2,23,123,[(48,26),(39,143)],['P'],[25,136]),
    ('ethernet',19.6,190,22,[],['E'],[193,208]),
    ('lower',19.6,240,6,[(48,243)],[],[243])]
metal_keys=['front-panel']
for name,x,y0,span,carrier,others,feet in brackets:
    web=b(x,0,y0,1.5,32,span)
    for d,y in carrier:web=web.fuse(b(x,30,y-2.8,1.5,d-26,5.6))
    for g,holes in [('M',carrier)]+[(g,mounts[g]) for g in others]:
        for d,y in holes:
            web=web.cut(cx(x-.5,d,y,1,2.5))
            a,z=(8.57,x) if g=='M' else (x+1.5,boards[g].BoundBox.XMin)
            sp=cx(a,d,y,2.35,z-a).cut(cx(a-.3,d,y,1.05,z-a+.6))
            put(f'spacer-{g}-{y}','F',sp,'fix','bdab87')
    for y in feet:
        xx=x+.75
        web=web.fuse(b(xx-1.3,0,y-1.75,2.6,5,3.5)).cut(cd(xx,-.5,y,.85,6))
        face=face.cut(cd(xx,-3,y,1.1,4))
    key='bracket-'+name
    put(key,'F',web.removeSplitter(),'metal','a5adb1');metal_keys.append(key)
put('front-panel','F',face,'metal','aab8c1')
# Connectors and in-card harness centre lines. Conductors and crimp contacts
# are not represented. Radii are bundle envelopes, to be checked on the chosen cable.
paths={'H-PI':[(32,25,47),(32,36,47),(32,47,46),(20,50,44),(13,57,44)],
       'H-PO':[(32,25,113),(32,42,113),(32,45,79),(31,47,66),(21,51,64),(13,57,64)],
       'H-RS':[(30.65,5.5,230.8),(30.65,16,230.8),(30.65,51,230.8),(26,55,232),(18,60,236),(12.7,65,238)]}
for name,points in paths.items():
    rad=1.65 if name=='H-RS' else 2.35
    clr={'H-PI':'d9a737','H-PO':'bc7140','H-RS':'5177ae'}[name]
    sh=tube(points,rad) if name=='H-RS' else flat_bundle(points)
    put(name,'H',sh,'harness',clr)
    sy=points[-1][2];dd=68 if name=='H-RS' else 60
    put(name+'-parent','M',b(8.57,dd-3.5,sy-(5 if name=='H-RS' else 9),6,7,(10 if name=='H-RS' else 18)),'socket','68717a')
    if name!='H-RS':
        put(name+'-front','P',b(30.35,21,points[0][2]-9,5.9,8,18),'socket','68717a')
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
        for metal in metal_keys:check(k+' / '+metal,sh,shapes[metal])
# Check neighbouring components even when they share a host PCB.
for k,j in itertools.combinations([k for k in shapes if spec[k]['kind'] in ('port','mate','device','socket','back')],2):
    check(k+' / '+j,shapes[k],shapes[j])
service=[]
for a,c in itertools.combinations(ports,2):
    gap=[]
    for v,attr in [('x_from_left_mm','service_W_mm'),('y_from_top_mm','service_H_mm')]:
        gap.append(max(0,abs(float(a[v])-float(c[v]))-(float(a[attr])+float(c[attr]))/2))
    service.append((round(math.hypot(*gap),3),a['label'],c['label']))
service.sort()
optic=[r['label']+'-'+r['group'] for r in ports if r['group'] in ('F06','SC')]
assert len(optic)==16
optical_bounds=[shapes[key].BoundBox for key in optic]
row_bounds=[round(H-max(bb.ZMax for bb in optical_bounds),3),
            round(H-min(bb.ZMin for bb in optical_bounds),3)]
parent_bounds=boards['M'].BoundBox
edge_margins=[round(row_bounds[0]-(H-parent_bounds.ZMax),3),
              round(H-parent_bounds.ZMin-row_bounds[1],3)]
assert min(edge_margins)>0
for key in optic:
    assert shapes[key].distToShape(boards['M'])[0]<1e-6
    assert shapes[key].common(boards['M']).Volume<1e-6
watch=[('R1-F06','R2-F06'),('R10-F06','T1-F06'),('T3-F06','S1-SC'),('S1-SC','S2-SC'),
       ('H-PO','bracket-upper'),('H-PI','bracket-upper'),('PCB_M','PCB_C'),('PCB_C','PCB_E')]
clearance={a+' / '+b:round(shapes[a].distToShape(shapes[b])[0],3) for a,b in watch}
report={'F06_housing_review_X_Y_D_mm':[13.4,11.0,15.0], 'DR9300_basis':'Delivery specification Rev.0 p.4; 11 mm width along panel Y, 13.1+0.3 seated height along X. DS transfer provisional', 'DR9300_nose_width_and_length_mm':[9.0,7.1], 'DR_row_min_body_gap_mm':round(shapes['R1-F06'].distToShape(shapes['R2-F06'])[0],2), 'selected_clearances_mm':clearance,'pcbs':rows,'removed_header_envelopes':status,'front_service_min':service[:8],'unexpected_intersections_mm3':clash,
        'route_mm_without_slack':{h:round(sum(math.dist(a,bp) for a,bp in zip(p,p[1:])),1) for h,p in paths.items()},
        'optics_in_contact_with_parent':len(optic),'row_span_Y_mm':row_bounds,
        'optical_row_length_mm':round(row_bounds[1]-row_bounds[0],3),
        'optical_row_board_edge_margins_mm':edge_margins,
        'board_pairs_checked':len(list(itertools.combinations(boards,2))),'fx10_fx8c_interfaces_checked':len(mates)}
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
