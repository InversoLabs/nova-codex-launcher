"""Bounded file operations executed by Codex's sandbox, never by the proxy."""
import ast
import base64
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote,urlsplit

def safe_path(root,value):
    if not isinstance(value,str) or not value or any(ord(c)<32 for c in value): raise ValueError('Invalid path')
    root=Path(root).resolve(); p=(root/value).resolve()
    if p==root or not p.is_relative_to(root): raise ValueError('Path outside workspace')
    if any(part.startswith('.') for part in p.relative_to(root).parts): raise ValueError('Hidden paths disabled')
    return p

def digest(p):
    if not p.exists(): return None
    if not p.is_file() or p.stat().st_size>2_000_000: raise ValueError('File too large or not a regular file')
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replaced_bytes(data,old,new):
    old=old.encode('utf-8'); new=new.encode('utf-8')
    # read_text presents LF to the model; preserve a Windows file's CRLF bytes.
    if old not in data and b'\r\n' in data and b'\r\n' not in old:
        old=old.replace(b'\n',b'\r\n'); new=new.replace(b'\n',b'\r\n')
    if not old or data.count(old)!=1: raise ValueError('Edit must match exactly once; read the relevant range and retry')
    return data.replace(old,new,1)

def apply_file(root,a,expected):
    p=safe_path(root,a['path'])
    if digest(p)!=expected: raise ValueError('File changed since edit was prepared; read it again')
    if a['tool']=='write':
        data=a['content'].encode('utf-8')
    else:
        data=replaced_bytes(p.read_bytes(),a['old'],a['new'])
    if len(data)>2_000_000: raise ValueError('Resulting file too large')
    if p.exists() and p.read_bytes()==data: raise ValueError('No change; run checks instead of repeating the edit')
    p.parent.mkdir(parents=True,exist_ok=True)
    # Check containment and original bytes again immediately before mutation.
    p=safe_path(root,a['path'])
    if digest(p)!=expected: raise ValueError('File changed before update')
    p.write_bytes(data)
    return 'Updated '+a['path']

def read_range(root,a):
    p=safe_path(root,a['path']); digest(p)
    start=a.get('start',1); count=a.get('count',80)
    if type(start)!=int or type(count)!=int or start<1 or not 1<=count<=160: raise ValueError('Use start >= 1 and count 1..160')
    lines=p.read_text(encoding='utf-8-sig').splitlines()
    selected=lines[start-1:start-1+count]
    out=f'{a["path"]}: lines {start}-{min(start+count-1,len(lines))} of {len(lines)}\n'
    for index,line in enumerate(selected,start):
        row=f'{index}: {line}\n'
        if len(out)+len(row)>12000: return out+'[Output limited; request a smaller range.]'
        out+=row
    if start+count<=len(lines): out+=f'[More lines available; next start={start+count}]'
    return out

class Assets(HTMLParser):
    def __init__(self): super().__init__(); self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('script','img') and a.get('src'): self.refs.append(a['src'])
        if tag=='link' and a.get('rel')=='stylesheet' and a.get('href'): self.refs.append(a['href'])

def verify(root,paths):
    root=Path(root).resolve(); checks=[]; errors=[]; skipped=[]
    for name in sorted(set(paths)):
        try:
            p=safe_path(root,name); digest(p)
            if not p.is_file(): raise ValueError('File missing')
            ext=p.suffix.lower()
            if ext in ('.js','.cjs','.mjs'):
                node=shutil.which('node')
                if not node: raise ValueError('Node is unavailable; JavaScript syntax is unverified')
                result=subprocess.run([node,'--check',str(p)],capture_output=True,text=True,timeout=20)
                if result.returncode: raise ValueError(result.stderr[:1800])
                checks.append(name+': JavaScript syntax passed')
            elif ext=='.py': ast.parse(p.read_text(encoding='utf-8-sig')); checks.append(name+': Python syntax passed')
            elif ext=='.json': json.loads(p.read_text(encoding='utf-8-sig')); checks.append(name+': JSON parsed')
            elif ext in ('.html','.htm'):
                parser=Assets(); parser.feed(p.read_text(encoding='utf-8-sig'))
                for ref in parser.refs:
                    url=urlsplit(ref)
                    if url.scheme or url.netloc or not url.path: continue
                    target=(root/unquote(url.path.lstrip('/')) if url.path.startswith('/') else p.parent/unquote(url.path)).resolve()
                    if not target.is_relative_to(root) or not target.is_file(): raise ValueError('Missing or outside-workspace asset: '+ref)
                checks.append(name+': referenced local assets exist')
            else: checks.append(name+': file exists'); skipped.append(name+': no language/runtime check')
        except Exception as exc: errors.append(name+': '+str(exc))
    return {'passed':not errors,'checks':checks,'errors':errors,'limitations':skipped+['These checks do not prove application behavior or visual correctness.']}

def source_snapshot(root):
    """Bounded metadata scan detects edits through arbitrary shell commands too."""
    root=Path(root).resolve(); result={}; size=0
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if not d.startswith('.') and d not in ('node_modules','vendor','dist','build','__pycache__') and not (Path(directory)/d).is_symlink()]
        for name in files:
            p=Path(directory)/name
            if p.suffix.lower() not in ('.js','.cjs','.mjs','.py','.json','.html','.htm','.css') or p.is_symlink() or name.startswith('.'): continue
            size+=p.stat().st_size
            if len(result)>=1000 or size>32_000_000: raise ValueError('Workspace too large for automatic verification; select a smaller project folder')
            result[str(p.relative_to(root))]=digest(p)
    return result

class DocumentText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','nav','svg'): self.skip+=1
        if not self.skip and tag in ('p','div','h1','h2','h3','pre','br','li'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','nav','svg') and self.skip: self.skip-=1
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def fetch_document(a):
    import urllib.request
    url=a['url']; parsed=urlsplit(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use an HTTP(S) documentation URL without credentials')
    start=a.get('start',0)
    if type(start)!=int or start<0: raise ValueError('start must be a nonnegative character offset')
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request,timeout=20) as response:
        data=response.read(2_000_001)
        if len(data)>2_000_000: raise ValueError('Document exceeds 2 MB limit')
        content=data.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')
        if 'html' in response.headers.get_content_type():
            parser=DocumentText(); parser.feed(content)
            content='\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
        return {'url':response.url,'status':response.status,'start':start,'total_characters':len(content),
                'text':content[start:start+7000],
                'next_start':start+7000 if start+7000<len(content) else None}

def main():
    payload=json.loads(base64.b64decode(sys.argv[1])); root=payload['root']; a=payload['action']
    if a['tool'] in ('write','edit'): print(apply_file(root,a,payload['expected']))
    elif a['tool']=='read': print(read_range(root,a))
    elif a['tool']=='fetch': print(json.dumps(fetch_document(a),ensure_ascii=True))
    elif a['tool']=='verify':
        result=verify(root,a['paths']); print(json.dumps(result)); sys.exit(0 if result['passed'] else 1)
    else: raise ValueError('Unsupported workspace operation')

if __name__=='__main__':
    try: main()
    except Exception as exc: print(str(exc),file=sys.stderr); sys.exit(1)
