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
  li    t1, 13                  ; full-width advance (the renderers' own constant)
  lui   t2, hi(last_adv)
  sh    t1, lo(last_adv)(t2)
  j     LOOKUP_SJIS
  addiu a0, a0, -0xA6           ; the overwritten instruction
@@ascii:
  addiu t0, t0, -0x20
  bltz  t0, @@none
  nop
  la    t1, adv_tab
  addu  t1, t1, t0
  lbu   t1, 0(t1)
  lui   t2, hi(last_adv)
  sh    t1, lo(last_adv)(t2)
  sll   t0, t0, 1
  la    t1, cell_tab
  addu  t1, t1, t0
  lhu   a2, 0(t1)
  j     LOOKUP_CELL             ; a2 = 0 -> returns -1 (space: no glyph, pen still advances)
  nop
@@none:
  lui   t2, hi(last_adv)
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

.align 2
last_adv:
  .halfword 13
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
