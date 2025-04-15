
"""
    Op-kod        Grx   Adr mod             Adress
|--------------||------||------||------------------------------|

        Optional Operand (för immidiet addressering)
|--------------------------------------------------------------|

Op 4 bitar vilken instruktion som avses.
GRx 2 bitar vilket av de fyra generella registren som ska användas.
M 2 bitar anger adresseringsmetod.
ADR 8 bitar adressfält
Operand 16 bitar operand
"""
"""
ADD_MOD = KONSTANT 8bit | KONSTANT 16bit | [ADRESS] | [ADRESS,GR3]

M=00 Direkt adressering, instruktionsformat 1. Innehållet i ADR fältet är adressen till
den minnescell i vilken operanden finns.
LOAD R0, KONSTANT 8bit

M=01 Omedelbar operand, instruktionsformat 2. Det efterföljande ordet innehåller
operanden.
LOAD R0, KONSTANT 16bit

M=10 Indirekt adressering, instruktionsformat 1. ADR fälet innehåller adressen till
den minnescell där adressen till operanden finns.
LOAD R0, [ADRESS]

M=11 Indexerad adressering med GR3, instruktionsformat 1. Summan av innehållet
i ADR fältet och innehållet i GR3 är adressen till operanden.
LOAD R0, [ADRESS,GR3]

STORE GRx,M,ADR PM(A) := GRx 00,10,11 -
STORE GRx ADD_MOD (ej indirrekt addressering tack)

ADD GRx,M,ADR GRx :=GRx+PM(A) 00,01,10,11 Z,N,O,C
ADD GRx ADD_MOD

SUB GRx,M,ADR GRx :=GRx-PM(A) 00,01,10,11 Z,N,O,C
SUB GRx ADD_MOD

AND GRx,M,ADR GRx :=GRx and PM(A) 00,01,10,11 Z,N
AND GRx ADD_MOD

LSR GRx,M,Y GRx skiftas logiskt - (ange 00) Z,N,C utskiftad bit
höger Y (ADR-f¨altet) steg
LSR Grx KONSTANT 1-16

BRA ADR PC :=PC+1+ADR - (ange 00) -
BRA ADDRESS

BNE ADR PC := PC+1+ADR - (ange 00) -
om Z=0, annars
PC:= PC+1
BNE ADDRESS

HALT avbryt exekv. - (ange 00) -
HALT
"""

def get_instruction_size(instruction: str) -> int:
    return 1 + '#' in instruction


