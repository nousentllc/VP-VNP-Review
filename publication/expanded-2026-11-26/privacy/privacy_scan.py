#!/usr/bin/env python3
"""Value-suppressing Git-history and recursive container privacy inventory."""
import collections
import gzip
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib
import numpy as np

def main():
    repo, out = map(pathlib.Path, sys.argv[1:3])
    out.mkdir(parents=True, exist_ok=True)
    def git(*args):
        return subprocess.check_output(['git','-C',str(repo),*args])
    refs = git('show-ref').decode().splitlines()
    objects = git('rev-list','--objects','--all').decode().splitlines()
    paths = dict((line.split(' ',1)+[''])[:2] for line in objects)
    batch = subprocess.Popen(['git','-C',str(repo),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    counts = collections.Counter()
    findings, limits, inventory = [], [], []
    seen = set()
    patterns = {
        'credential_prefix': re.compile(r'(?i)(?:sk-(?:proj-|ant-api\d+-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{15,}|AIza[A-Za-z0-9_-]{30,})'),
        'additional_credential': re.compile(r'(?:ASIA[A-Z0-9]{16}|sk_live_[A-Za-z0-9]{16,}|rk_live_[A-Za-z0-9]{16,}|hf_[A-Za-z0-9]{20,}|npm_[A-Za-z0-9]{20,}|pypi-[A-Za-z0-9_-]{30,}|eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,})'),
        'us_ssn_candidate': re.compile(r'(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])'),
        'us_phone_candidate': re.compile(r'(?<![\d])(?:\+1[ .-]?)?\([2-9]\d{2}\)[ .-]?\d{3}[ .-]\d{4}(?!\d)'),
        'private_key_header': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
        'assigned_secret': re.compile(r'''(?im)(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd)\s*[=:]\s*["']?([^\s"'`,;}{]{8,})'''),
        'authorization_value': re.compile(r'(?i)(?:Authorization\s*[:=]\s*["\x27]?Bearer\s+|https?://[^\s/:]+:)([^\s"\x27/]{12,})'),
        'email_candidate': re.compile(r'(?<![\w@])[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w])'),
        'home_path': re.compile(r'(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^\s/\\"\x27:]+'),
        'private_network': re.compile(r'(?<![\d.])(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\d.])'),
        'personal_field': re.compile(r'(?im)(?:date.of.birth|social.security|ssn|home.address|phone.number)\s*[=:]'),
    }
    def scan_text(text, loc, digest, layer):
        counts['text_units'] += 1
        for category, pattern in patterns.items():
            for match in pattern.finditer(text):
                value = match.group(0)
                classification = 'candidate'
                if category == 'email_candidate':
                    if value.startswith('@') or ('lean' in loc.lower() and (value.startswith('@') or 'leanprover' not in value)):
                        classification = 'review_lean_syntax'
                    if 'noreply.github.com' in value:
                        classification = 'platform_noreply'
                if category == 'home_path':
                    classification = 'system_path' if value in ['/home/runner','/home/lean','/home/user','/home/proof','/Users/runner'] else 'local_account_path'
                if category == 'assigned_secret':
                    val = match.group(1)
                    if any(s in val.lower() for s in ['environ','getenv','secrets.','api_key','your_','example','redacted','placeholder','$','none','<']):
                        classification = 'reference_or_placeholder'
                findings.append(dict(category=category,classification=classification,location=loc,line=text.count('\n',0,match.start())+1,content_sha256=digest,match_sha256=hashlib.sha256(value.encode()).hexdigest(),layer=layer))
    def scan(data, loc, depth=0):
        digest = hashlib.sha256(data).hexdigest()
        counts['encountered_units'] += 1
        if digest in seen:
            counts['duplicate_content_units'] += 1
            return
        seen.add(digest)
        counts['unique_bytes'] += len(data)
        inventory.append(dict(location=loc,sha256=digest,bytes=len(data),depth=depth))
        if depth > 12:
            limits.append(dict(location=loc,reason='recursion_depth',sha256=digest)); return
        if len(data)>8 and data[4:8]==b'jumb':
            counts['jumbf_manifests']+=1
            def boxes(raw, label):
                pos=0
                while pos+8<=len(raw):
                    size=int.from_bytes(raw[pos:pos+4],'big'); typ=raw[pos+4:pos+8]; head=8
                    if size==1:
                        size=int.from_bytes(raw[pos+8:pos+16],'big');head=16
                    if size==0:size=len(raw)-pos
                    if size<head or pos+size>len(raw):
                        limits.append(dict(location=label,reason='invalid_jumbf_box'));return
                    payload=raw[pos+head:pos+size]
                    name=label+'!'+typ.decode('ascii',errors='replace')
                    if typ==b'jumb':boxes(payload,name)
                    else:
                        scan_text('\n'.join(x.decode('ascii') for x in re.findall(rb'[\x20-\x7e]{4,}',payload)),name,digest,'jumbf_strings')
                        if typ==b'cbor':
                            counts['cbor_boxes']+=1
                            # Decode every CBOR text string, including non-ASCII text;
                            # byte strings retain a separate string-screening boundary.
                            def item(buf,p):
                                b=buf[p];p+=1;major=b>>5;ai=b&31
                                if ai<24:n=ai
                                elif ai in (24,25,26,27):
                                    k=1<<(ai-24);n=int.from_bytes(buf[p:p+k],'big');p+=k
                                elif ai==31:
                                    while buf[p]!=255:p=item(buf,p)
                                    return p+1
                                else:raise ValueError('reserved CBOR additional info')
                                if major in (2,3):
                                    val=buf[p:p+n]
                                    if len(val)!=n:raise ValueError('short CBOR string')
                                    if major==3:scan_text(val.decode('utf8'),name,digest,'cbor_text')
                                    else:scan_text('\n'.join(x.decode('ascii') for x in re.findall(rb'[\x20-\x7e]{4,}',val)),name,digest,'cbor_bytes_strings')
                                    return p+n
                                if major in (4,5):
                                    for _ in range(n*(2 if major==5 else 1)):p=item(buf,p)
                                elif major==6:p=item(buf,p)
                                return p
                            try:
                                p=0
                                while p<len(payload):p=item(payload,p)
                            except Exception as e:limits.append(dict(location=name,reason='cbor_'+type(e).__name__))
                    pos+=size
                if pos!=len(raw):limits.append(dict(location=label,reason='trailing_jumbf_bytes'))
            boxes(data,loc)
        elif data.startswith(b'PK\x03\x04'):
            counts['zip_containers'] += 1
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for member in z.infolist():
                        if member.is_dir(): continue
                        if member.file_size > 200_000_000:
                            limits.append(dict(location=loc+'!'+member.filename,reason='member_over_200MB')); continue
                        scan(z.read(member),loc+'!'+member.filename,depth+1)
            except Exception as e: limits.append(dict(location=loc,reason=type(e).__name__,sha256=digest))
        elif data[:2] == b'\x1f\x8b':
            counts['gzip_containers'] += 1
            try: scan(gzip.decompress(data),loc+'!gunzip',depth+1)
            except Exception as e:
                partial=zlib.decompressobj(31).decompress(data)
                if partial: scan(partial,loc+'!partial_gunzip',depth+1)
                limits.append(dict(location=loc,reason=type(e).__name__+'_partial_recovery',sha256=digest))
        elif len(data)>262 and data[257:262]==b'ustar':
            counts['tar_containers'] += 1
            try:
                with tarfile.open(fileobj=io.BytesIO(data)) as t:
                    for m in t:
                        if m.isfile(): scan(t.extractfile(m).read(),loc+'!'+m.name,depth+1)
            except Exception as e: limits.append(dict(location=loc,reason=type(e).__name__,sha256=digest))
        elif data.startswith(b'%PDF'):
            counts['pdfs'] += 1
            with tempfile.TemporaryDirectory() as td:
                p=pathlib.Path(td)/'document.pdf'; p.write_bytes(data)
                for cmd, layer in [(['pdftotext','-layout',str(p),'-'],'pdf_text'),(['pdfinfo','-meta',str(p)],'pdf_xmp'),(['pdfinfo',str(p)],'pdf_metadata'),(['pdfdetach','-list',str(p)],'pdf_attachments')]:
                    run=subprocess.run(cmd,capture_output=True)
                    if run.returncode: limits.append(dict(location=loc,reason=layer+'_failed',sha256=digest))
                    else:
                        scan_text(run.stdout.decode(errors='replace'),loc,digest,layer)
                        if layer=='pdf_attachments' and not run.stdout.startswith(b'0 embedded'):
                            match=re.match(rb'(\d+) embedded',run.stdout)
                            if match:
                                for i in range(1,int(match.group(1))+1):
                                    dst=pathlib.Path(td)/('attachment-'+str(i))
                                    extracted=subprocess.run(['pdfdetach','-save',str(i),'-o',str(dst),str(p)],capture_output=True)
                                    if extracted.returncode==0 and dst.exists():
                                        counts['pdf_attachment_files']+=1
                                        scan(dst.read_bytes(),loc+'!pdf_attachment_'+str(i),depth+1)
                                    else: limits.append(dict(location=loc,reason='attachment_extraction_failed',sha256=digest))
        elif data.startswith(b'\x93NUMPY'):
            counts['numpy_arrays']+=1
            try:
                arr=np.load(io.BytesIO(data),allow_pickle=False)
                if arr.dtype.kind in 'US': scan_text('\n'.join(map(str,arr.ravel())),loc,digest,'numpy_strings')
                elif arr.dtype.kind in 'biufc': counts['numeric_arrays']+=1
                else: limits.append(dict(location=loc,reason='numpy_nonprimitive_dtype',sha256=digest))
            except Exception as e: limits.append(dict(location=loc,reason='numpy_'+type(e).__name__,sha256=digest))
        elif data.startswith((b'\x89PNG',b'\xff\xd8\xff',b'GIF8')):
            counts['images_ocr']+=1
            with tempfile.TemporaryDirectory() as td:
                p=pathlib.Path(td)/'image'; p.write_bytes(data)
                run=subprocess.run(['tesseract',str(p),'stdout'],capture_output=True)
                scan_text(run.stdout.decode(errors='replace'),loc,digest,'image_ocr')
                if run.returncode: limits.append(dict(location=loc,reason='image_ocr_failed',sha256=digest))
        elif b'\x00' not in data[:8192]:
            try: scan_text(data.decode('utf-8'),loc,digest,'text')
            except UnicodeDecodeError: scan_text(data.decode('latin-1'),loc,digest,'non_utf8_text')
        else:
            counts['opaque_binary'] += 1
            scan_text('\n'.join(x.decode('ascii') for x in re.findall(rb'[\x20-\x7e]{8,}',data)),loc,digest,'binary_strings')
            limits.append(dict(location=loc,reason='binary_strings_only_no_visual_OCR',sha256=digest))
    for sha, path in paths.items():
        batch.stdin.write((sha+'\n').encode()); batch.stdin.flush()
        header=batch.stdout.readline().decode().split()
        if len(header)!=3: limits.append(dict(location=sha,reason='missing_git_object')); continue
        typ,size=header[1],int(header[2]); data=batch.stdout.read(size); batch.stdout.read(1)
        counts['git_'+typ] += 1
        if typ in ('blob','commit','tag'): scan(data,(path or typ)+'@'+sha)
    batch.stdin.close(); batch.wait()
    for payload in map(pathlib.Path,sys.argv[3:]):
        for p in sorted(payload.rglob('*')):
            if p.is_file() and not any(x in ('build','.git','__pycache__','privacy') for x in p.relative_to(payload).parts):
                scan(p.read_bytes(),'release-payload/'+str(p.relative_to(payload)))
    summary=dict(refs=refs,counts=dict(counts),findings_by_category=dict(collections.Counter(x['category'] for x in findings)),limits_count=len(limits),limitations=['Pattern screening cannot establish absence of unknown credentials or identifiers.','Deduplicated content is scanned once; inventory retains first occurrence. Git objects remain in the original bundle.','Images receive OCR; binary signature/certificate data receives string screening. Numeric arrays are classified by dtype without treating measured numbers as identifiers. No credential validity tests are performed.','Git reachable refs only; deleted unreachable objects, GitHub caches, forks, external logs and account settings are not covered.'])
    for name,obj in [('scan-summary.json',summary),('findings.json',findings),('limits.json',limits),('inventory.json',inventory)]:
        (out/name).write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
