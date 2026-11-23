; EXE hooks: English (ASCII) glyphs + variable-width advance (docs/re/text.md "English font").
; armips asm/hooks.asm -strequ EXE <path to SLPS_012.9x> -strequ TABLES <font_tables.bin from tools/font.py>
; RAM = file offset + 0x8000F800. Startup (0x8006B1CC) zeroes BSS 0x800B6408-0x80162F88, so the payload is stored in
; that zero BSS area of the file and copied by a boot stub (new EXE entry point) to PAYLOAD.
; Our RAM: 0x801E8000-0x801F7FFF, cut off the top of the game's malloc arena (descriptor 0x8015B608, base
; [0x800120DC]+0x800, end 0x801F7F00 -> 0x801E7F00; highest block end seen in 11 scene dumps 0x801D1284).
; The stack sits above (0x801F7FF8-0x801FFFF8).
.psx
.open EXE, 0x8000F800

PAYLOAD     equ (0x801F0000)    ; code + tables, up to 0x801F7FF8
SCEN_BUF    equ (0x801E8000)    ; scenario block buffer, 0x8000 bytes (was 0x2800 at 0x800D16F8)
SCEN_MAX    equ (0x8000)

.org 0x8001A6FC                 ; main: arena size = 0x801F7700 - [0x800120DC]  (was lui v0, 0x801F)
  lui   v0, 0x801E
STUB        equ (0x800CAC00)   ; BSS, zero in the file, after the glyph map (0x800C4E78 + 0x5D7C)
START       equ (0x8006B1CC)   ; original entry point
LOOKUP_SJIS equ (0x80044C50)   ; glyph lookup, after its first two instructions
LOOKUP_CELL equ (0x80044CB8)   ; glyph lookup, entry (a2) -> u, v, plane

; ---- new entry point ----
.org 0x8000F810
  .word boot_stub

.org STUB
boot_stub:
  la    t0, payload_src
  la    t1, PAYLOAD
  la    t2, payload_src + (payload_end - PAYLOAD)
@@copy:
  lw    t3, 0(t0)
  addiu t0, t0, 4
  sw    t3, 0(t1)
  bne   t0, t2, @@copy
  addiu t1, t1, 4
  j     START
  nop
.align 4
payload_src:
.headersize PAYLOAD - orga()

