import requests, re, time

def get_mail_list(username, domain):
    url = 'https://tempmail.plus/api/mails?email=%s@%s&epin=&limit=5' % (username, domain)
    resp = requests.get(url, timeout=10)
    data = resp.json()
    if data.get('result'):
        return data.get('mail_list', [])
    return []

def get_mail_detail(mail_id, username, domain):
    url = 'https://tempmail.plus/api/mails/%s?email=%s@%s&epin=' % (mail_id, username, domain)
    resp = requests.get(url, timeout=10)
    data = resp.json()
    if data.get('result'):
        return data
    return None

def extract_code(mail_data):
    text = mail_data.get('text', '') or ''
    html = mail_data.get('html', '') or ''
    body = text + html
    # Look for the specific pattern: 您的验证码是: XXXXXX or 验证码: XXXXXX
    patterns = [
        r'验证码[是:：\s]*(\d{6})',
        r'code[:\s]*(\d{6})',
        r'verification[:\s]*(\d{6})',
        r'token[:\s]*(\d{6})',
    ]
    for pat in patterns:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            return m.group(1)
    # Fallback: find any 6-digit code near '验证' or 'verif' or 'code'
    codes = re.findall(r'(\d{6})', body)
    for code in codes:
        if code in ('000000', '010201'):
            continue
        idx = body.find(code)
        if idx >= 0:
            context = body[max(0,idx-30):idx+36]
            if '验证' in context or 'verif' in context.lower() or 'code:' in context.lower():
                return code
    return None

def wait_for_code(email, timeout=120, check_interval=3):
    username, domain = email.split('@')
    known_ids = set()
    
    start = time.time()
    while time.time() - start < timeout:
        mail_list = get_mail_list(username, domain)
        
        for mail in mail_list:
            mid = mail.get('mail_id')
            if mid in known_ids:
                continue
            known_ids.add(mid)
            
            subject = mail.get('subject', '')
            sender = mail.get('from_mail', '')
            
            if 'osaio' in sender.lower() or '验证' in subject or 'code' in subject.lower():
                detail = get_mail_detail(mid, username, domain)
                if detail:
                    code = extract_code(detail)
                    if code:
                        return code, mid
        
        time.sleep(check_interval)
    
    return None, None

if __name__ == '__main__':
    import sys
    code, mid = wait_for_code(sys.argv[1] if len(sys.argv) > 1 else 'testb01@mailto.plus', timeout=30)
    if code:
        print('CODE:%s' % code)
    else:
        print('CODE:None')