def assemble(instructions: list[str]) -> list[int]:
    OP_CODE_OFFSET = 12
    REG_OFFSET = 10
    ADDR_MOD_OFFSET = 8

    assembled = []
    var_values = []
    var_start_address = None
    var_addresses = {}
    label_to_address = {}
    label_consumer = {}

    def parse_num(num: str):
        if num.startswith('0x'):
            return int(num[2:], 16)
        elif num.startswith('0b'):
            return int(num[2:], 2)
        elif num in var_addresses:
            return var_addresses[num]
        else:
            return int(num)

    def do_the_addr_mod(addr: str, compiled: int):
        if addr.startswith('#'):
            compiled += 0b01 << ADDR_MOD_OFFSET
            assembled.append(compiled)
            assembled.append(parse_num(addr[1:]))
            return
        if addr.startswith('[[') and addr.endswith(']]'):
            compiled += 0b10 << ADDR_MOD_OFFSET
            compiled += parse_num(addr[2:-2])
        elif addr[0] == '[' and addr.endswith(',]'):
            compiled += 0b11 << ADDR_MOD_OFFSET
            compiled += parse_num(addr[1:-2])
        elif addr[0] == '[' and addr.endswith(']'):
            compiled += 0b00 << ADDR_MOD_OFFSET
            compiled += parse_num(addr[1:-1])
        elif addr in var_addresses:
            compiled += 0b00 << ADDR_MOD_OFFSET
            compiled += var_addresses[addr]
        elif addr.startswith('%'):
            compiled += 0b00 << ADDR_MOD_OFFSET
            label_consumer[len(assembled)] = addr
        else:
            print(instruction)
            raise ValueError(f'Unknown format for instruction on line {row + 1}.')

        assembled.append(compiled)

    def do_the_branch(addr, compiled):
        compiled += 0b00 << ADDR_MOD_OFFSET
        address_offset = (-len(assembled) - 1) & 0xFF
        compiled += address_offset
        label_consumer[len(assembled)] = addr
        assembled.append(compiled)

    for (row, instruction) in enumerate(instructions):
        # Comment or empty line
        if instruction.startswith(';') or instruction == '\n':
            continue

        # Assembly setting
        elif instruction.startswith('@'):
            setting, value = map(str.strip, instruction[1:].split('='))
            if setting == 'VAR_ADDRESS':
                var_start_address = parse_num(value)
            else:
                raise ValueError(f'Unknown assembly setting on line {row + 1}')
            continue

        # Variable declaration
        elif instruction.startswith(':'):
            name, value = map(str.strip, instruction.split('='))
            try:
                var_addresses[name] = var_start_address - len(var_values)
            except TypeError:
                raise ValueError(f'Variable declaration appered before VAR_ADDRESS assembly setting was set on line {row + 1}')
            var_values.append(parse_num(value))
            continue

        # Label
        elif instruction.startswith('%'):
            label_to_address[instruction.strip()] = len(assembled)
            continue

        match instruction.split():
            # LOAD GRx,M,ADR GRx := PM(A) 00,01,10,11 -
            case 'LOAD', reg, addr:
                compiled = (0 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)
                
            # STORE GRx,M,ADR PM(A) := GRx 00,10,11 -
            case 'STORE', reg, addr:
                compiled = (1 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)

            # ADD GRx,M,ADR GRx :=GRx+PM(A) 00,01,10,11 Z,N,O,C
            case 'ADD', reg, addr:
                compiled = (2 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)

            # SUB GRx,M,ADR GRx :=GRx-PM(A) 00,01,10,11 Z,N,O,C
            case 'SUB', reg, addr:
                compiled = (3 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)

            # AND GRx,M,ADR GRx :=GRx and PM(A) 00,01,10,11 Z,N
            case 'AND', reg, addr:
                compiled = (4 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)

            # LSR GRx,M,Y GRx skiftas logiskt - (ange 00) Z,N,C utskiftad bit
            # höger Y (ADR-fältet) steg
            case 'LSR', reg, steps:
                compiled = (5 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET) + parse_num(steps[1:])
                assembled.append(compiled)

            # BRA ADR PC :=PC+1+ADR - (ange 00) -
            case 'BRA', addr:
                compiled = (6 << OP_CODE_OFFSET) + parse_num(addr)
                do_the_branch(addr, compiled)

            # BNE ADR PC := PC+1+ADR - (ange 00) -
            # om Z=0, annars
            # PC:= PC+1
            case 'BNE', addr:
                compiled = (7 << OP_CODE_OFFSET)
                do_the_branch(addr, compiled)

            # HALT avbryt exekv. - (ange 00) -
            case 'HALT',:
                compiled = (8 << OP_CODE_OFFSET)
                assembled.append(compiled)

            # CMP, GRx,M,ADR GRx :=GRx-PM(A) 00,01,10,11 Z,N,O,C
            case 'CMP', reg, addr:
                compiled = (9 << OP_CODE_OFFSET) + (parse_num(reg) << REG_OFFSET)
                do_the_addr_mod(addr, compiled)

            # BGE, branch if grater or equal, asumes 2s-complemet numbers are compared
            case 'BGE', addr:
                compiled = (0xA << OP_CODE_OFFSET)
                do_the_branch(addr, compiled)

            # BEQ, branch if equal
            case 'BEQ', addr:
                compiled = (0xB << OP_CODE_OFFSET)
                do_the_branch(addr, compiled)

            case _:
                raise ValueError(f'Error parsing row {row + 1}, didnt match any known instruction')

    for address, label in label_consumer.items():
        inst, addr = assembled[address] & 0xFF00, assembled[address] & 0xFF
        assembled[address] = inst + ((label_to_address[label] + addr) & 0xFF)
    
    return assembled, var_values, var_start_address


def format_hex(num: int, digits: int) -> str:
    hexed = hex(num)[2:]
    if len(hexed) < digits:
        hexed = '0' * (digits - len(hexed)) + hexed
    return hexed


