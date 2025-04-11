
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
def parse_num(num: str):
    num = num.lower()
    if num.startswith('0x'):
        return int(num[2:], 16)
    elif num.startswith('0b'):
        return int(num[2:], 2)
    else:
        return int(num)

def assemble(instructions: list[str]) -> list[int]:
    OP_CODE_OFFSET = 12
    REG_OFFSET = 10
    ADDR_MOD_OFFSET = 8

    assembled = []

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
        else:
            raise ValueError('Unknown format for LOAD instruction.')

        assembled.append(compiled)

    for (row, instruction) in enumerate(instructions):
        # Comment
        if instruction.startswith(';') or instruction == '\n':
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
                assembled.append(compiled)

            # BNE ADR PC := PC+1+ADR - (ange 00) -
            # om Z=0, annars
            # PC:= PC+1
            case 'BNE', addr:
                compiled = (7 << OP_CODE_OFFSET) + parse_num(addr)
                assembled.append(compiled)

            # HALT avbryt exekv. - (ange 00) -
            case 'HALT',:
                compiled = (8 << OP_CODE_OFFSET)
                assembled.append(compiled)

            case _:
                raise ValueError(f'Error parsing row {row}, didnt match any known instruction')
    
    return assembled


def format_hex(num: int, digits: int) -> str:
    hexed = hex(num)[2:]
    if len(hexed) < digits:
        hexed = '0' * (digits - len(hexed)) + hexed
    return hexed


def output(file, instructions: list[int]):
    with open(file, 'w') as file:
        file.write('\n'.join((f'{format_hex(line, 2)}: {format_hex(inst, 4)}' for (line, inst) in enumerate(instructions))))


if __name__ == '__main__':
    # print(list(map(bin, assemble(['LOAD 2 255', 'LOAD 2 511', 'LOAD 0 [123]', 'LOAD 3 [123,]']))))
    # print(list(map(bin, assemble(['STORE 0 255', 'ADD 0 255', 'SUB 0 255', 'AND 0 255', 'LSR 0 4', 'BRA 255', 'BNE 255', 'HALT']))))
    with open('main.asm') as file:
        output('output.txt', assemble(file.readlines()))