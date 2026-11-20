# pscont_backplane_system

大型電源の三相PWMコンバータと2象限単相チョッパを制御する、マスタ1枚・PWMカード最大12枚のシステム。電流制御はSTM32H745XIH6、同期と指令配信は10M16DCF484I7Gで行う。

| プロジェクト | 内容 |
|---|---|
| [backplane_board](backplane_board/README.md) | 受動バックプレーンの回路設計仕様。96差動対の割当、電源容量、保護、評価項目を含む。 |
| [KiCadプロジェクト](backplane_board/backplane_board.kicad_pro) | KiCad 10。全体結線、12 V保護、マスタ3コネクタ、PWM 12スロットの階層回路図。 |
| [スロット結線表](backplane_board/slot_links.csv) | マスタ・スロット間の全96対。電気的に独立する正負ネットと終端位置。 |
| [回路図PDF](backplane_board/backplane_board.pdf) | A3、全17ページ。各スロットの実装部品番号を展開。 |
| [通販URL付きBOM](backplane_board/BOM.csv) | 1台分の購入部品と在庫掲載数。 |
