"""Upload static assets with verified SSH and preserve replaced files outside web root."""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen, Request
import os, re, shlex, subprocess, tempfile, time, hashlib
from validate import validate, ROOT, DEMO_PAGES, MARKETING_PAGES

def settings(env):
    required=['HOSTINGER_HOST','HOSTINGER_USER','HOSTINGER_PORT','HOSTINGER_SSH_KEY','HOSTINGER_KNOWN_HOSTS','HOSTINGER_TARGET_DIR','DEMO_BASE_URL']
    missing=[k for k in required if not env.get(k,'').strip()]
    if missing: raise ValueError('Missing settings: '+', '.join(missing))
    c={k:env[k].strip() for k in required}
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',c['HOSTINGER_HOST']): raise ValueError('Invalid host')
    if not re.fullmatch(r'[a-zA-Z0-9_]+',c['HOSTINGER_USER']): raise ValueError('Invalid SSH user')
    if not c['HOSTINGER_PORT'].isdigit() or not 1<=int(c['HOSTINGER_PORT'])<=65535: raise ValueError('Invalid SSH port')
    target=c['HOSTINGER_TARGET_DIR'].rstrip('/')
    if not re.fullmatch(r'/home/[a-zA-Z0-9_]+/domains/[A-Za-z0-9.-]+/public_html(?:/[A-Za-z0-9_-]+)*',target):
        raise ValueError('Target must be an explicit Hostinger /home/USER/domains/DOMAIN/public_html path (optionally /demos)')
    if target.split('/')[2]!=c['HOSTINGER_USER']: raise ValueError('Target account does not match SSH user')
    c['HOSTINGER_TARGET_DIR']=target
    u=urlsplit(c['DEMO_BASE_URL'])
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('DEMO_BASE_URL must be an HTTPS URL without credentials, query or fragment')
    c['DEMO_BASE_URL']=c['DEMO_BASE_URL'].rstrip('/')+'/'
    profile=env.get('DEPLOY_SITE','demos')
    if profile not in {'demos','marketing'}: raise ValueError('Unknown deployment site')
    c['DEPLOY_SITE']=profile
    if profile=='marketing':
        expected='/home/'+c['HOSTINGER_USER']+'/domains/bleenky.com/public_html/demos'
        if target!=expected: raise ValueError('Marketing deployment requires the exact Bleenky demo destination')
        c['HOSTINGER_TARGET_DIR']=target.removesuffix('/demos')
        c['DEMO_BASE_URL']='https://bleenky.com/'
    return c

def main():
    c=settings(os.environ);dry=os.environ.get('DRY_RUN','true')=='true'
    marketing=c['DEPLOY_SITE']=='marketing'
    root=ROOT.parent/'marketing' if marketing else ROOT
    pages=MARKETING_PAGES if marketing else DEMO_PAGES
    validate(root, marketing)
    target=c['HOSTINGER_TARGET_DIR'];remote=c['HOSTINGER_USER']+'@'+c['HOSTINGER_HOST']
    run=os.environ.get('GITHUB_RUN_ID',str(int(time.time())))
    attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1')
    if not re.fullmatch(r'\d+',run) or not re.fullmatch(r'\d+',attempt): raise ValueError('Invalid run identifier')
    destination_id=hashlib.sha256(target.encode()).hexdigest()[:12]
    backup='/home/'+c['HOSTINGER_USER']+'/.bleenky-deploy-backups/'+destination_id+'/'+run+'-'+attempt
    with tempfile.TemporaryDirectory(prefix='bleenky-ssh-') as temp:
        folder=Path(temp);key=folder/'key';hosts=folder/'known_hosts'
        key.write_text(c['HOSTINGER_SSH_KEY']+'\n');key.chmod(0o600)
        hosts.write_text(c['HOSTINGER_KNOWN_HOSTS']+'\n');hosts.chmod(0o600)
        ssh=['ssh','-i',str(key),'-p',c['HOSTINGER_PORT'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),'-o','ConnectTimeout=20']
        # Require an existing destination; a typo must not silently create another site.
        subprocess.run(ssh+[remote,'test -d '+shlex.quote(target)],check=True)
        args=['rsync','-rzp','--checksum','--itemize-changes','--delay-updates','--chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r','--backup','--backup-dir='+backup]
        if marketing: args+=['--exclude=/demos/']
        if dry: args.append('--dry-run')
        # Deliberately no --delete: unrelated files in the hosting directory are preserved.
        args+=['-e',shlex.join(ssh),str(root)+'/',remote+':'+target+'/']
        subprocess.run(args,check=True)
    if dry:
        print('Dry run complete. No website files changed.');return
    # Verify exact deployed HTML, not just a 200 response from an unrelated page.
    for page in pages:
        route=page.removesuffix('index.html')
        expected=(root/page).read_bytes();verified=False
        for n in range(3):
            request=Request(c['DEMO_BASE_URL']+route+'?bleenky_deploy='+run,headers={'Cache-Control':'no-cache'})
            try:
                with urlopen(request,timeout=25) as response: actual=response.read()
                if actual==expected: verified=True;break
            except Exception: pass
            if n<2: time.sleep(5)
        if not verified: raise RuntimeError('Upload finished but live HTML verification failed for '+route+'; check DNS, SSL, path and caching. No automatic rollback performed.')
    print('Deployment and four live HTML checks passed. Replaced files backed up outside the web root.')
if __name__=='__main__': main()
