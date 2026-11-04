# -*- coding: utf-8 -*-
"""危険の種類ごとに項目をまとめ、そこから「関連する項目」を導く。

なぜ項目ごとに書き並べないか:
  124項目ぶんの関連リストを手で持つと、両向きがずれる。
  「窒息」から「誤飲」へは張ってあるのに、逆が無いという状態になり、
  項目を足すたびに全部を見直すことになる。

  危険の種類のほうを並べておけば、関連は両向きに成り立つ。
  項目を足すときも、その項目をどの種類に入れるかだけを決めればよい。

  このサイトの売りは網羅性なので、「同じ危険が、どの月齢でも形を変えて
  出てくる」ことが見えるのが、いちばん価値のある並べ方でもある。
  チャイルドシートなら、退院の日から助手席に座りたがる年齢までが一続きになる。

並べ方:
  同じ種類に入っている項目のうち、月齢が近いものから出す。
  複数の種類に入っている項目は、種類ごとに順番に拾って、
  どれか1つの種類で埋まらないようにする。最大6件まで。

決まり:
  すべての項目が、少なくとも1つの種類に入っていること。
  ビルド時に確かめているので、入れ忘れるとエラーで止まる。
"""

THEMES = {
    "のどに詰まる・窒息": [
        "feeding", "first-aid", "swallow-4m", "weaning", "honey", "toys-4m",
        "food-7m", "food-1y", "first-aid-1y", "food-y3",
    ],
    "口に入れる・誤飲": [
        "baby-chemicals", "swallow-4m", "toys-4m", "poison",
        "disinfectant-1y", "poison-y3", "od-y10",
    ],
    "転落・落ちる": [
        "carrier", "fall-m0", "fall-bath", "fall-4m", "changing-table",
        "stroller-4m", "stairs", "window", "crib-7m", "chair-7m",
        "cart-1y", "bed-1y", "window-y3", "play-y3", "playground",
    ],
    "水におぼれる": [
        "bath-newborn", "water-7m", "pool-7m", "water-1y",
        "water-y3", "water-y6", "water-y10", "swim-y10",
    ],
    "やけど・火": [
        "burn-newborn", "burn-7m", "outlet", "fire-y3",
    ],
    "寝かせ方と、睡眠中の事故": [
        "crib-pre", "sleep-pre", "sids", "swaddle", "sleep-env",
        "sleep-products", "room-temp", "watch", "bouncer", "rack",
        "roll-prone", "roll-swaddle", "bedguard-4m", "crib-7m", "bed-1y",
    ],
    "車に乗せる": [
        "carseat-pre", "car-leave", "carseat-newborn", "carseat-1y",
        "juniorseat-y3", "seatbelt-y6", "frontseat-y10",
    ],
    "自転車に乗せる・乗る": [
        "bike-m0", "bike-4m", "bike", "bike-y3", "bike-y6", "bike-y10",
    ],
    "道路と駐車場": [
        "road", "road-y3", "school-road", "bike-y3", "bike-y6",
    ],
    "暑さと熱中症": [
        "room-temp", "uv", "heat-4m", "car-leave", "heat-1y",
        "heat-y3", "heat-y6", "sports-y10",
    ],
    "家の中を変える": [
        "home-pre", "notyet-pre", "furniture", "corner-pinch", "gate-7m",
        "outlet", "poison", "walker", "home-1y",
    ],
    "抱っこ・おんぶ": [
        "carrier-pre", "hold", "ddh", "carrier", "bike-4m",
    ],
    "ベビーカー": [
        "stroller-pre", "stroller", "stroller-4m", "heat-4m",
    ],
    "災害への備え": [
        "disaster-pre", "disaster-m0", "disaster-m7",
        "disaster-1y", "disaster-y10",
    ],
    "ミルクと離乳食": [
        "formula-pre", "formula", "feeding", "outdated-m4",
        "weaning-start", "weaning", "allergy-4m", "honey", "food-7m",
        "milk-medicine",
    ],
    "泣きやまないときと、親のこころ": [
        "cry-pre", "support-pre", "smoke-pre", "sbs", "hair-tourniquet",
        "milk-medicine",
    ],
    "製品の選び方と使い方": [
        "crib-pre", "stroller-pre", "notyet-pre", "misinformation", "manual",
        "bedguard-4m", "babychair-4m", "toys-4m", "walker",
    ],
    "ひも・コードが首に巻く": [
        "home-pre", "cord", "playground", "play-y3",
    ],
    "予防接種と、うつる病気": [
        "vaccine-m0", "vaccine-seizure", "skin-infection",
    ],

    "歯": [
        "teeth-7m", "toothpaste-7m", "toothbrush",
    ],
    "ネットとお金": [
        "net-y6", "gamepay-y6", "net-y10",
    ],
    "ひとりにする・防犯": [
        "leave", "watch", "lost-y3", "crime-y6", "home-alone", "net-y10",
    ],
    "古くなった常識": [
        "outdated-m0", "misinformation", "outdated-m4",
        "outdated-m7", "outdated-y6",
        "vaccine-m0", "vaccine-seizure", "toothpaste-7m", "skin-infection",
        "milk-medicine", "allergy-4m",
    ],
    "遊具と運動": [
        "playground", "play-y3", "trampoline-y6",
        "school-injury-y6", "sports-y10",
    ],
    "そのときどうするか": [
        "first-aid", "seizure-m7", "vaccine-seizure", "first-aid-1y",
    ],
    "虫よけと日差し": [
        "uv", "repellent-4m",
    ],
}

# 1つの項目に出す関連項目の数。多いと、カードの末尾が目次になってしまう。
MAX = 6


def related_ids(item_id, age_of):
    """item_id に関連する項目のidを、出す順に返す。

    age_of は id からタブの並び順（月齢の順）を引く辞書。
    同じ種類の中では月齢の近いものを先に出し、
    種類が複数あるときは、種類ごとに順番に1件ずつ拾う。"""
    mine = [t for t, ids in THEMES.items() if item_id in ids]
    if not mine:
        return []
    here = age_of[item_id]
    queues = []
    for theme in sorted(mine):
        others = [i for i in THEMES[theme] if i != item_id and i in age_of]
        others.sort(key=lambda i: (abs(age_of[i] - here), age_of[i]))
        queues.append(others)
    out = []
    while queues and len(out) < MAX:
        for q in list(queues):
            if not q:
                queues.remove(q)
                continue
            pick = q.pop(0)
            if pick not in out:
                out.append(pick)
            if len(out) >= MAX:
                break
    return out
