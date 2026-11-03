import sys
from search_failures import main
seed=int(sys.argv[1])
f=main(seed=seed, n_grids=6000, sizes=(5,6,7,8,10,12), dens=(0.25,0.35,0.45), weights=(1.5,2.0,4.0,8.0,20.0), ties=('hig','log','fifo','lifo'), pairs_per_grid=10)
print("TOTAL FAILURES", len(f))
