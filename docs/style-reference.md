# Style reference

Voices settled in the pilot (b003-b004: script/scenario/00.json, 01.json; checked in game on ev02). Each row: the JP
markers and the English devices that carry them. Paired examples are real lines from the pilot.

| Character | JP markers | English devices |
|---|---|---|
| Miyuki (美由紀) | あたし, 〜だよ, 〜っしょ, stretched vowels (う～, やったぁ), くふふ, える/なーんちゃって | bubbly, childish: "sooo", "wanna", "Wooow", "Ehehe", "Hehehe", doubled phrases ("I want one, I want one!"); calls Mayu "Mayu-chan", Chikana "Chika-chan" |
| Mayu (真由) | Hakata dialect: 〜けん, 〜と, 〜やね, こがん/そがん, なか, 〜ばい, あたし | blunt and practical; dropped g's and contractions ("goin'", "nothin'", "s'posed", "'em", "ain't" rarely), "fixin' to"; never heavy phonetic spelling |
| Chikana (周防ちかな) | アタシ, 〜さ, 〜だろ, 〜かい, あんた | cool tomboy big-sister: "you know?", "Got it?", "Good grief", "Bingo~", short clipped sentences |
| Egubado officers (由美, 富楼那, 知美) | 〜わ, 〜ておいて, は(っ) | Yumi curt and imperious ("Very well."), subordinates stiff ("Yes, ma'am.", "Yumi-sama!"); Tomomi (Suzaku) silky and condescending ("My, my...") |
| Dragons (炎龍 etc.) | indented narration, no quotes, である/のだ | solemn, archaic-leaning, no quotation marks ("Bereft of our protection, this island nation is fated to perish.") |
| Guardians (我王, コウエン) | だ/である, terse | dignified, few words ("Let her try.") |

## Paired examples
- 真由「なーんノンキに歌っとるとあんたは」 -> "What're you singin' so carefree for?"
- ちかな「あ～の～ね～」 -> "Lis-ten-to-me." (stretched scolding kept as rhythm)
- 美由紀「たまごーたまごー温泉たまご～、私はキミが好きなのよ～」 -> "Eggies, eggies, hot-spring eggies~ Oh, how I love you so~"
- 美由紀「天神高校３年１組、天城美由紀サマさ！　なーんちゃって」 -> "Tenjin High, Class 3-1, the great Miyuki Amagi! ...Just kidding."
- Corrected: 守護獣さん was "Guardian-san" -> "Mister Guardian" (さん after a non-person is not an honorific to keep).

## Format
- Body only; the tool adds the name line and wraps (224 px, 3 lines a page; overflow becomes a new {wait} page).
- 「」 -> "...", （） -> (...), narration (indented, no brackets) -> plain text, no quotes.
- Choices: two bracketed options on separate lines -> two quoted options joined by `\n`.
