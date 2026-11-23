# Glossary - Guardian Recall: Shugojuu Shoukan

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
Every `| JP | EN |` row is lint-enforced by `tools/batches.py check` (a JP form in the line needs one of the EN forms
in the English; `/` separates alternatives; Avoid spellings fail). Readings come from the game's own dictionary
(txd dic.*) and guardian list (gd.*), romanised Hepburn without macrons (D2).

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Name-san, Name-chan, Name-kun, Name-sama, Name-senpai, Name-sensei). Name order:
  Western (given name first).
- Romanisation source: official English names where they exist, else an earlier fan patch, else Hepburn without macrons.
- Credits: English.
- Register: natural contemporary English. The heroines are high-school girls: casual, quick, teasing banter; keep each
  one's quirks (dialect, cute speech, bluntness). Egubado officers speak formally or arrogantly; the ten disciples
  stiff and military. Light comedy scenes stay funny.
- Sound effects: English onomatopoeia in the line (Bam! Whoosh...). Kana laughs/yells become English (Hahaha!, Aaah!).
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation: 「」 -> "...", （） (thoughts) -> (...), 『』 -> '...' inside dialogue, titles in narration; ・・・ / …
  -> ... ; ！？ -> !? ; ー stretched vowels -> letters (Nooo). Only printable ASCII; no `&` in txd text.
- Speaker names are added by the tool (tools/batches.py SPEAKERS below); translators write only the body.
- Furigana in the text (由美（ゆみ）様) is dropped in English: write the name once.
- Dialect: Mayu (真由) speaks Hakata/Kyushu dialect (〜とよ, 〜けん, 〜やね, こがん, なか): render as folksy, dropped-g
  English ("goin'", "nothin'", "s'posed", "ain't" sparingly), never heavy phonetic spelling. Other voices:
  docs/style-reference.md.

## Speakers (name line drawn above the dialogue; also enforced as terms)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 美由紀 | Miyuki | | heroine, 天城美由紀 | |
| 真由 | Mayu | | 炎真由 | |
| 裕子 | Yuko | | 大地裕子; brash, standard speech (not Hakata) | Yuuko |
| ちかな | Chikana | | 周防ちかな, Kamikado clan heir | |
| ゆかり | Yukari | | 聖ゆかり | |
| 美里 | Misato | | 海原美里 | |
| 唯 | Yui | | 岩見沢唯 | |
| 瞳 | Hitomi | | 仁瞳; (no lint): 瞳 also means "eyes" | |
| さやか | Sayaka | | 静内さやか | |
| 景子 | Keiko | | 飛知和景子 | |
| 鈴音 | Suzune | | 一の宮鈴音, Kotone's twin | |
| 晶 | Akira | | 雷晶 | |
| 巴澄 | Hasumi | | 直江巴澄 | |
| かおる | Kaoru | | 小泊かおる | |
| るり | Ruri | | 平泉るり | |
| 琴音 | Kotone | | 一の宮琴音 | |
| 涼子 | Ryoko | | 鏡涼子 | Ryouko |
| 蘭 | Ran | | 日之影蘭 | |
| 麗子 | Reiko | | 西苑寺麗子 (Byakko) | |
| 武神 | Takegami | | | |
| めぐみ | Megumi | | 北斗めぐみ (Genbu) | |
| 知美 | Tomomi | | 南城知美 (Suzaku) | |
| 由美 | Yumi | | 半澤由美 | |
| 聡美 | Satomi | | 東聡美 (Seiryu) | |
| 仁 | Jin | | (no lint) | |
| 直江 | Naoe | | (no lint) | |
| 鏡 | Kagami | | (no lint): 鏡 also means "mirror" | |
| 天 | Ten | | (no lint): Ten-chan's name label | |
| 女の子 | Girl | | speaker label | |
| 謎の女性 | Mysterious Woman | | speaker label | |
| 謎の男 | Mysterious Man | | speaker label | |
| 謎の守護獣 | Mysterious Guardian | | speaker label | |
| 闘士 | Warrior | | Egubado rank-and-file; also generic noun | Fighter |