; ---- glyph lookup 0x80044C48(code, &out): bytes 0x20-0x7F use cell_tab; every call sets last_adv ----
lookup_hook:                    ; a2 = code (set in the patched delay slot)
  andi  t0, a2, 0xFFFF
  sltiu t1, t0, 0x80
  bnez  t1, @@ascii
  lui   t2, hi(last_adv)        ; payload < 0x801F8000: last_adv and last_sjis share hi()
  li    t1, 13                  ; full-width advance (the renderers' own constant)
  sh    t1, lo(last_adv)(t2)
  li    t1, 1
  sh    t1, lo(last_sjis)(t2)
  j     LOOKUP_SJIS
  addiu a0, a0, -0xA6           ; the overwritten instruction
@@ascii:
  sh    zero, lo(last_sjis)(t2)
  addiu t0, t0, -0x20
  bltz  t0, @@none
  nop
  la    t1, adv_tab
  addu  t1, t1, t0
  lbu   t1, 0(t1)
  sh    t1, lo(last_adv)(t2)
  sll   t0, t0, 1
  la    t1, cell_tab
  addu  t1, t1, t0
  lhu   a2, 0(t1)
  j     LOOKUP_CELL             ; a2 = 0 (byte without a glyph) -> returns -1
  nop
@@none:
  sh    zero, lo(last_adv)(t2)
  j     LOOKUP_CELL
  move  a2, zero

; ---- scenario renderer 0x80043DA4: pen x (s3) += last_adv instead of 13 ----
scen_adv:                       ; called from 0x80044480; v0 is live (delay slot load), use at only
  lui   at, hi(last_adv)
  lhu   at, lo(last_adv)(at)
  nop
  jr    ra
  addu  s3, s3, at

; ---- generic string draw 0x80043A64 (menus, ~200 callers): pen x (s3) += last_adv after a glyph or a lookup miss ----
gen_adv:
  lui   at, hi(last_adv)
  lhu   at, lo(last_adv)(at)
  nop
  addu  s3, s3, at
  j     0x80043AB0
  nop

; ---- string draw 0x80044624 (ACTION/HEN/EXE): pen x (s2) += last_adv; a lookup miss (space) advances too ----
gen2_adv:
  lui   at, hi(last_adv)
  lhu   at, lo(last_adv)(at)
  nop
  addu  s2, s2, at
  j     0x80044680
  nop

; ---- txd markup text 0x800133D4, default font mode: x ([a0+0x14]) += &g width [a0+0x24] + last_adv - 13.
; The line's char count [a0+0x34] (auto-wrap at [a0+0x2C] chars, 0x80017EAC) counts Shift-JIS glyphs only, so
; English never auto-wraps: insert.py wraps it with &n() by pixel width.
txd_adv:                        ; from 0x80017DC8 (leaf, returns to the caller); v1 = &g width (delay-slot load)
  lw    v0, 0x14(a0)
  lui   t0, hi(last_adv)
  lhu   at, lo(last_adv)(t0)
  lhu   t0, lo(last_sjis)(t0)
  addiu at, at, -13
  addu  v1, v1, at
  addu  v0, v0, v1
  beqz  t0, @@done
  sw    v0, 0x14(a0)
  lw    v0, 0x34(a0)
  nop
  addiu v0, v0, 1
  sw    v0, 0x34(a0)
@@done:
  jr    ra
  nop

; ---- DIC.BIN dictionary pages (docs/re/text.md "Dictionary pages"). All unlocked entries are laid out at once
; into one array of glyph records in the task workspace (ws + 0x49B0 up to the fields at ws + 0x3688C). The
; original 26-byte records (u, v, x, y, clut, 4 corners, colour) hold 7856 glyphs, too few for English; records
; are now 10 bytes (u, v, x, y, clut, colour: DIC_REC_MAX = 20444) and dic_expand rebuilds the corners per draw. ----
DIC_REC     equ (10)

; column s1 counts pixels: += 14 per Shift-JIS glyph (the grid pitch) or last_adv per ASCII glyph. A space
; keeps no record: t9 = records added (0/1), t8 = t9 * DIC_REC, used by the patched increments at ovl 0xD58-0xD70.
dic_adv:
  lui   t0, hi(last_adv)
  lhu   at, lo(last_sjis)(t0)
  lhu   t0, lo(last_adv)(t0)
  li    t9, 1
  li    t8, DIC_REC
  beqz  at, @@ascii
  addiu at, s0, -0x20
  li    t0, 14
@@ascii:
  bnez  at, @@add
  nop
  move  t9, zero
  move  t8, zero
@@add:
  jr    ra
  addu  s1, s1, t0

; glyph draw ovl 0x1CEC(ws, page, rec) at 0x1D20 (ra saved): expand the compact record into dic_scratch (the
; original 26-byte form: corners from x,y) and draw from that. Does the overwritten `sw a0, 0x50(sp)` and redoes
; the delay-slot load `lh v0, 8(s4)`.
dic_expand:
  sw    a0, 0x50(sp)
  la    t7, dic_scratch
  lbu   t5, 0(s4)
  lbu   t6, 1(s4)
  sb    t5, 0(t7)
  sb    t6, 1(t7)
  lhu   t5, 6(s4)
  lbu   t6, 8(s4)
  sh    t5, 6(t7)
  sb    t6, 0x18(t7)
  lh    t5, 2(s4)               ; x
  lh    t6, 4(s4)               ; y
  sh    t5, 2(t7)
  sh    t6, 4(t7)
  sh    t5, 0x8(t7)             ; corners: (x,y) (x+12,y) (x,y+14) (x+12,y+14)
  sh    t6, 0xA(t7)
  sh    t6, 0xE(t7)
  sh    t5, 0x10(t7)
  addiu t5, t5, 12
  addiu t6, t6, 14
  sh    t5, 0xC(t7)
  sh    t6, 0x12(t7)
  sh    t5, 0x14(t7)
  sh    t6, 0x16(t7)
  move  s4, t7
  jr    ra
  lh    v0, 8(s4)

.align 4
dic_scratch:
  .fill 28

.align 4
last_adv:
  .halfword 13
last_sjis:                      ; 1 after a Shift-JIS lookup, 0 after an ASCII one
  .halfword 1
.align 4
cell_tab:                       ; u16[96] glyph-map entries for bytes 0x20-0x7F, then u8[96] advances
  .incbin TABLES, 0, 192
adv_tab:
  .incbin TABLES, 192, 96
.align 4
payload_end:
.headersize 0x8000F800

.if orga() > (0x800D16F8 - 0x8000F800)
  .error "payload source runs into the scenario buffer"
.endif

; ---- patches in place ----
.org 0x80044C48                 ; was: move a2, a0 / addiu a0, a0, -0xA6
  j     lookup_hook
  move  a2, a0

.org 0x80044480                 ; was: addiu s3, s3, 0xD
  jal   scen_adv

.org 0x80043B60                 ; was: bnez v0, 0x80043AF4 (lookup miss: +13)
  bnez  v0, 0x80043D6C
.org 0x80043D6C                 ; was: j 0x80043AB0 / addiu s3, s3, 0xD
  j     gen_adv
  nop

.org 0x8004471C                 ; was: bnez v0, 0x80044680 (lookup miss: no advance)
  bnez  v0, 0x80044928
.org 0x80044928                 ; was: j 0x80044680 / addiu s2, s2, 0xD
  j     gen2_adv
  nop

.org 0x80017DC8                 ; was: lw v0, 0x14(a0) / lw v1, 0x24(a0)
  j     txd_adv
  lw    v1, 0x24(a0)

; ---- 0x80012EE0(dst, src): list rows (0x800174AC, DAY.BIN save list) widen ASCII to Shift-JIS (lowercase came out
; as ？). Now ASCII is copied as is (drawn by the VWF): no digit/letter class, no space/colon match ----
.org 0x80012F18                 ; was: andi v0, a2, 4 (digit)
  andi  v0, a2, 0
.org 0x80012F24                 ; was: andi v0, a2, 3 (letter)
  andi  v0, a2, 0
.org 0x80012F5C                 ; was: addiu v0, zero, 0x20 (space -> 8140)
  addiu v0, zero, 0x100
.org 0x80012F64                 ; was: addiu v0, zero, 0x3A (colon -> 8146)
  addiu v0, zero, 0x100

; ---- scenario block buffer 0x800D16F8 (0x2800 bytes: the next symbol is 0x800D3EF8) -> SCEN_BUF ----
.org 0x80044B4C
  lui   s0, hi(SCEN_BUF)
.org 0x80044B50
  addiu s0, s0, lo(SCEN_BUF)
.org 0x80044C30
  lui   v0, hi(SCEN_BUF)
.org 0x80044C38
  addiu v0, v0, lo(SCEN_BUF)
.org 0x80044DE4
  lui   v0, hi(SCEN_BUF)
.org 0x80044DE8
  addiu v0, v0, lo(SCEN_BUF)
.org 0x80044F40
  lui   v1, hi(SCEN_BUF)
.org 0x80044F44
  addiu v1, v1, lo(SCEN_BUF)
.org 0x80044FE8
  lui   a0, hi(SCEN_BUF)
.org 0x80044FEC
  addiu a0, a0, lo(SCEN_BUF)

; ---- battle-quote block (UNN g13) buffer: malloc(0x2800) at 0x80044BB4 -> malloc(G13_MAX) ----
G13_MAX     equ (0x4000)
.org 0x80044BC0
  addiu a0, zero, G13_MAX

.close

; ---- DIC.BIN (overlay at 0x80166218): dictionary page text, VWF (docs/re/text.md "Dictionary pages") ----
; Grid: x = col * 14 + page base (ovl 0x227C), 8 columns. Now col = pixels: wrap when col >= 100 (8th JP cell at 98).
.open DIC, 0x80166218
.org 0x80166218 + 0xC1C         ; was: slti v0, s1, 8 (8140 path)
  slti  v0, s1, 100
.org 0x80166218 + 0xC24         ; was: addiu s1, s1, 1 (8140: one cell)
  addiu s1, s1, 14
.org 0x80166218 + 0xCD0         ; was: slti v0, s1, 8
  slti  v0, s1, 100
.org 0x80166218 + 0xD4C         ; was: addiu s1, s1, 1 (after a glyph); the next op (delay slot) is a store
  jal   dic_adv
.org 0x80166218 + 0xD58         ; was: addiu s5, s5, 0x1A
  addu  s5, s5, t8
.org 0x80166218 + 0xD60         ; was: addiu s2, s2, 0x1A
  addu  s2, s2, t8
.org 0x80166218 + 0xD6C         ; was: addiu v0, v0, 1 / addiu v1, v1, 1 (record counts)
  addu  v0, v0, t9
  addu  v1, v1, t9
.org 0x80166218 + 0x227C        ; was: v0 = a0 * 14
  move  v0, a0
  nop
  nop
; 10-byte glyph records
.org 0x80166218 + 0xB94         ; was: v0 = v1 * 26 + 0x49B0 (6 ops): first record of a layout
  sll   v0, v1, 2
  addu  v0, v0, v1
  sll   v0, v0, 1
  addiu v0, v0, 0x49B0
  nop
  nop
.org 0x80166218 + 0xD5C         ; was: sb v0, 0(s2) (colour at +0x18; s2 = record + 0x18)
  sb    v0, -0x10(s2)
.org 0x80166218 + 0x2564        ; was: v0 = v1 * 26 + 0x49B0 (6 ops): first record of a page draw
  sll   v0, v1, 2
  addu  v0, v0, v1
  sll   v0, v0, 1
  addiu v0, v0, 0x49B0
  nop
  nop
.org 0x80166218 + 0x25A4        ; was: addiu s1, s1, 0x1A (page draw loop)
  addiu s1, s1, DIC_REC
.org 0x80166218 + 0x23E8        ; corner fill loop (corners now made by dic_expand)
  jr    ra
  nop
.org 0x80166218 + 0x1D20        ; glyph draw: was sw a0, 0x50(sp)
  jal   dic_expand
.close
