# pscont_backplane_system

**2マスターのクレート収容案**　[電源8 HP＋コンバータ36 HP＋チョッパ36 HP](backplane_board/mechanical/dual_master_crate/README.md) · [正面図・電源ベイの立体図・容量比較（PDF）](backplane_board/mechanical/dual_master_crate/dual_master_crate.pdf)

**比較元の1マスター機構案**　[6Uクレート・正面左16 HPの着脱式電源](backplane_board/mechanical/front_psu_16hp/README.md) · [3D組立・取付図（PDF）](backplane_board/mechanical/front_psu_16hp/PSCONT_front_PSU_views.pdf)

大型電源の三相PWMコンバータと2象限単相チョッパを制御するシステム。電流制御はSTM32H745XIH6、同期と指令配信は10M16DCF484I7Gで行う。2マスター案では各系統がPWM 6枚とDAC 1枚を担当する。下表のKiCad設計は先行する1マスター版。

| プロジェクト | 内容 |
|---|---|
| [backplane_board](backplane_board/README.md) | 受動バックプレーンの回路設計仕様。96差動対の割当、電源容量、保護、評価項目を含む。 |
| [16 ch DAC・4 HP化と盤内電源の検討](backplane_board/mechanical/dac_4hp/README.md) | 14共通スロット案。負荷別の電力、112対の割当、電源取付と背面保守のPDF・DXF・STEP。 |
| [KiCadプロジェクト](backplane_board/backplane_board.kicad_pro) | KiCad 10。全体結線、12 V保護、6Uマスタの160極2コネクタ、PWM 12スロットの階層回路図。 |
| [スロット結線表](backplane_board/slot_links.csv) | マスタ・スロット間の全96対。電気的に独立する正負ネットと終端位置。 |
| [回路図PDF](backplane_board/backplane_board.pdf) | A3、全22ページ。各スロットの実装部品番号を展開。 |
| [通販URL付きBOM](backplane_board/BOM.csv) | 1台分の購入部品と在庫掲載数。 |