## Characters (full names; Western order)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 天城美由紀 | Miyuki Amagi | | | |
| 炎真由 / 炎　真由 | Mayu Homura | | | |
| 大地裕子 / 大地　裕子 | Yuko Daichi | | | |
| 聖ゆかり / 聖　ゆかり | Yukari Hijiri | | | |
| 海原美里 / 海原　美里 | Misato Kaibara | | | |
| 雷晶 / 雷　晶 | Akira Ikazuchi | | | |
| 飛知和景子 | Keiko Hichiwa | | | |
| 岩見沢唯 / 岩見沢　唯 | Yui Iwamizawa | | | |
| 周防ちかな | Chikana Suo | | | |
| 静内さやか | Sayaka Shizunai | | | |
| 一の宮鈴音 | Suzune Ichinomiya | | | |
| 小泊かおる | Kaoru Kodomari | | | |
| 一の宮琴音 | Kotone Ichinomiya | | | |
| 平泉るり / 平泉　るり | Ruri Hiraizumi | | | |
| 日之影蘭 / 日之影　蘭 | Ran Hinokage | | | |
| 直江巴澄 / 直江　巴澄 | Hasumi Naoe | | | |
| 仁瞳 / 仁　瞳 | Hitomi Jin | | | |
| 半澤由美 / 半澤　由美 | Yumi Hanzawa | | | |
| 鏡涼子 / 鏡　涼子 | Ryoko Kagami | | | |
| 南城知美 / 南城　知美 | Tomomi Nanjo | | | |
| 東聡美 / 東　聡美 | Satomi Azuma | | | |
| 西苑寺麗子 | Reiko Saionji | | | |
| 北斗めぐみ | Megumi Hokuto | | | |
| 海原望 | Nozomu Kaibara | | Misato's father, oceanographer | |
| 龍鬼妃 | Ryukihi | | prophetess who foretold the Dragon Wielder | |
| 富楼那 | Furuna | | the ten disciples (Egubado officers) | |
| 迦葉 | Kasho | | | Kashou |
| 迦旃 | Kasen | | | |
| 阿那律 | Anaritsu | | | |
| 阿難 / 阿南 | Anan | | 阿南 is an evd typo for 阿難 | |
| 優婆離 | Ubari | | | |
| 舎利弗 / 舎利 | Sharihotsu | | | |
| 須菩提 | Subodai | | | |
| 目連 | Mokuren | | | |
| 羅侯羅 | Ragora | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 天神高校 | Tenjin High | | | |
| 雪花旅館 | Yukibana Inn | | | |
| 大雪山 | Mt. Taisetsu | | | |
| 阿蘇山 / 阿蘇 | Aso | | Mt. Aso | |
| 青函トンネル | Seikan Tunnel | | | |
| 東京タワー | Tokyo Tower | | | |
| 国会議事堂 | National Diet Building | | | |
| 二条城 | Nijo Castle | | | |
| 桜井海岸 | Sakurai Beach | | | |
| 恐山 | Mt. Osore | | | |
| 佐渡島 | Sado Island | | | |
| 日光東照宮 | Nikko Toshogu | | | |
| 浅草寺 | Sensoji | | | |
| 龍泉洞 | Ryusendo Cave | | | |
| 瀬戸大橋 | Seto Ohashi Bridge | | | |
| 大鳴門橋 | Onaruto Bridge | | | |
| 妃龍鬼殿 | Hiryuki Palace | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 守護獣 | Guardian | | 守護獣召喚 = the title, "Guardian Recall" | Guardian Beast |
| 守護獣使い | Guardian user | | | |
| マスター | Master | | a guardian's human partner | |
| 召喚 | summon | | | |
| 荏狗覇菟 | Egubado | | the enemy organisation (えぐばど) | |
| 天闘衆 | Tentoshu | | Egubado strike force | |
| 神門 / 神門一門 | Kamikado | | Chikana's clan (the Kamikado clan) | |
| 四門将 | Four Gate Generals | | Suzaku, Byakko, Seiryu, Genbu | |
| 四聖獣 | Four Holy Beasts | | | |
| 朱雀 | Suzaku | | | |
| 白虎 | Byakko | | | |
| 青龍 | Seiryu | | | |
| 玄武 | Genbu | | | |
| 龍脈 | dragon vein | | | ley line |
| 龍の使い手 | Dragon Wielder | | | |
| 七龍 | Seven Dragons | | | |
| 制御ピアス | control piercing | | | |
| 結界 | barrier | | | |
| 列島大地震 | Great Archipelago Earthquake | | | |
| 超力 | Psi | | special power command | |
| 思考 | Tactic | | a guardian's AI order (思考ポイント = Tactic Points) | |
| 気力 | Spirit | | SP | |
| 属性 | element | | | |
| 斎姫 | Saiki | | | |
| 我王 | Gao | | Chikana's guardian | Gaou |
| 天ちゃん | Ten-chan | | Miyuki's guardian (named after shrimp tempura) | |
| コウエン | Koen | | Mayu's guardian | Kouen |
| メール | Mer | | Misato's guardian | Mail |
| 合体守護獣ぬえ | Combined Guardian Nue | | | |
| 花香湯 | Floral Tonic | | Spirit-restoring medicine | |
| 温泉たまご | hot-spring egg | | Miyuki's obsession | |
| ゆっこ | Yukko | | Misato's childhood nickname for Yumi Hanzawa | |
| メトラン / サバオト | Metran / Sabaoth | | Yumi's summoning words ("In the names of Metran and Sabaoth") | |
| 瀬戸内海 | Seto Inland Sea | | | |
| 風水 | feng shui | | | |
| 姫ちゃん | Hime-chan | | Yui's (and Yuko's) nickname for Saiki | |
| ダムダム作戦 | Operation Dam-Dam | | Kagami's dam plan | |
| ストーンサークル | stone circle | | teleporter site (ch. 15) | |
| 皇龍 | Emperor Dragon | | legendary incarnation of the Seven Dragons (ch. 24) | |
| 日比谷公園 | Hibiya Park | | waiting spot in Tokyo (ch. 21-24) | |
| 四門 | Four Gates | | Tokyo's barrier generators around the Diet Building (ch. 25); marker = stone tower 石塔 | |
| 新宿中央公園 | Shinjuku Central Park | | north gate | |
| 世田谷トンダーエッグ | Setagaya Tonder Egg | | west gate (Tokyo Dome parody) | |
| 東京第二国際空港 | Tokyo Second International Airport | | south gate | |
| 龍鬼 | Ryuki | | Ryukihi's Guardian (ch. 41) | |

