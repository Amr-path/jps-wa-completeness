import sys, random
from collections import Counter
from common import *
src=open('sweep_test2.py').read()
src=src.replace("""                    if w not in steps.get(S[i],set()):
                        cnt[""","""                    if w not in steps.get(S[i],set()):
                        if shown<8:
                            shown+=1; print(f'EXC2 kind={kind} o={o} dA={cd.get(o)} w={w} e={e} i={i} S_i={S[i]} by {steps.get(S[i])} S1={S[1]} by {steps.get(S[1])} S1closed={S[1] in cd} dA(S1)={cd.get(S[1])} S0={S[0]} by {steps.get(S[0])} S0closed={S[0] in cd} dA(S0)={cd.get(S[0])}'); print(grid_to_str(grid,s,None,[S[i],o]))
                        cnt[""")
src=src.replace("if shown<4 and not f0:","if False:")
exec(src)
