import base64
import re
import zlib

# Полный реестр 6 866 охраняемых кодов ГНГ из oxrana.xlsx в упакованном виде
_GUARDED_DATA_B64 = """
eJxN3U1y3DoOBuD1d3HVATr1D/WA3b/KTTreI3K8T8a8P98/x//Pz9//9kEDfND4QQ/qQch+fD4e
f3qAAnzQeL5//9B0vvdC+aDx+Xk/fKCb2/v2QfmgI/f32gd9e6A3v3t/f2+aP/Dtg769v1//6G4/6Nt7
v1/vG/7Qj//eN+sD/e3vD/vA/1PzB3x7f6828Ie/f2+/b/y/qfn/32f2f11+f/f3aO3p/uGvev1A15f6
fX0Xm3l9mS/399/t/v3o+s+sD7T4x33P/p70T3y53S+/f7e/59sH3dy3x33Qe0Hj+/p+v++f/f493/1N
mvhD/x+9L30Nvn4Dvdv7xT4/N6sPPs92o9fX69X2A+vN3m0/m09/o7Xvf839A293z/p6vf4aX//F63f1
N+r9A+/j9ftHfeA33jfwvv5+/Xo9s4+/zL5/43/33z94+a90//mS+z4+m2++/7o2ff+2j//5/A3eN4/X
b/G34Hrfv9Tf2/614PXe6GvjD4m/Uvf333X1P9rNf51//c29//vO622+mfeC/X/7r032m//3D9m04v6e
1zL/TfaX4pvn632m3xI/z/p95u//+c7o/y038M+03nfg6z64v6e4j7+p5ffG/Nvf32i+/4uX+f/8H2O8
mfl1qO+m92p8d3LffL3Nf9eL5/aN3jTebPPd78X/0pvm23y93c+f3994/fI8b56v999lS/rXm+erfX3j
+/S7vfn6e//6rX3X++2X7//bH2B+w7i/zX390j/Q/sS3T3x/7w+8/36z2+v7bL5/2X7130+2b3a//eB6
c92+4z++qL5vH03f90+/qL/f1j3eN3+Pze81+M1d+9n21/D88N3c/uT7xTff4I/36aPvA9vX77m/Z//6
N/0X8P1g23xX9P3sD7a+L9eXm+/vA2/uN3rf3//j/c329/7yP33rA3T/+pDvf3/1d38R/2W3+3rfp/P/
3/u238d2f+fX//5G09evxR/+9v9u9/4d//H5+j7j+4jvf9m2p7/c/52+3/2f+zP1d1v/+/36+219vS+u
/2qbf7qft1e3/O//m16/EfyI/eD6NfD4+U3Tvvv1qflx3f1fL9m+/lff7/M//qbbv8483z+4L9Xff6e5
33N+76+/19//49pff9M/pD/+x3u++d3L9q//x/7339f4O8/34y+/w/TfH7/O11++9u3vH9sHfU1e//pG
5+8vM5r34293Nl//E1e+XvPdr9/k/mXG6y+/x//267/j9d5k2/y5r/eA8f+2vv/490n87fH9O/7s2zeP
//p1m+/H/168X79k//9sff1fX9e78/f7rI830//k3s/z/99j+e/1v33o1+/i7X3m+u12p7f/2mN/wOf/
8//u2zf1j1x/3d53pX/f5fve/b/5X/O+3tA33f/6pvn3v9c/vv813w2f19vb1X77NfLp64v89z1p/i2u
e7S2//j9m49vNf++E38n4p/t2xf2nff8Xv6f67vXl9pX+/qUft+5/k7r7941ve9S/P+p+D0fvvfe/v+p
1381/+7u67/s/jfxq/4/eJvX+8z/3719nfn/a33v0ffP+T//Pq//1eN7//z5X+/E3/I13/z22m8z9/3b
3x//62ve12Pxe3O8X1e8/1f63j+fvx+/8/d43X3T1yD8mH63b/7/I14Pvt52f4v2j+Yf+m/v+9qf61/7
s+/O3mbf+L993S/N//T43S7/Uu4/v++Xf/+/12f53d/H7u003z+a3zT/Dfb4u8/j+/d32/d4b4//yXtf
bN91+1+2/e+G+/fbf1//90e+/kL+/oHvx+b/+Zvv8+b7n2/z+/f7b2S+X5f/a7b/39XmX43X67q0v8a+
1v63eL42+u27969837a/Xbf3I/r7I3O/vv0L2b5vvf9+u634Rvt3/e/1b+4/2+5t+Xf179c3T/9p/b9r
+zH4/Z+/Sfdxvf+e23/83eH//aLvv4fH2/eN/+3/O9e/vE//+oX8/8H0/kH1T+L/E94m4X90+z/+m/m+
fv81vTf9A3v/yvd6+b+/3f769/6N22+S3x/6m5jv/y423+f8y2m+Xv1/5vG5Xv+2P9O64/744m+F//d+
v/r++2d+z/fveO/E/+q9P3pvhvfbvXfD+P//+/d9/xP//4vf7e62vvqG+0v3f3e6vvI3aN+4+/uMv1/k
93z1/f/a+/l1Nn3/z5/vY69d/sT03l76e8x/v+9/sL9++qI35p+/r94ffn99L+Jv3t/a/O//4f0d61v9
35veE2wfuD7v/6N3a3yX974e+XpffXm+v+b2d4L4P91eX177/ffm29d89/4+/R/y/f+/9/Wj9w9u31e4
/xPuv3i+//veo367X/6/f1sP/K/fO+e/u3/xvfB5L3S/e7x3e/m/uX198L//5fv762s78A2+y81eN6uX
+N9s4X8//p/+f/1H3m9N3w//eJ/55nv149/1ve1vT+bvhXf/43/+0vffX2p///35+l7vX2Xm89vH5/2T
+3f23iN6/+x3e3f3/3/rXv7//m33/2O9T6N93/O7u60X0f8Tfx+L3f1u7x939w1+3/P4+Xncf1+L1+/n
fT154p/y/W963/f6fWff45fA22j143a3xvd9G/E/9/e4+S5+0//N3y3//X4e1v/5+/r+9n+H//35fQ/f
3//6G/yA/+5/zdeL9x+/u//6E1/fvL7/+V8e4e+4/R+d/9v+e4v/d3a//9O/42/j17///fT1j942976w
/yvU33f4fvMvxft2X193X7/5e3j3O/X7bH//I/v34e42a/7p++/dffx1evp/N/9+/x7/E343/1184++M
+/vF3fP2feL/8/3pvuN3ff1vE3mffvf+r64m+m//x7u2X/m3p+Lvv8f6r9S/+I///++f7e34O+I6M33P
d38n/p/+9+3b2ff+eX+f6O9s9v2P3t/o69vxL274ff/eN/29L9c/0O+L/R+6f9m/C++vv4v4v//+/fv8
8fX6jH41+/Ptf+0f8T1G/d193/I6m337M/G3/r/3y3vf3z//x/fe2+3L7S/+m+/v8939+P6H3Tf3TfB9
9P42m/rfePvNvv7N7/Xf92x/t7v9R3r/+4v5e2/4fv+/x1v8b/T3Xp/mXzrf/x2uX/+xL4u//x3vX0f/
M+3vf92X+H8R/63b/7e8P//X9/D+/36/N3q9iX8D4f46/f4/X3++X4O///4b+11/+zvev6bfb9n/5n5e
b/+5L+1fvX+/5v458X1jff8n/qZ5X6ff32f91/m+vve4xPfC9y3v29H/j92/+d/p/+2+m3/v1S+33X2f
++f5H81X6S//4X25fR2v+13ff03N/jG8D1f/8pvn338R//72X1+8p+/X2989eL5evS++3s63L9H9E3vf
2/6//u4C+H23ft4ffS3ef+26r0m8/c70X/C5v8m3//D/2z4y4/s83vd0e73eN67f+3pG8+O4fvG2r8Xp
//8b4f//d++75t/f4vf1x+/T3++X32d/2242/8/5eXv4H39745u1x/p35m///2/83XG96X04f/5+b34X
zU//t++p2dfY79vM8/qA7m94f3l/y2vX12fxv6f//w+917T8Xk/8j+5ffM9mX/vF33v5f92n/D1Nn7N3
36vXk/+T/W/X5v3//D5w/xrfZ13m//q3v76i3l+i+S91f0//S7bf/v8399eN//0/0L66/r2P/6f3vNnv
A3ff5/T36d8f8Xk5///m9+X77r+m5o+396e///D3/7fX+wWv97fA+4bf//p70ePvS8x3l77vA/p39vf9
A++v5t9p/bO4n7+Z/m/w5vfV+x/8+/T/+vfT/lX8f/k+//0///vj/v/v8X/fP3s2m/8X
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
        lookup.add(code)
        lookup.add(clean)
        lookup.add(code[:4])
        lookup.add(clean[:4])
    return lookup


GUARDED_LOOKUP_SET = _build_lookup_set()


def is_cargo_guarded(gng_code: str) -> bool:
    if not gng_code:
        return False

    clean_input = re.sub(r'\D', '', str(gng_code))
    if not clean_input:
        return False

    padded_right = clean_input.ljust(8, '0')
    prefix_4 = clean_input[:4]

    return (
        clean_input in GUARDED_LOOKUP_SET
        or padded_right in GUARDED_LOOKUP_SET
        or prefix_4 in GUARDED_LOOKUP_SET
    )
