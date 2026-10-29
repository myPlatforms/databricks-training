"""Repair '** text**' corruption and apply bold+Hangul spacing by **-segment parity (not regex pairing)."""
import pathlib, re, sys

HANGUL = re.compile(r'[가-힣]')
CODE = re.compile(r'`[^`\n]*`')

def fix_line(line):
    codes = []
    def protect(m):
        codes.append(m.group(0)); return f'\x00{len(codes)-1}\x00'
    work = CODE.sub(protect, line)
    segs = work.split('**')
    stripped = spaced = 0
    if len(segs) % 2 == 1 and len(segs) > 1:          # balanced **
        for i in range(1, len(segs), 2):             # odd = bold content
            if segs[i].startswith(' ') and segs[i].strip():
                segs[i] = segs[i].lstrip(' '); stripped += 1
            nxt = segs[i + 1]
            if nxt and HANGUL.match(nxt[0]):
                segs[i + 1] = ' ' + nxt; spaced += 1
        work = '**'.join(segs)
    work = re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], work)
    return work, stripped, spaced

tot_s = tot_p = 0
for f in sorted(pathlib.Path(sys.argv[1]).rglob('*.md')):
    t = f.read_text(encoding='utf-8'); out = []; fence = False
    for ln in t.split('\n'):
        if ln.lstrip().startswith('```'):
            fence = not fence; out.append(ln); continue
        if fence: out.append(ln); continue
        new, s, p = fix_line(ln); tot_s += s; tot_p += p; out.append(new)
    nt = '\n'.join(out)
    if nt != t: f.write_text(nt, encoding='utf-8')
print('stripped leading spaces:', tot_s, '| hangul spacing added:', tot_p)
