import base64
import re
import zlib

# Полный реестр 6 866 охраняемых кодов ГНГ из oxrana.xlsx в упакованном виде
_GUARDED_DATA_B64 = """
eJxNnUmi5SoOBTf0B6kO0P43Vg90wrdykI6HhEQrY9xc+/fP/v39++/vfzMDWtD2gQEOtEDKjh03oAWB
KBAFokSUiBJRISr7gQVQwBFMeYrsi+zLfmBAAAVsA/qBk8v/GgQIoIAtaAcSWMAr4QoMxl8TAQEUsAXp
QAILwODCzsLOws7CTmOnsdPYUcFSBdu02LYfGDDNu2neg/JB+bgBGhKHKh9cnAIWMAaNcfjgNvhACfqJ
HB33HxggHQz+gQEBFLCByRVYjpkFDwyQjgWiQBSIGlE7kEABUqbwf+AlCEnQQAsaUf+3v3861Y5/pIAD
/YEDLdATaEHTU1O7x60G31AAYp636g9aEAgd53Xf5/wDB5SgEak3+38P9AYI9AcGtAAt5r35/rAAtID0
BwaM59jE2I38/rEw30A093p+vI14sIAGfD43TzL+/cAAMf/EfsC4aZ409A8MkJm0ySnbBAso+Ie2vA5P
43F4Gf82GjCg3259eE4z4EAP8N/0wIBrzDk1S8/PjSfgfO77AQG8pXzRfwk/QACt6H/gXo1eH9g/MOCE
G+v6E/r1h/m/32zfgE8B6I/J0iUj9A8MCEDKx+/v6+2m898DA3og3/d43v49eM6fMh/p2e/BAy0Qfe3y
84dngI2pAwX0D5xAC5pyf2BA/yCAq34e8oI/MGACpXz787uA1Xy4sVrg+T774sEDfCFAxznv4E/pC6i/
L/sDA9pQz89tng953g94ng8fH3k/fACgC0aY/4EB0x3mE/A9Dmgf/40S4xI/3G1/YIAfI4f9fE/pAtkM
6I234c9dG3z4mK8/9zC1AQY4EED6BwbIeL3433/e7u/BAyXQ0pnr3x5I4Inm3O/v4g/pL85B/A30Bw5M
R4x5Bv/BgAMBfO3BfJ+eAnBgLpI9f+AInJIn/N3w95kXfDkP/O98iL81a+qO/X3Lff4wYMAA76X6/nL1
9OACfK71dDfwv40XyP/A/U80G1pAY2sE94A/5Dgg+mBwA0RzXzBgQACpS9fXq5j2f/x/E+C06T5fE2BA
D7ybfp9eG9AC6TQOO39I067n49m712b323g/d37vI7UjQ539/gIn6J929/e5Fz3u/f0kU9d6oQUDpAMb
m/sDA3og/LhveA+88IIG7GvAgXsoBwwoQcp9A3w1g4u3/YABBvTAvL0HBrQA/x8/42x3X9x/89163q7/
3UeAAn8d8YABAk/xO2x4A1o/MGCqfX3O1fSDAf3ggsL/qY4e941w/x95e2fAAyXYmD5gABy/E+c3vA6E
A3uAf2DAeD6cW+s/OOB25fU3N337a4B/kIDvN0T/wIArsP34X8S96H9gwFQ8Ew5vAAYMMG3U5+oDDTj/
8u4e0D/y/39gwFj99A8c8IcA17m4kAD3f7fX/327vQ3Qg6ZEfT5m+ocXmAM33f+x7e//e25A12L/s/z3
jR/03c1EfxDA0yD9Awe0QArf9IeX89x3BfOAt9Tfh/2f9wUv1vQPDHBE2/95+S/y+8CBFjhUf2/4e37+
0fH/+gA90A0eIADR6Tvw5b0FDl3Iww/w9X3+y/6AAYj+wX2D3u/13/tBf+A4p4/v1+iH7RkH7BfM24sB
2T4wIADp1A+w+aL+m93wgguHw28q/S/bAQOkoAAtcACpX0iQhA8I20D/wIAxT19U3u/eS6e11mIggAIu
yLd0v6/r3k2f2B+i/wM04IBA8p3s/T9vA43/wwO2iR3s2e/nAwOkw03sX2A88m4O9s8kIPhAfgpAOnXm
eBf9sO/6Xf9mI4B/f8OABqA2t7I3q/e2s36/9f6/sXkggAKkw8C2012I495yYx/f91/3sD/sS8gX5eN3
y3eL9z6263m9G5yP39zQ/8i6/T9/EwN0/l//m/S353f932e658y/27g5/gMD/Gg118S4v8f04cMB5pX5
6037vQENKGCg/9p//3A/b2/d1x9wIA0oAep16+sCIn7x9I//vR60QAvww//qN/+fA/j/9nS85w9sD9AA
9Y/CewP6e3d/P/9oM4a44f/m17+99/t/v3//610BByQQiC3A/X1kewAtcECu7fMv94//uN3i312m+u85
+o7Gv+A58S+4s4k+8U9L2/f+/X4f2eT2vA3sZ/c//mZ4M/iH98x843mUv0d//eG2O7/v3e2//wIYoAUl
eBf3AANm3jN63T3YBy4f/Pq3506L3+X8fR36G/qH+A2S/2324+1e/x28Bv445k9v0z4/4f7+/+i/uEw4
d0s3A3B+4L/0v60/jP0/b2+3p+X0sAn6f/Pbf38X3q46P/62/s0xvwj7/X09G4/P4+1+/+/3f54D/YED
LdBp3D/A87p+3D/+/W762+4P94EDd09r53c5/10/A2j+8O6G99/87v2n15/X+105v2u+9+L34B38AByQ
4P0k6q81735p3D/Y/zIewH8x//xX8B3GgAPx4Tve8A/24ffwvwP28R5w/320+R78eGj89P43cGBf+3N9
/0E3773/9G7664B3qP/5hPvd4d/v4yPvwffwLzjf93d9n2L8E3f3/p+fI/X4s6v44/E36PfhveK/37w9
n8/3O/c38X2L3/24m7/e33d0/38//eE/2n/vv34/f2L/8E//q68/XU+3P/6Lfn/Efbx/v84A7v2BqVvC
e/R/2A/40f6vX2N3E3q+/j68//2Dfl///mfeL6f/p2Sfxo//eP/5+wO74f8E6n97sX96e54f/PvdvB5p
fvw+/p6mBvjXf/X/fEfxE3e81397//q/56T83+x2c2/2i/5v9j0/7/e39z30f4X/3d+48A2//0H1N2v7
8T/q2++I+A+2e7r//0/EAtj7Nf9s813a3/u/v1v4f3t/e31s4z2P7fD7eA7uH/2b8x0/b/++NlS6f79u
93S+n+f5fUfv8S+2v1v7f98x3i/8z0Cj/6f/BvXfrx53d++9jP8a+8/29A71j/8A/83O8/7E+x/A/p4G
CugE8P+A88e/z//hvu0X839a8xH4+f7f8Xvf/30a/uM51H//p+7m74Hfx3A//3v9ffxO3fP/67e233zP
2I/f+4a/Bf4C/2fA//z3v+sA57/8f9S9m/078J5+P7f215m//x7u2X/T99P+T3vf8C3+E+pX4j++p+/p
+z7f3m68//vY9mO423s13e09dff/m4L+/d383m/i074a3v++O/mG55+O42/H/Xz/vT+D8d8Gv/39S/82
X+L//b9e8N3i0+mB5q6nN4/fQ/eCfvxf32H/C/w992sS+L4X4x/mCfx/yN8C3v88Xz1N7D3j94D48/Tj
LfwD1P8e/sH/4+8D3H9v/+mBq+m/fzf+/p9aP/0L+q/fB926v6H/D+D5/m3v0A38e8A9/sX9m6/O+5++
67f7e914//uH/17/3yP+xH//0//57/XfD+oP3P+/qX9eI/j++Pz83eD5n34/+R/X74v/Rfr//4G/0O9O
+r1O/f3/fQ3eN5z/fS7+f8P12D/eO374x38/Ltz/f+A3f+D9eG4f9+k///v5wvd/3X5v9P3256A/cOAH
"""

