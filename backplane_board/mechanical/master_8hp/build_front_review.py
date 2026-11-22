"""Draw the 1:1 front fit review from the connector-centre register, using PyMuPDF.
Pass an optional installed Japanese font file as argument. Print actual size.
"""
from pathlib import Path
import csv,sys
import pymupdf as pdf
folder=Path(__file__).resolve().parent
fontfile=sys.argv[1] if len(sys.argv)>1 else 'C:/Windows/Fonts/meiryo.ttc'
ports=list(csv.DictReader((folder/'front_io_centres.csv').open(encoding='utf-8-sig')))
doc=pdf.open()
MM=72/25.4
page=doc.new_page(width=210*MM,height=297*MM)
page.insert_font(fontname='JP',fontfile=fontfile)
dark=(.12,.19,.22);green=(.04,.42,.36);blue=(.15,.40,.57);orange=(.66,.31,.13);grey=(.42,.47,.49)
def tx(x,y,text,size=9,c=dark):
    page.insert_text((x*MM,y*MM),text,fontname='JP',fontsize=size,color=c)
def line(x,y,xx,yy,c=grey,weight=.5):
    page.draw_line((x*MM,y*MM),(xx*MM,yy*MM),color=c,width=weight)
def rec(x,y,w,h,stroke=grey,fill=None,weight=.55,dashes=None):
    page.draw_rect((x*MM,y*MM,(x+w)*MM,(y+h)*MM),color=stroke,fill=fill,width=weight,dashes=dashes)
x0,y0=31,16
tx(10,10,'6U・8 HP　親基板前縁に光16個を直付け',15)
tx(139,10,'正面図　1:1  ／  単位 mm',10)
rec(x0,y0,40.34,260.45,dark,None,1)
# Opaque solids first, thin dashed mating envelopes on top.
colors={'SC':green,'F06':blue,'PLC':grey,'RS':grey,'ETH':grey}
for r in ports:
    g,tag=r['group'],r['label'];x=x0+float(r['x_from_left_mm']);y=y0+float(r['y_from_top_mm'])
    c=orange if tag.startswith('T') else colors[g]
    bw,bh=float(r['body_W_mm_review']),float(r['body_H_mm_review'])
    rec(x-bw/2,y-bh/2,bw,bh,c,tuple(.83+.17*i for i in c))
    if g=='F06':rec(x-bw/2,y-4.5,bw,9,c,None,.45)
    sw,sh=float(r['service_W_mm']),float(r['service_H_mm'])
    rec(x-sw/2,y-sh/2,sw,sh,c,None,.45,'[2 2] 0')
    if g in ('F06','SC'):
        line(20,y,x-sw/2-1,y,c);tx(10,y+1.25,tag,10,c)
    else:
        line(x+sw/2+.5,y,80,y,c);tx(82,y+1.25,tag,10)
for x in (x0,x0+40.34):line(x,y0+261.5,x,y0+265.5)
line(x0,y0+264,x0+40.34,y0+264)
tx(x0+12,y0+269,'40.34',11)
tx(9,291,'印刷は「実際のサイズ」または100 %。右下のスケールを定規で確認。',9,grey)
for y,t,c,sz in [
 (30,'部品面に沿う一列',green,14),(39,'親基板　233.35 × 160 × 1.6',dark,10),
 (55,'R1～R10　DR9300 受信',blue,12),(62,'24 bit ADC 3 ch × 3本 ＋ 16 bit ADC 戻り1本',dark,8.6),
 (73,'T1～T3　DS9300 送信',orange,12),(80,'16 bit ADC の SCLK / FS / CONVSTART',dark,9),
 (91,'S1～S3　HFBR-24E6Z 受信',green,12),(98,'タイミング入力3本。S1～S3 間は16.0 mm。',dark,9),
 (117,'12.7 mm ピッチの寸法内訳',green,13),(127,'DR本体 11.0　→　本体間 1.7',dark,10),
 (135,'DR先端 9.0　→　先端間 3.7',dark,10),(143,'仮のプラグ幅 12.0　→　間隔 0.7',dark,10),
 (157,'実線は本体、破線は仮のプラグ・操作範囲。',dark,9),
 (164,'DSの先端はDRの外形を仮置き。',dark,9),
 (171,'X中心は筐体中心。光軸と穴加工は未確定。',dark,9),
 (191,'光列の占有長　213.85 mm',green,13),
 (201,'親基板の上端から初段本体まで 8.95 mm。',dark,9),
 (208,'最終段本体から下端まで 10.55 mm。',dark,9),
 (223,'対向列の最小余裕（仮の外形間）',green,12),
 (233,'PLC / F06　0.73 mm',dark,10),(241,'Ethernet / SC　0.81 mm',dark,10),
 (249,'DE-9 / SC　0.14 mm',dark,10),(260,'発注前に外部プラグ同時装着で確認。',dark,9)]:
    tx(102,y,t,sz,c)
line(103,280,153,280,dark,1)
for x in range(103,154,10):line(x,278,x,282,dark,.8)
tx(117,287,'50.0 mm',10)
doc.set_metadata({'title':'6U 8 HP マスター前板　光16個直付け　実寸配置検討図'})
doc.subset_fonts();doc.save(folder/'master_8hp_panel_fit.pdf',garbage=4,deflate=True)