def output(file, instructions: list[int], var_values: list[int], var_start_address: int):
    MEM_SIZE = 0x100

    memory_lines = []
    for (line, inst) in enumerate(instructions):
        memory_lines.append(f'{format_hex(line, 2)}: {format_hex(inst, 4)}')
    
    for line in range(len(instructions), MEM_SIZE):
        if line == var_start_address - len(var_values):
            break
        memory_lines.append(f'{format_hex(line, 2)}: 0000')

    for variable in reversed(var_values):
        line += 1
        memory_lines.append(f'{format_hex(line, 2)}: {format_hex(variable, 4)}')

    for line in range(line + 1, MEM_SIZE):
        memory_lines.append(f'{format_hex(line, 2)}: 0000')

    with open(file, 'w') as file:
        file.write('PM:\n')
        file.write('\n'.join(memory_lines))
        file.write("""

MyM:
00: 00f8000
01: 008a000
02: 0004100
03: 0078080
04: 00fa080
05: 0078000
06: 00b8080
07: 0240000
08: 1184000
09: 0138080
0a: 00b0180
0b: 0190180
0c: 0380000
0d: 08b0000
0e: 0130180
0f: 0380000
10: 0ab0000
11: 0130180
12: 0380000
13: 0cb0000
14: 0130180
15: 0041000
16: 0380000
17: 1a00800
18: 000061a
19: 0000297
1a: 0130180
1b: 02c0000
1c: 0840000
1d: 0118180
1e: 02c0420
1f: 0840000
20: 0118180
21: 0000780
22: 0380000
23: 0a80180
24: 02c0429
25: 00004a8
26: 00005aa
27: 00002a9
28: 000072a
29: 0840000
2a: 0118180
2b: 02c022d
2c: 0840000
2d: 0118180
2e: 0000000
2f: 0000000
30: 0000000
31: 0000000
32: 0000000
33: 0000000
34: 0000000
35: 0000000
36: 0000000
37: 0000000
38: 0000000
39: 0000000
3a: 0000000
3b: 0000000
3c: 0000000
3d: 0000000
3e: 0000000
3f: 0000000
40: 0000000
41: 0000000
42: 0000000
43: 0000000
44: 0000000
45: 0000000
46: 0000000
47: 0000000
48: 0000000
49: 0000000
4a: 0000000
4b: 0000000
4c: 0000000
4d: 0000000
4e: 0000000
4f: 0000000
50: 0000000
51: 0000000
52: 0000000
53: 0000000
54: 0000000
55: 0000000
56: 0000000
57: 0000000
58: 0000000
59: 0000000
5a: 0000000
5b: 0000000
5c: 0000000
5d: 0000000
5e: 0000000
5f: 0000000
60: 0000000
61: 0000000
62: 0000000
63: 0000000
64: 0000000
65: 0000000
66: 0000000
67: 0000000
68: 0000000
69: 0000000
6a: 0000000
6b: 0000000
6c: 0000000
6d: 0000000
6e: 0000000
6f: 0000000
70: 0000000
71: 0000000
72: 0000000
73: 0000000
74: 0000000
75: 0000000
76: 0000000
77: 0000000
78: 0000000
79: 0000000
7a: 0000000
7b: 0000000
7c: 0000000
7d: 0000000
7e: 0000000
7f: 0000000

K1:
00: 0a
01: 0b
02: 0c
03: 0f
04: 12
05: 15
06: 1b
07: 1e
08: 21
09: 22
0a: 24
0b: 2b
0c: 00
0d: 00
0e: 00
0f: 00

K2:
00: 03
01: 04
02: 05
03: 07

PC:
00

ASR:
00

AR:
0000

HR:
0000

GR0:
0008

GR1:
0000

GR2:
0000

GR3:
0000

IR:
0000

MyPC:
00

SMyPC:
00

LC:
00

O_flag:

C_flag:

N_flag:

Z_flag:

L_flag:
End_of_dump_file
                   """)


if __name__ == '__main__':
    # print(list(map(bin, assemble(['LOAD 2 255', 'LOAD 2 511', 'LOAD 0 [123]', 'LOAD 3 [123,]']))))
    # print(list(map(bin, assemble(['STORE 0 255', 'ADD 0 255', 'SUB 0 255', 'AND 0 255', 'LSR 0 4', 'BRA 255', 'BNE 255', 'HALT']))))
    with open('main.asm') as file:
        instructions, var_values, var_start_address = assemble(file.readlines())
        output('main.mia', instructions, var_values, var_start_address)