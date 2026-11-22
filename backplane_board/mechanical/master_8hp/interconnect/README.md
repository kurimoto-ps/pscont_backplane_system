# 6U・8 HPマスターの実装と前面配線

[3D組立図（4頁）](master_front_interconnect.pdf) ｜ [回転・分解できる3Dビューア](assembly_3d/master_8hp_viewer.zip) ｜ [組立STEP](assembly_3d/master_8hp_STEP.zip) ｜ [基板台帳](assembly_3d/board_register.csv) ｜ [内部端子割付](interconnect_pins.csv) ｜ [前板実寸図](../master_8hp_panel_fit.pdf)

![親基板の前縁に載る16個の光素子](assembly_3d/optical_row.png)

## マスターカード1台に使う基板

| ID | 基板 | 外形、前縁方向×奥行 mm | 接続 |
|---|---|---|---|
| M | 新規の親基板 | 233.35 × 160 | 前縁の同じ部品面にDR9300 ×10、DS9300 ×3、HFBR-24E6Z ×3。背面にバックプレーン用コネクタ2個 |
| C | 既設演算子基板を改版 | 145.05 × 68.4 | STM32H745XIH6、10M16DCF484I7G、SDRAM。Mへ既設FX10×4、面間5 mm |
| E | 新規Ethernet基板 | 21.2 × 107 | C上のXETHに嵌合、面間7 mm案。LAN8742AとMagJackを実装 |
| P | 新規PLC受動中継基板 | 121 × 31 | 外部20極J3・J4を搭載し、H-PIとH-POの各20芯でMへ |

4種各1枚。RS-232Cは前板に固定したDE-9をMへ直配線する。前面の光用中継コネクタXR・XLと2枚の光基板を省く。クレート側バックプレーン、PWMカード、DACカードは別の組立品。

![4枚の分解図](assembly_3d/exploded_view.png)

## 親基板に載せる光回路

- R1～R9は24 bit ADC 3台のDRDY・DATA・SCLK各3本、R10は16 bit ADCのADDATA16。TEP523Aの受信バッファ、5 Vの受光器電源・デカップリング、3.3 Vへの変換をMへ移す。DR9300の納入仕様書Rev.0、4–5頁の端子は1 DATA OUT、2 GND、3 Vcc、4/5/6 GND。判定タイミングは、各ADCのSCLKとDATAの受光器・バッファ・配線・FX10の相対遅延を含めて確認する。
- T1～T3は16 bit ADCへのSCLK、FS、CONVSTART。CのJ9からMのTEP526A相当の送信駆動回路を経てDS9300へ。送信の電流ループを受光器の電源帰路から離す。
- S1～S3はタイミング用HFBR入力。S1は既存TEP521CのHFBR-24E6Z、C35のAC結合、整形段に相当する回路をMに置く。S2/S3は同じ機械外形を仮定。連続クロックと単発／静止レベルの違いを踏まえ、整形方式とC側端子は入力仕様に合わせて決める。PWMゲート用のHFBR-1522ETZ／2522ETZはPWMカード側にある。
- Mは12 V受電・ローカル電源、同期クロック、LVDS、ゲートトリップ集約、PLC絶縁入出力、ADM3202も担う。FMC16はCのSDRAM専用。PWM・DAC指令とゲートエラー帰還は背面経由。ゲート停止のハードウェア経路とエラー箇所の低速読出しを独立させる。

端子表の「M optical port」のphysical_pinは前面ポートIDを示す。実装する素子のパッケージ端子番号は各素子の図面に従う。

## 前板ハーネス

| 外部コネクタ | 前板から親まで | TEP521Cから引き継ぐ接点 |
|---|---|---|
| 母J3、PLC DO → マスター入力 | 前面HIF3B-20PA-2.54DS(71) → 受動板 → H-PI 20芯 → 親の入力抵抗・PS2801C-4系 → 子J8 | 1～16が各点、17～20は既設図の「+24V」共通。各ピンを同番号で結線し、共通4接点も残す |
| 母J4、マスター出力 → PLC DI | 子J8 → 親のG3VM-41HR系接点 → H-PO 20芯 → 受動板 → 前面HIF3B | 1～16が各点、17～20は既設図の「-24V」共通。J3とは別キー。±の呼称は既設図のネット名で、親のロジック電源を基準とする電圧指定ではない |
| 母J5、RS-232C（外部はDE-9メス） | 子J8 → 親のADM3202 → H-RS → 前面DE-9。ねじは既設プラグに合わせる | マスターから見て2=RXD入力、3=TXD出力、5=SG、7=RTS出力、8=CTS入力。1/4/6/9は未接続。7/8は別線で引き、既設の子J8-66/68側のフロー制御折返しを維持 |

H-PI/H-POはラッチ付圧着、同一筐体を用いる場合も異なる誤嵌合キーで区別する。現場側の20極プラグおよび番号を保存。H-RSは9極ハウジングに有効5線を実装し、端子番号は前面DE-9と対応させる。SGはADM3202側の信号基準へ戻す。DE-9金属シェルは前板シャーシで受け、SGとの結合は盤の接地仕様に合わせる。PLCのフィールド共通線はロジックGNDから分離。

