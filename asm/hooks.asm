; EXE hooks: English (ASCII) glyphs + variable-width advance (docs/re/text.md "English font").
; armips asm/hooks.asm -strequ EXE <path to SLPS_012.9x> -strequ TABLES <font_tables.bin from tools/font.py>
; RAM = file offset + 0x8000F800. Startup (0x8006B1CC) zeroes BSS 0x800B6408-0x80162F88, so the payload is stored in
; that zero BSS area of the file and copied by a boot stub (new EXE entry point) to PAYLOAD.
; Our RAM: 0x801EC000-0x801F7FFF, cut off the top of the game's malloc arena (descriptor 0x8015B608, base
; [0x800120DC]+0x800, end 0x801F7F00 -> 0x801EBF00; the HEN screen uses it up to 0x801E1778 on the original:
; tools/lua/heap.lua), plus the scenario buffer in a free BSS gap (SCEN_BUF).
; The stack sits above (0x801F7FF8-0x801FFFF8).
.psx
.open EXE, 0x8000F800

PAYLOAD     equ (0x801F0000)    ; code + tables, up to 0x801F7FF8
STR_POOL    equ (0x801F4000)    ; relocated strings, up to 0x801F7FF8 (tools/insert.py STR_POOL)
G13_BUF     equ (0x801EC000)    ; battle-quote block buffer, 0x4000 bytes (was malloc(0x2800); tools/insert.py LIMITS)
SCEN_BUF    equ (0x800CAC00)    ; scenario block buffer in zero BSS, 0x6A78 bytes up to the vars at 0x800D1678 (was
                                ; 0x2800 at 0x800D16F8); the boot stub there is dead once START runs
SCEN_MAX    equ (0x6A78)

.org 0x8001A6FC                 ; main: arena size = 0x801EB700 - [0x800120DC], end 0x801EBF00 (was 0x801F7700)
  lui   v0, 0x801E
.org 0x8001A708
  ori   v0, v0, 0xB700
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
  sll   t0, t0, 1                 ; load delay slot: t1 not ready yet on R3000
  sh    t1, lo(last_adv)(t2)
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

; ---- evd op 0x34 (unit name, handler 0x8001E214): unit+0x10 = pointer to the name in the evd buffer. tools/insert.py
; replaces each translated name with key 7F hi lo; point the unit at evd_names[(hi-1)*255 + lo-1] instead ----
evd_name_hook:                  ; v1 = name in the evd buffer, v0 = unit record (0x8013E650 + idx * 0x7C)
  lbu   t0, 0(v1)
  li    t1, 0x7F
  bne   t0, t1, @@store
  lbu   t0, 1(v1)
  lbu   t1, 2(v1)
  sll   t2, t0, 8
  subu  t0, t2, t0              ; hi * 255
  addu  t0, t0, t1
  addiu t0, t0, -256            ; (hi-1)*255 + (lo-1)
  sll   t0, t0, 1
  la    t1, evd_names
  addu  t2, t0, t1
  lhu   t2, 0(t2)
  nop
  addu  v1, t1, t2
@@store:
  jr    ra
  sw    v1, 0x10(v0)            ; the overwritten instruction

; ---- 2D primitive pool growth (0x8004F43C; pool struct *0x8015238C, docs/re/text.md "2D primitive pool"). The game
; grows the pool to exactly the frame's demand and ignores a failed malloc: base 0 -> glyph packets overwrite the
; kernel (crash, ra 0xD00). Our RAM cut shrank the heap, so English text hit it (ring > UNIT, long names); the
; original's tac_search stall is the same failure. Grow in 0x2000 steps above the minimum, and on failure keep
; the current buffer (+0xC) and cap: requests over the cap fail and those primitives are skipped ----
pool_grow:                      ; a0 = slot[k&1] (the buffer not in use), s0 = pool struct
  lw    v0, 0x30(s0)            ; demand
  lw    v1, 0x1C(s0)            ; minimum (0x2800)
  nop
  slt   t0, v1, v0
  beqz  t0, @@size
  nop
  addiu v0, v0, 0x1FFF
  srl   v0, v0, 13
  sll   v0, v0, 13
  sw    v0, 0x30(s0)            ; becomes the cap (+0x18) at 0x8004F528
@@size:
  bnez  a0, @@realloc
  sll   a1, v0, 1               ; two frame halves
  jal   0x8006996C              ; malloc(a0 = size)
  move  a0, a1
  b     @@got
  nop
@@realloc:
  jal   0x800699BC              ; free(a0) then malloc(a1)
  nop
@@got:
  beqz  v0, @@fail
  nop
  j     0x8004F4E8
  sw    v0, 0xC(s0)
@@fail:
  lw    v0, 0x14(s0)            ; k
  nop
  andi  v0, v0, 1
  sll   v0, v0, 2
  addu  v0, s0, v0
  j     0x8004F530              ; return: cap, +0xC and k unchanged
  sw    zero, 4(v0)             ; slot[k&1] was freed (or never allocated)

