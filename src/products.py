# -*- coding: utf-8 -*-
"""Amazon 商品レジストリ。

方針:
- 無名の出品者ではなく、**定番ブランドのロングセラー品**を選ぶ。
  リンクが長持ちし、読者が他店と比較しやすく、安全規格への対応も確認しやすい。
- Amazon アソシエイト運営規約により、価格・在庫・★評価は PA-API 経由で取得し
  24時間以内に更新したものしか表示できない。ここでは商品名とASINのみを持ち、
  ページには価格を出力しない。
- ASIN は必ず実際に Amazon で確認してから登録する。
"""

AFFILIATE_TAG = "faithandbrave-22"

PRODUCTS = {
    # 眠る
    "swaddle":        ("B0C9QS9YNW", "エイデンアンドアネイ essentials おくるみ 2枚セット 112×112cm"),
    "swaddle_gauze":  ("B0H334VTFS", "Libaby 綿100% ガーゼおくるみ 100×100cm"),
    "sleeper":        ("B008DBJB1W", "10mois Hoppetta ふくふくガーゼ ベビースリーパー"),
    "mattress":       ("B09BZ21NRV", "サンデシカ ベビー敷ふとん 固綿マット レギュラー 70×120cm"),
    "crib":           ("B0FSDHRH6Z", "カトージ ハイシートミニベビーベッドII プレミアム（新生児〜）"),
    "crib_tomoneru":  ("B0CZNCP4NC", "コンビ すくすや トモネル ベビーベッド＆サークル コンパクト"),
    "sterilizer":     ("B0B9386D3V", "ピジョン 哺乳びんスチーム除菌・乾燥器 POCHITTO"),
    "milk_pot_zojirushi": ("B07NBRFC8D", "象印 電気ポット 1.2L STAN.（70℃保温）"),
    "milk_pot_tiger":  ("B0FDFDBD3D", "タイガー 電気ポット とく子さん 蒸気レス（70℃保温）"),
    "milk_pot_combi":  ("B0DJW1ZKBQ", "コンビ 調乳じょーず Q（70℃保温）"),
    "babybed":        ("B07QWP97J5", "石崎家具 日本製 木製ベビーベッド ワンタッチハイベッド クール"),
    "babybed_cocon":  ("B0GX8TW3GT", "アップリカ ココネルエアー AB（PSCマーク）"),
    "diaper_pouch":   ("B0BJZ7WM59", "10mois ワンタッチおむつポーチ（フラップ付き）"),
    "diaper_sheet":   ("B09T36S3QY", "ケラッタ 使い捨ておむつ替えシート（防水・50枚）"),
    "repel_skinvape": ("B0CWK5KWQ5", "フマキラー スキンベープ ミスト イカリジン アルコールフリー"),
    "repel_kincho":   ("B07NDQRC73", "KINCHO プレシャワーDF（ディートフリー・イカリジン）"),
    "repel_pigeon":   ("B0GH8HZLXS", "ピジョン 虫くるりんplus まも〜るミスト"),
    "monitor":        ("B07QR8RZJH", "パナソニック ベビーモニター KX-HC705"),
    "sensor_med":     ("B07KY57C5Y", "Sense-U ベビーセンサー（一般医療機器）"),
    "sensor_mat":     ("B08HCSBWWC", "ベビースマイル ベビーアラーム（乳児用体動センサ）"),
    "thermohygro":    ("B0DZ1VNDMN", "タニタ 温湿度計（気圧計つき）"),
    "thermometer":    ("B076Q5WCPP", "オムロン 電子体温計 けんおんくん MC-688（15秒予測）"),

    # 抱っこ・移動
    "carrier":        ("B0DXF1H4NY", "エルゴベビー OMNI Deluxe Mesh"),
    "carrier_light":  ("B0B3R6BJBT", "コニー抱っこ紐 FLEX（ヘッドサポート入り）"),
    "carseat":        ("B0FD351L6B", "アップリカ クルリラエックスプラス（ISOFIX）"),
    "harness":        ("B0DVLGVW31", "MILASIC キッズハーネス"),
    "helmet":         ("B0BPLF5MBB", "söpöta 幼児用ヘルメット（SGマーク）"),
    

    # おふろ
    "babybath":       ("B0BQ3G3BHH", "リッチェル ふかふかベビーバス ステップアップ（新生児〜12か月頃・ストッパー付）"),

    # 誤飲・やけど・感電
    "choke_checker":  ("B0B5GHCB4H", "誤飲チェッカー"),
    "battery_case":   ("B0D6VR15Y6", "JJC ボタン電池ケース"),
    "outlet":         ("B0DX7451H9", "コンセントカバー 24個入（ロック機能つき）"),
    "stove_guard":    ("B093K51BDS", "Homemi ストーブガード"),

    # 家の中の改造
    "gate_stairs":    ("B0H2GDDBPV", "日本育児 スムーズマルチゲイト（6か月頃〜満2歳・階段上はネジ固定）"),
    "gate_kitchen":   ("B003NCVK1K", "日本育児 ベビーズゲート（つっぱり式）"),
    "furniture_pole": ("B00C1SUKYU", "平安伸銅 家具転倒防止突っ張り棒 2本入（取付高さ22〜27cm・他サイズあり）"),
    "cabinet_lock":   ("B07987GQWK", "リッチェル ベビーガード はがせる開き戸ロックR"),
    "fridge_lock":    ("B076VDDZJG", "リッチェル ベビーガード 冷蔵庫引き出しロックR"),
    "corner":         ("B0DY1CPG8B", "コーナーガード 全長6m（貼り直せるゲルタイプ）"),
    "door_finger":    ("B0DPMVSP3N", "はさマンモス（ドア指はさみ防止）"),
    "window_lock":    ("B0064RFM7E", "ノムラテック ウインドロックZERO（窓用補助錠）"),

    # 食べる
    "food_scissors":  ("B00UA3JETU", "コンビ ベビーレーベル お肉も切れるフードカッター（7か月頃〜）"),
    "toothbrush":     ("B084JCTT2L", "ピジョン 乳歯ブラシ レッスン段階4"),

    # --- 追加分 ---
    "swaddle_10mois":  ("B081Z6QV3N", "10mois NAOMI ITO スワドルコットン 110×100cm（0か月〜・日本製）"),
    "sleeper_vest":    ("B0H74RWS5L", "プッパプーポ 6重ガーゼスリーパー（袖なし）"),
    "sleeper_organic": ("B08WH7YFZ4", "Haruulala organic スリーパー"),
    "carrier_bjorn":   ("B09QKYG6Z2", "ベビービョルン 抱っこひも HARMONY（0か月〜）"),
    "bathmat":         ("B0G1LSRPBP", "リッチェル ひんやりしないおふろマット"),
    "bath_thermo":     ("B0GKN2QN57", "お風呂用 湯温計（浮かべるタイプ）"),
    "cool_sheet":      ("B0D2K9S3W2", "日本育児 ファン付ベビーカーシート エアライナー（新生児〜4歳頃）"),
    "playmat":         ("B0BZHCWSWB", "ケラッタ もっちりマシュマロマット 200×140cm（厚さ1.5cm）"),
    "diaper_mat":      ("B0DNJDVJ3G", "un doudou 防水おむつ替えシート 2枚組 45×58cm"),
    "chair_belt":      ("B0D9T3C9NK", "チェアベルト（立ち上がり・転落防止）"),
    "sunshade":        ("B0GT428SDP", "Liscia ベビーカー サンシェード（メッシュ・虫よけ兼用）"),
    "furniture_belt":  ("B0DM2G631W", "家具転倒防止ベルト（穴あけ不要）"),
    "door_stopper":    ("B0F28JYF3S", "＆COCO ドア 指はさみ防止カバー"),
    "range_guard":     ("B0CDBPSX48", "東洋アルミ レンジガード"),
    "bathlid":         ("B001GTZXZQ", "東プレ 折りたたみ風呂ふた"),
    "food_cutter":     ("B082M6FHVS", "GREEN BELL 匠の技 ベビー用フードカッター（ケース付き）"),
    "food_scissors2":  ("B07GN72K1L", "エジソンママ 離乳食はさみ（ステンレス・ケース付）"),
    "toothbrush_r":    ("B0FX44WNG5", "リッチェル つよもち乳歯ブラシ STEP1"),
    "toothbrush_set":  ("B0FX436WBY", "リッチェル つよもち乳歯ブラシセット"),
    "reflector":       ("B0BWY3K15X", "TERUI Lights LED 吊り下げリフレクター（反射板）"),
    "buzzer":          ("B093D8PKG3", "防犯ブザー 130dB（LEDライト付き）"),
    "gps":             ("B0DZMM9VNF", "みてねみまもりGPSトーク"),
    "lifejacket":      ("B07RPRBLTY", "オーシャンライフ 子供用ライフジャケット（船舶検査対応）"),
    "lifejacket2":     ("B09TSYN53B", "Bluestorm 子供用 救命胴衣"),
    "wbgt":            ("B0FCSCH9CK", "黒球式 熱中症指数計（WBGT計・JIS準拠）"),
    "bottle_1l":       ("B08YNXLMHG", "BOTTLE BOTTLE ステンレス水筒 1L（保冷・ストロー）"),
    "neckcooler":      ("B0HBTDPKCX", "マジクール キッズ ネッククーラー"),
    "ors":             ("B0GY7CZMRD", "経口補水液 OS-1（300ml×12本）"),
    "bike_light":      ("B0CF8JRB6R", "DARKBEAM 自転車ライト 前後セット（充電式・IPX5）"),
    "bike_reflector":  ("B0GMGP4G9H", "自転車用 スポークリフレクター"),
    "whistle":         ("B0FBG5PG1G", "エマージェンシーホイッスル（防災笛）"),
    "led_keylight":    ("B09834GZDX", "キーホルダーライト（小型LED・4個セット）"),
    "powerbank":       ("B0GPDBS299", "エレコム モバイルバッテリー 10000mAh"),
    "router":          ("B0DM8PTZS1", "ASUS RT-BE92U ペアレンタルコントロール搭載ルーター（接続時間帯の設定・AiProtection）"),
    "privacy_film":    ("B01N4R89QG", "PDA工房 Nintendo Switch用 のぞき見防止フィルム（日本製）"),
    "doorscope":       ("B0DBVHPSNT", "マグネット式ドアスコープカバー"),
    "waterproof_case": ("B0DLK8866F", "スマホ防水ケース（IPX8・ネックストラップ）"),
    "cable_box":      ("B0BSLDCT8D", "ケーブルボックス（配線隠し）"),
    "cord_clip":      ("B0C4YK72N4", "TOSO コードアジャスタNS 10個セット（シェードのコードをまとめる）"),
    "first_aid_kit":  ("B0GJ7QQMYR", "救急セット 16点（ファーストエイド）"),
    "humidifier":     ("B0CL4R54X4", "SwitchBot 気化式加湿器（熱湯を使わない方式）"),
    "baby_hat":       ("B0FD9TF37P", "ベビー用 コットンハット（ゴム付き・2way）"),
    "carseat_joie":   ("B08C13F7QF", "Joie アイ・アーク360° ISOFIX固定（0か月〜4歳頃・回転式）"),
    "carseat_kuru":   ("B0D4D75WQV", "コンビ クルムーヴ ロング R129（新生児〜10才頃・回転式ISOFIX）"),
    "futon_junior_kataen": ("B0D41KP131", "こどものふとん ジュニア敷き布団 90×190cm（固綿入・日本製）"),
    "futon_junior_nishikawa": ("B0FBRK9ZLY", "西川 ジュニアサイズ 合繊敷きふとん 90×180cm（抗菌加工・日本製）"),
    "futon_junior_3layer": ("B07MFTTPCF", "リビングプランニング 敷き布団 ジュニアサイズ 85×185cm（3層構造・日本製）"),
    "juniorseat_combi":  ("B0H1Q8CFDZ", "コンビ ジョイトリップ アドバンス for kids エッグショック MB（ISOFIX固定・R129対応・3歳頃から12歳頃まで・身長150cmまで）"),
    "juniorseat_aprica": ("B0DKSRTGWM", "アップリカ ライドクルーISOFIX AB（ISOFIX固定・R129適合・3歳半頃〜12歳頃・背もたれ取り外し可）"),
    "juniorseat_graco":  ("B0CJLHM5FL", "グレコ ジュニアプラスネクスト（シートベルト固定・R129適合・3歳半頃〜12歳頃・身長150cmまで・背もたれ取り外し可）"),
    "stroller_bag":   ("B0CR83NNTC", "ベビーカー用 アンダーバッグ（下かご収納）"),
    "bouncer_bjorn":  ("B09DC26NL5", "ベビービョルン バウンサー Bliss Air（日本正規品）"),
    "bouncer_richell":("B0FYLKZZ35", "リッチェル バウンシングシートN（月齢1か月頃から）"),
    "bouncer_ergo":   ("B0D95KQTG3", "エルゴベビー evolve バウンサー（メッシュ）"),
    "babyrack_combi": ("B0D4DBJ142", "コンビ ハイローチェア ネムリラ Fit AQ"),
    "babyrack_bedi":  ("B07ZTN6WBG", "コンビ ホワイトレーベル ネムリラ AUTO SWING BEDi Long シェル EG"),
    "babyrack_apr":   ("B0967Q7LS1", "アップリカ ハイローチェア ユラリズム オート ライト（0か月〜4歳頃）"),
    "babyrack_katoji": ("B0D9NHJKPB", "カトージ スイングハイローラック ピッコロ（新生児〜）"),

    # 4〜6か月。床で完結させる・外出先の暑さ・おもちゃ。
    "playmat_nuage":  ("B0FL25V9MR", "日本育児 nuage スムースプレイマット 220×140cm（厚さ4cm・継ぎ目なし）"),
    "jointmat":       ("B09WD7F75Z", "タンスのゲン ジョイントマット 極厚20mm 大判59cm 16枚組"),
    "blender_braun":  ("B0FTMR59ZY", "ブラウン ハンドブレンダー マルチクイック5"),
    "fan_seat_airluv": ("B0DXKRPR51", "Poled エアラブ4プラス ドーナッツ ファンシート（新生児〜満4歳頃）"),
    "cape_babyhopper": ("B0GQ9NXRW5", "ベビーホッパー 空調ベビーケープR26（首すわり後〜）"),
    # トイローヤルは商品ページにSTマークと対象年齢の記載がある。
    # 他社の乳児向けおもちゃは、商品ページでSTマークを確認できないものが多い。
    "toy_rolling":    ("B096LJYS1C", "トイローヤル ヒーリングローリー（STマーク・0か月〜）"),
    "toy_rattle":     ("B0B5X583VT", "トイローヤル ふってリンリン（STマーク・2か月〜・ネジ不使用）"),
    "toy_rattle_soft": ("B00IXF31JG", "トイローヤル やわらかふってリンリン（STマーク・3か月〜）"),
    "diaper_pouch_mat": ("B0DDSRHRXN", "タイニートゥインクル マットにもなるおむつポーチ"),
    # ソフトクローズのふたを備えたおもちゃ箱は定番ブランドに無い。
    # かぶせ式のふたは、ちょうつがいの重いふたより指をはさみにくい。
    "toybox":         ("B0DFCM81BR", "アイリスオーヤマ フタ付き積み重ねBOX 45×29×25cm"),
}