仮配索の中心線長はH-PI 44.5、H-PO 85.3、H-RS 69.6 mm。PLC束は16 × 4.2 mm、RS束は直径3.3 mmの仮外形。親側のコネクタ中心は (Y,D) が (44,60)、(64,60)、(238,68) mm。端子の挿入代、余長・折り曲げ、クランプまで含む製作長は現物で決める。

## 演算子基板とEthernet

既存のSTM・MAX 10・SDRAMとFX10の配置を維持する。CからEへPHY、25 MHz水晶、ストラップ、MagJackを移す。STDC14のキー・1番ピン、シルクを修正し、RJ45ガイド穴を移設先Eでメーカー図に合わせる。Cの部品面X15.17に対し、Eの裏面X22.17（公称面間7 mm）、部品面X23.77、ジャック外形中心X30.82 mm。XETHはFX8C-60P-SV2＋FX8C-60S-SV候補。旧J1（HRTIM／FLT5）と旧J3（STM ADC3）はEの投影内で、公称7 mmのヘッダーは未嵌合でも余裕0 mm。C改版時にEの外へ移す。旧Cでの先行試験はEを外して既設RJ45を使う。

Eに旧Ethernet回路を一括移設する。Cとの間はXETH 60極のうち、RMII 50 MHz基準・RXD[1:0]・CRS_DV・TX_EN・TXD[1:0]、MDC・MDIO・nRSTで10信号。GNDと3.3 Vも渡す。PHYがREF_CLKをSTMへ供給する既設方式、PHYアドレス・MODEストラップ、リセット、LED、RBIASを継承する。R105などPHY出力の直列抵抗はEの送端へ。STM側の出力にも必要に応じて送端抵抗のランドを取る。XETHからPHYまでの信号長と負荷を抑え、特にPHY→STMのクロックとSTM→PHYの送信データの往復を含めて最小／最大のsetup・holdを確認する。MDI差動対はE内で100 Ω差動を目標に連続した参照面上を配線し、絶縁部の銅箔除外・シャーシ境界はジャックとPHYの推奨に従う。

## 組立モデルの検証範囲

親基板には前縁切欠きのない矩形を使い、前板金具で上・中・下の3点を支持する。PとEにも前板側の支持を設ける。STEPのXは前板左基準、Dは背面方向、Zは260.45−Y。ビューアはZIP展開後にHTMLをChrome/Edgeで開く。前板の有無、4枚の分解、各基板、直付け光列、内部3ハーネス、金具を切り替えられる。

FreeCADで光素子16個の着座、全4基板の6組、搭載部品・ケーブル経路と金具の公称形状を照合した。外部プラグは2D操作枠のみ。DSの詳細形状、公差、前板の光軸位置、ケーブルの曲げ半径・ラッチ操作、着脱荷重、リードや銅箔等の詳細は製作前に実機で照合する。前板の穴とモデルの光素子は収容検討用。自動確認結果は [fit_report.json](assembly_3d/fit_report.json)、モデル再生成は [build_model.py](assembly_3d/build_model.py)。

## 設計元

- [演算子基板の回路・外形](https://github.com/kurimoto-ps/jparc-fb-board/tree/8ffc1ff86d3a8252b1c35c7859f049dd370dface/hardware/kicad)・[ADC／PLC／RS-232C対応](https://github.com/kurimoto-ps/jparc-fb-board/blob/8ffc1ff86d3a8252b1c35c7859f049dd370dface/docs/interfaces.md)・[既知の改版箇所](https://github.com/kurimoto-ps/jparc-fb-board/blob/8ffc1ff86d3a8252b1c35c7859f049dd370dface/docs/errata.md)
- [既設のTEP521C・TEP523A・TEP526A回路図](https://github.com/kurimoto-ps/digital_power_control/tree/2a581d19a357db6020fd6056bd86994f189acb45/targets/jparc_rev58/docs/hardware/circuit)
- [LAN8742A](https://www.microchip.com/en-us/product/lan8742a)・[Molexジャック外形・ドリル図](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/934/93463/934635206_sd.pdf)・[Hirose FX10](https://www.hirose.com/product/series/FX10)・[Hirose FX8C](https://www.hirose.com/product/series/FX8C)

- [JST XH旧J1/J3の外形](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)・[Hirose HIF3B PLCコネクタ](https://www.marutsu.co.jp/contents/shop/marutsu/datasheet/HIF3B_catalog.pdf)・[はんだカップ型DE-9候補 XM3D-0921](https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/XM3D-0921/4755015)（M2.6は別の固定金具で照合）・[HyLink外形](https://www.hitachi-ite.co.jp/products/catalog/pdf/hylink.pdf)・[HFBR SCポート外形](https://docs.broadcom.com/doc/AV02-0176EN)
