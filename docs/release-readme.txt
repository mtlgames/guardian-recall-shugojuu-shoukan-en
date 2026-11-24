Guardian Recall: Shugojuu Shoukan - English translation v{version}
====================================================================

Unofficial English fan translation of Guardian Recall: Shugojuu Shoukan (PlayStation, XING, 1998, 2 discs).
This zip holds only the patches. It contains no game data: you need your own dump of the Japanese discs.

What you need
-------------
Redump "Guardian Recall - Shugojuu Shoukan (Japan)", BIN/CUE, one track per disc:

  Disc 1: Guardian Recall - Shugojuu Shoukan (Japan) (Disc 1).bin
          size {o1size} bytes, CRC32 {o1crc}, MD5 {o1md5}, SHA-1 {o1sha1}
  Disc 2: Guardian Recall - Shugojuu Shoukan (Japan) (Disc 2).bin
          size {o2size} bytes, CRC32 {o2crc}, MD5 {o2md5}, SHA-1 {o2sha1}

Any other dump (a different rip, an already patched copy) will not patch correctly.

How to patch
------------
1. Apply each .xdelta to its disc's .bin with xdelta3, Delta Patcher or xdelta UI:
     xdelta3 -d -s "...(Japan) (Disc 1).bin" {slug_d1} "Guardian Recall (English) (Disc 1).bin"
   (and the same for Disc 2 with the Disc 2 patch).
2. Make a .cue next to each patched .bin, with these three lines (change the file name to yours):
     FILE "Guardian Recall (English) (Disc 1).bin" BINARY
       TRACK 01 MODE2/2352
         INDEX 01 00:00:00
3. Load the .cue in your emulator. Swap to the Disc 2 .cue when the game asks.

Patched images:
  Disc 1: size {p1size} bytes, CRC32 {p1crc}, SHA-1 {p1sha1}
  Disc 2: size {p2size} bytes, CRC32 {p2crc}, SHA-1 {p2sha1}

Start from a cold boot (power on), not from a savestate made on the Japanese game: savestates keep the old text and
font.

Translation status
------------------
  Story dialogue, battle quotes, diary            translated
  Menus, units, items, Psi, traits, system text   translated
  Dictionaries, character files, guardian pages   translated
  Title screen, chapter cards, other graphic text translated
  Staff credits movie                             translated (names romanized)
  Voiced movies (FMV)                             Japanese voice, no subtitles

Tested in PCSX-Redux with the SCPH-5500 BIOS, both discs, from a cold boot.

Known issues
------------
None known. Please report bugs (untranslated text, typos, text running out of its box, crashes) at
https://github.com/minhnhattonthat/guardian-recall-shugojuu-shoukan-en/issues - a savestate helps most.

Credits and notes
-----------------
Translation, tools and patch: minhnhattonthat. Made with extensive AI assistance (Claude by Anthropic).
Fonts and their licences: docs/fonts.md in the repository.
Guardian Recall: Shugojuu Shoukan is (c) XING / Agumix. This is an unofficial fan project, not affiliated with them.
Do not distribute pre-patched disc images.
