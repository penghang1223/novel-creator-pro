import re
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    text = f.read()

def is_dialogue_line(line):
    stripped = line.strip()
    if stripped.startswith('"') or stripped.startswith('"') or stripped.startswith('「'):
        return True
    dialogue_chars = 0
    for m in re.finditer(r'[""""""""""""](.*?)[""""""""""""]', stripped):
        dialogue_chars += len(m.group(1))
    total_cjk = len(re.findall(r'[一-鿿]', stripped))
    if total_cjk > 0 and dialogue_chars / total_cjk > 0.5:
        return True
    return False

def count_non_dialogue_chars(line):
    non_dialogue = line.strip()
    for m in re.finditer(r'[""""""""""""](.*?)[""""""""""""]', non_dialogue):
        non_dialogue = non_dialogue.replace(m.group(0), '', 1)
    return len(re.findall(r'[一-鿿]', non_dialogue))

lines = text.split('\n')
valid_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped or stripped.startswith('#') or stripped.startswith('---'):
        continue
    valid_lines.append((i+1, stripped))

max_c = 0
cur_c = 0
prev_d = False
chain_lines = []
best_chain = []

for line_no, line in valid_lines:
    if is_dialogue_line(line):
        if prev_d:
            cur_c += 1
        else:
            cur_c = 1
        prev_d = True
        chain_lines.append(f'  L{line_no} D: {line[:80]}')
    else:
        nd = count_non_dialogue_chars(line)
        if nd <= 15:
            chain_lines.append(f'  L{line_no} I({nd}chars): {line[:70]}')
        else:
            if cur_c > max_c:
                max_c = cur_c
                best_chain = chain_lines[:]
            cur_c = 0
            prev_d = False
            chain_lines = []

if cur_c > max_c:
    max_c = cur_c
    best_chain = chain_lines[:]

print(f'Max chain: {max_c} dialogue exchanges')
print('---Best chain---')
for l in best_chain:
    print(l)
