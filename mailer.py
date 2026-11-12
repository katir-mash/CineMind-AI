"""SMTP через переменные окружения; никакие секреты не вшиваются в код."""
import os, smtplib
from email.message import EmailMessage

def send(to,subject,body):
    host=os.getenv('CINEMIND_SMTP_HOST','')
    username=os.getenv('CINEMIND_SMTP_USER','')
    password=os.getenv('CINEMIND_SMTP_PASSWORD','')
    port=int(os.getenv('CINEMIND_SMTP_PORT','587'))
    if not (host and username and password):raise RuntimeError('SMTP не настроен. Установите CINEMIND_SMTP_HOST, CINEMIND_SMTP_USER, CINEMIND_SMTP_PASSWORD.')
    msg=EmailMessage();msg['From']=username;msg['To']=to;msg['Subject']=subject;msg.set_content(body)
    with smtplib.SMTP(host,port,timeout=15) as server:
        server.starttls();server.login(username,password);server.send_message(msg)