; ---- DAY save: memory-card title (sprintf of day.002a0 -> 0x80157E68, strcpy'd into the card header at 0x8005DEEC).
; The BIOS card manager wants full-width Shift-JIS, so ASCII is widened here (the shared row converter 0x80012EE0
; keeps ASCII for the VWF). Capped at 62 bytes + 00: the card title field is 64, the buffer 0x50 (next symbol
; 0x80157EB8, tools/xref_range.py). A long label loses the time at the end (day.002a0 format). ----
title_wide:                     ; a0 = dst, a1 = src (Shift-JIS pairs copied as is)
  addiu t2, a0, 62
@@loop:
  lbu   t0, 0(a1)
  nop
  beqz  t0, @@end
  addiu t1, a0, 2
  sltu  t1, t2, t1              ; no room for one more pair
  bnez  t1, @@end
  sltiu t1, t0, 0x80
  bnez  t1, @@ascii
  lbu   t3, 1(a1)
  sb    t0, 0(a0)
  sb    t3, 1(a0)
  addiu a1, a1, 2
  b     @@loop
  addiu a0, a0, 2
@@ascii:
  sltiu t1, t0, 0x20
  bnez  t1, @@next              ; control byte: dropped
  addiu t1, t0, -0x20
  sll   t1, t1, 1
  la    t3, wide_tab
  addu  t3, t3, t1
  lhu   t1, 0(t3)
  nop
  srl   t3, t1, 8
  sb    t3, 0(a0)
  sb    t1, 1(a0)
  addiu a0, a0, 2
@@next:
  b     @@loop
  addiu a1, a1, 1
@@end:
  jr    ra
  sb    zero, 0(a0)
wide_tab:                       ; ASCII 0x20-0x7F -> full-width Shift-JIS
  .halfword 0x8140, 0x8149, 0x8168, 0x8194, 0x8190, 0x8193, 0x8195, 0x8166
  .halfword 0x8169, 0x816A, 0x8196, 0x817B, 0x8143, 0x817C, 0x8144, 0x815E
  .halfword 0x824F, 0x8250, 0x8251, 0x8252, 0x8253, 0x8254, 0x8255, 0x8256
  .halfword 0x8257, 0x8258, 0x8146, 0x8147, 0x8183, 0x8181, 0x8184, 0x8148
  .halfword 0x8197, 0x8260, 0x8261, 0x8262, 0x8263, 0x8264, 0x8265, 0x8266
  .halfword 0x8267, 0x8268, 0x8269, 0x826A, 0x826B, 0x826C, 0x826D, 0x826E
  .halfword 0x826F, 0x8270, 0x8271, 0x8272, 0x8273, 0x8274, 0x8275, 0x8276
  .halfword 0x8277, 0x8278, 0x8279, 0x816D, 0x815F, 0x816E, 0x814F, 0x8151
  .halfword 0x814D, 0x8281, 0x8282, 0x8283, 0x8284, 0x8285, 0x8286, 0x8287
  .halfword 0x8288, 0x8289, 0x828A, 0x828B, 0x828C, 0x828D, 0x828E, 0x828F
  .halfword 0x8290, 0x8291, 0x8292, 0x8293, 0x8294, 0x8295, 0x8296, 0x8297
  .halfword 0x8298, 0x8299, 0x829A, 0x816F, 0x8162, 0x8170, 0x8160, 0x8140
.align 4
evd_names:
  .incbin EVDNAMES
.if org() > STR_POOL
  .error "payload code/tables run into STR_POOL"
.endif
.org STR_POOL                   ; EXE/overlay strings too long for their place (tools/insert.py STR_POOL, repointed refs)
  .incbin STRPOOL
.align 4
payload_end:
.headersize 0x8000F800

; the source only has to stay inside the file's zero area (BSS 0x800B6408-0x80162F88): the stub copies it before
; START zeroes that area, so nothing else is there yet
.if orga() > (0x80162F88 - 0x8000F800)
  .error "payload source runs past the EXE's zero area"
.endif
.if payload_end > 0x801F7FF8
  .error "payload runs into the stack"
.endif

.org 0x8004F4B8                 ; 2D pool growth: was lw v0, 0x30(s0) / nop (a0 = slot load above, delay done here)
  j     pool_grow
  nop

.org 0x8001E278                 ; evd op 0x34: was sw v1, 0x10(v0) (the next op, sh a1, 0xC6(gp), is the delay slot)
  j     evd_name_hook

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

; ---- battle-quote block (UNN g13) buffer: malloc(0x2800) at 0x80044BB4 -> static G13_BUF ----
; A bigger malloc failed on a tight heap (HEN formation screen, ev43: v0 = 0, the CD DMA then wrote the kernel at 0).
; Every caller reads the block through gp+0xBF4 (none keeps v0), so one static buffer is safe; the release at
; 0x80044C10 frees gp+0xBF8 only when it equals gp+0xBF4: that free is skipped (it would corrupt the heap).
.org 0x80044BC0                 ; was: addiu a0, zero, 0x2800
  lui   v0, hi(G13_BUF)
.org 0x80044BC8                 ; was: jal 0x80064370 (malloc); its delay slot (sw s0) stays
  addiu v0, v0, lo(G13_BUF)
.org 0x80044C24                 ; was: jal 0x80064390 (free)
  nop

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

; ---- DAY.BIN (overlay at 0x80166218): memory-card title in full-width Shift-JIS ----
.open DAY, 0x80166218
.org 0x8016ABB8                 ; was: jal 0x80012EE0 (a0 = 0x80157E68 title, a1 = sp+0x30 sprintf result)
  jal   title_wide
.close
