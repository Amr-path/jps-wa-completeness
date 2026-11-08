import re, ast, json
out = []
for i, w, N in [(1,1.0,9),(2,2.0,9),(3,1e6,9),(4,3.0,8),(6,1e6,8),(7,1.5,9)]:
    L = [l for l in open(f'logs_v2/climb_{i}.log') if l.startswith('DONE')][0]
    m = re.search(r"DONE \((.*?),\) evals (\d+) s= (\(.*?\)) t= (\(.*?\)) blocked= (\[.*\])", L)
    out.append(dict(name=f'climb{i}', w=w, N=N, reported=float(m.group(1)), evals=int(m.group(2)),
                    s=ast.literal_eval(m.group(3)), t=ast.literal_eval(m.group(4)), bl=ast.literal_eval(m.group(5))))
json.dump(out, open('logs_v2/climb_endpoints.json', 'w'))
for o in out: print(o['name'], o['w'], o['N'], o['reported'], o['evals'], o['s'], o['t'], len(o['bl']))
print('total evals', sum(o['evals'] for o in out))
