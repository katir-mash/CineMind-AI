import hashlib, hmac, os, re, secrets, time
from database import connect

EMAIL=re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
def valid_email(email):return bool(EMAIL.fullmatch(email.strip()))
def digest(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),240000).hex()
def hash_password(password):
    salt=os.urandom(16).hex();return digest(password,salt),salt

def register(name,email,password,confirm):
    email=email.strip().lower();name=name.strip()
    if not name or not valid_email(email):raise ValueError('Укажите имя и корректную почту.')
    if len(password)<8:raise ValueError('Пароль должен содержать минимум 8 символов.')
    if password!=confirm:raise ValueError('Пароли не совпадают.')
    pw,salt=hash_password(password)
    with connect() as c:
        try:
            cur=c.execute('INSERT INTO users(name,email,pw_hash,salt) VALUES(?,?,?,?)',(name,email,pw,salt))
        except __import__('sqlite3').IntegrityError:raise ValueError('Эта почта уже зарегистрирована.')
    return cur.lastrowid

def login(email,password):
    with connect() as c:user=c.execute('SELECT * FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
    if not user or not hmac.compare_digest(digest(password,user['salt']),user['pw_hash']):
        raise ValueError('Неправильная почта или пароль.')
    return dict(user)

def change_password(uid,old,new):
    with connect() as c:u=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    if not u or not hmac.compare_digest(digest(old,u['salt']),u['pw_hash']):raise ValueError('Старый пароль неверный.')
    if len(new)<8:raise ValueError('Новый пароль слишком короткий.')
    h,s=hash_password(new)
    with connect() as c:c.execute('UPDATE users SET pw_hash=?,salt=? WHERE id=?',(h,s,uid))

def generate_reset(email):
    with connect() as c:u=c.execute('SELECT id FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
    if not u:raise ValueError('Такой пользователь не найден.')
    code=f'{secrets.randbelow(1000000):06d}'
    hashed=hashlib.sha256(code.encode()).hexdigest()
    with connect() as c:c.execute('INSERT OR REPLACE INTO reset_codes VALUES(?,?,?)',(u['id'],hashed,time.time()+600))
    return code

def reset_password(email,code,new):
    if len(new)<8:raise ValueError('Пароль должен содержать минимум 8 символов.')
    with connect() as c:
        r=c.execute('''SELECT u.id, r.token_hash, r.expires_at FROM users u JOIN reset_codes r ON r.user_id=u.id WHERE u.email=?''',(email.strip().lower(),)).fetchone()
        if not r or time.time()>r['expires_at'] or not hmac.compare_digest(r['token_hash'],hashlib.sha256(code.strip().encode()).hexdigest()):raise ValueError('Неверный или просроченный код.')
        h,s=hash_password(new)
        c.execute('UPDATE users SET pw_hash=?,salt=? WHERE id=?',(h,s,r['id']))
        c.execute('DELETE FROM reset_codes WHERE user_id=?',(r['id'],))
