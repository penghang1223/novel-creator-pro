import re

with open('novel_output/番茄/006_说好做个摆烂NPC怎么全服都叫我爹/正文/第001章-我穿越成了NPC.md', encoding='utf-8') as f:
    content = f.read()

# Find all unique quote-like characters
quotes = set()
for ch in content:
    if ch in '“”‘’「」『』＂„‟″〈〉《》（）—–':
        quotes.add(ch)

print('Quote chars found:', [(q, hex(ord(q))) for q in quotes])

# Show lines with Chinese quotes
lines = content.split('\n')
count = 0
for i, line in enumerate(lines):
    if re.search(r'[“”「」]', line):
        print(f'Line {i+1}: {line[:120]}')
        count += 1
        if count >= 30:
            break
