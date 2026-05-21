import re
import sys
import glob

def find_dialogue_chains(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    def is_dialogue(line):
        line = line.strip()
        if not line:
            return False
        return bool(re.search(r'[「」“”‘’＂]', line))

    def count_non_dialogue_chars(line):
        non_dialogue = line.strip()
        for m in re.finditer(r'[「」“”‘’＂](.*?)[「」“”‘’＂]', non_dialogue):
            non_dialogue = non_dialogue.replace(m.group(0), '', 1)
        return len(re.findall(r'[一-鿿]', non_dialogue))

    current_chain = 0
    chain_start = 0
    max_chain = 0
    max_chain_start = 0

    for i, line in enumerate(lines):
        if is_dialogue(line):
            if current_chain == 0:
                chain_start = i
            current_chain += 1
            if current_chain > max_chain:
                max_chain = current_chain
                max_chain_start = chain_start
        else:
            nd_chars = count_non_dialogue_chars(line)
            if nd_chars <= 15:
                pass
            else:
                current_chain = 0

    if max_chain >= 8:
        print(f'Max chain: {max_chain} lines starting at line {max_chain_start+1}')
        for i in range(max_chain_start, min(max_chain_start + max_chain + 3, len(lines))):
            print(f'  {i+1}: {lines[i].rstrip()}')
    else:
        print(f'OK - max chain {max_chain}')

base = 'novel_output/番茄/006_说好做个摆烂NPC怎么全服都叫我爹'
for ch in ['第001章', '第003章', '第026章']:
    files = glob.glob(f'{base}/正文/{ch}*.md')
    for f in files:
        print(f'=== {f.split("/")[-1]} ===')
        find_dialogue_chains(f)
        print()