# 書籍。グッズで解決しない項目（行動や情報の扱いが主題のもの）に紹介する。
BOOKS = {
    "bk_evidence":  ("4296002430", "医師が本当に伝えたい 12歳までの育児の真実（今西洋介）"),
    "bk_accident":  ("4862576540", "小児科医が教える「子どもを事故から守る本」（坂本昌彦）"),
    "bk_literacy":  ("4759825037", "フェイクニュースを科学する 拡散するデマ、陰謀論、プロパガンダのしくみ（笹原和俊）"),
    "bk_hajimete":  ("4072955442", "はじめてママ&パパの育児 0〜3才赤ちゃんとの暮らし"),
    "bk_firstaid":  ("4816370544", "0〜5歳児 ケガと病気の予防・救急 まるわかり安心BOOK"),
    "bk_anger1":    ("B06XYC4YLM", "子育てのイライラ・怒りにもう振り回されない本"),
    "bk_anger2":    ("B09GFJBS71", "アンガーマネジメント超入門 「怒り」が消える心のトレーニング"),
    "bk_sleep":     ("B07DHLP3YJ", "ママと赤ちゃんのぐっすり本 「夜泣き・寝かしつけ・早朝起き」解決ガイド"),
    "bk_homecare":  ("B075691CDH", "はじめてママ＆パパの0〜6才 病気とホームケア"),
    "bk_emergency": ("4652044089", "知っててよかった子どもの応急手当"),
}
PRODUCTS.update(BOOKS)


# 第三者評価。**商品そのものが受賞したと確認できたものだけ**を書く。
# 「メーカー別集計で○位」のように、受賞対象と紹介商品が一致しないものは載せない。
AWARDS = {
    "carrier":       ("マザーズセレクション大賞2025（Ergobaby OMNIシリーズ）",
                      "https://www.best-mother.jp/selection/mothers_selection17/"),
    "monitor":       ("マザーズセレクション大賞2025（ベビーモニター／ベビーカメラ）",
                      "https://www.best-mother.jp/selection/mothers_selection17/"),
    "sterilizer":    ("マザーズセレクション大賞2025（哺乳びんスチーム除菌・乾燥器 ポチットシリーズ）",
                      "https://www.best-mother.jp/selection/mothers_selection17/"),
    "crib_tomoneru": ("第18回キッズデザイン賞（すくすや トモネル ベビーベッド コンパクト）",
                      "https://kidsdesignaward.jp/docs/2024/18thKDawardPressrelease20240821.pdf"),
}


def award(key):
    return AWARDS.get(key)


def link(key):
    asin, name = PRODUCTS[key]
    return "https://www.amazon.co.jp/dp/%s?tag=%s" % (asin, AFFILIATE_TAG), name