## Guardian species and named guardians (evd unit names, b001; 改 = "+", 弐 = "II")
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 影鬼 | Shadow Oni / Mutant Shadow / Hex Shadow | | 影鬼・変異型 Mutant Shadow, 呪殺影鬼 Hex Shadow | |
| 龍殺鬼 | Dragonbane / Deathbane | | 龍殺鬼・改 Dragonbane+, 龍殺鬼・死鬼 Deathbane | |
| 斬鬼 | Slash Oni | | 斬鬼・改 Slash Oni+, 斬鬼・弐式改 Slash Oni II+ | |
| 弓男 | Bowman | | 狙撃手 Sniper Bowman, 雷撃手 Volt Bowman | |
| 戯画骸 | Toon Husk / Lesser Husk / Husk Zero | | 下位属 Lesser Husk, 零式 Husk Zero | |
| 甲殻機 | Shellmech | | 支援 Support Shellmech, 遠隔射 Gunner Shellmech | |
| 双砲蟹 | Twin-Gun Crab | | 長射 Long Gun Crab, 水上 Sea Gun Crab | |
| 爆竜 | Bomb Drake | | 強襲型 Assault Drake, 軽機動 Light Bomb Drake | |
| 一角砕 | Hornram | | 哨戒用 Scout Hornram, 重装甲 Heavy Hornram | |
| 鎌蜥蜴 | Scythe Lizard | | 改 Scythe Lizard+, 炎熱鎌蜥蜴 Blaze Lizard | |
| 翔妖 | Wing Wraith / Violet Wraith / Green Wraith | | 紫翼種 Violet Wraith, 緑翼種 Green Wraith | |
| 死人守 | Gravekeeper / Grave Chief / Grave Envoy | | 長 Grave Chief, 使 Grave Envoy | |
| 化石竜 | Fossil Dragon | | 水式 Aqua Fossil, 弐型 Fossil Dragon II | |
| 陸鮫 | Landshark | | 水式 Aqua, 雷式 Volt, 炎式 Flame Landshark | |
| 天尊 | Amazon | | 幼獣 Amazon Cub, 亜成獣 Amazon Youth, 成獣 Amazon Adult | |
| 陽炎剣士 | Haze Blade | | 褐装 Brown Haze Blade, 二刀 Twin Haze Blade | |
| 手那賀 | Tenaga | | 長肢型 Long Tenaga, 陸 Land Tenaga | |
| 拳闘骸骨 | Bone Boxer | | 軽機動 Swift Bone Boxer, 黒色 Black Bone Boxer | |
| 機忍 | Mechaninja | | 下 Mechaninja Lo, 上 Mechaninja Hi | |
| 百足蛇 | Centipede | | 海 Sea Centipede, 飛式 Flying Centipede | |
| 護法童子 | Goho Doji | | | |
| 天龍 | Sky Dragon | | 七龍: 天 Sky, 地 Earth, 炎 Flame, 聖 Holy, 海 Sea, 飛 Wind, 雷 Thunder; 黒龍 Black Dragon | |
| 地龍 | Earth Dragon | | | |
| 炎龍 | Flame Dragon | | Koen awakened | |
| 聖龍 | Holy Dragon | | | |
| 海龍 | Sea Dragon | | Mer awakened | |
| 飛龍 | Wind Dragon | | | |
| 雷龍 | Thunder Dragon | | | |
| 黒龍 | Black Dragon | | | |
| ポチ | Pochi | | | |
| ノルト | Nord | | | |
| アーチー | Archie | | Sayaka's guardian | |
| きらら | Kirara | | | |
| ザビたん | Zabi-tan | | | |
| ドナルド | Donald | | | |
| ドーガー | Doga | | | |
| ガーラー | Gara | | Kotone's guardian | |
| 凪 | Nagi | | (no lint): 凪 also "calm" | |
| 是空 | Zeku | | | |
| 不動 | Fudo | | (no lint): 不動 also "immovable" | |
| カネツグ | Kanetsugu | | | |
| ウール | Ur | | Yumi's guardian | |

## Decisions from earlier batches
- (none yet)