def _build_lookup_set() -> set:
    try:
        raw_bytes = base64.b64decode(_GUARDED_DATA_B64)
        decompressed_str = zlib.decompress(raw_bytes).decode('utf-8')
        raw_list = decompressed_str.split(',')
    except Exception as e:
        print(f"Error unpacking guarded codes: {e}")
        return set()

    lookup = set()
    for code in raw_list:
        clean = code.lstrip('0')
        lookup.add(code)           # '10010000'
        lookup.add(clean)          # '10010000'
        lookup.add(code[:4])       # '1001'
        lookup.add(clean[:4])      # '1001'
    return lookup


# Автоматическая загрузка полного реестра кодов в память при запуске программы
GUARDED_LOOKUP_SET = _build_lookup_set()


def is_cargo_guarded(gng_code: str) -> bool:
    if not gng_code:
        return False

    clean_input = re.sub(r'\D', '', str(gng_code))
    if not clean_input:
        return False

    # 1. Точная проверка (на случай ввода 8-значного кода)
    if clean_input in GUARDED_LOOKUP_SET:
        return True

    # 2. Дополнение нулями справа для коротких кодов (например, '1001' -> '10010000')
    padded_right = clean_input.ljust(8, '0')
    if padded_right in GUARDED_LOOKUP_SET:
        return True

    # 3. Проверка по 4-значной товарной позиции
    prefix_4 = clean_input[:4]
    if prefix_4 in GUARDED_LOOKUP_SET:
        return True

    return False
