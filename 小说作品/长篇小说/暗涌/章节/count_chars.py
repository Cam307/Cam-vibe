# -*- coding: utf-8 -*-
import os

path = os.path.dirname(os.path.abspath(__file__))
total = 0
details = []

for fname in os.listdir(path):
    if not fname.endswith('.md') or '第' not in fname or '章' not in fname:
        continue
    try:
        num = int(fname.split('第')[1].split('章')[0])
    except (IndexError, ValueError):
        continue
    fp = os.path.join(path, fname)
    if os.path.isfile(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()
        n = len(text)
        total += n
        details.append((num, fname, n))

details.sort(key=lambda x: x[0])
print('Total chars:', total)
for num, name, n in details[:5]:
    print(name, n)
print('...')
for num, name, n in details[-3:]:
    print(name, n)
