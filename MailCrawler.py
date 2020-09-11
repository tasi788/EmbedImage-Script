import logging
import logging.handlers
import smtplib
import sys
from configparser import ConfigParser
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import coloredlogs

# loads config.
config = ConfigParser()
config.read('./config.ini')

logger = logging.getLogger(__name__)
handler1 = logging.StreamHandler(sys.stdout)
handler2 = logging.handlers.TimedRotatingFileHandler(
    filename=config.get('logging', 'log_file_path'),
    when='D',
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logging_level = config.get('logging', 'logging_level')
logger.setLevel(logging_level)
handler1.setLevel(logging_level)
handler2.setLevel(logging_level)

logger.addHandler(handler1)
logger.addHandler(handler2)

coloredlogs.install(level=logging_level, logger=logger)

class MailCrawler:
    def __init__(self):
        self._loads_html()
        self._loads_smtp()
    
    def _loads_html(self):
        # load html template
        html = '''<html>
                <body>
                    <p>下面是 inline image</p>
                    <img src="cid:1">
                    <p>隨便寫寫</p>
                    <img src="cid:2">
                    <p>最後一張</p>
                    <img src="cid:3">
                    <p>沒了</p>
                </body>
                </html>
                '''
        self.mail = MIMEMultipart('related')
        self.mail.attach(MIMEText(html, 'html', 'utf-8'))
        logger.info("email content gen.")
    
    def _loads_smtp(self):
        # smtp services
        self.smtp = smtplib.SMTP_SSL('smtp.gmail.com')
        try:
            self.smtp.login(config.get('mail','login'), config.get('mail','application_secret'))
        except Exception as e:
            logger.exception(e)
            raise Exception('登入 SMTP 服務發生錯誤')
        logger.info("SMTP 已登入.")
    
    def embed(self):
        # load pics from attachment
        piclist = list(Path('./attachment').glob('*.png'))
        if len(piclist) == 0:
            logger.critical('找不到圖片。')
            return

        counter = 1
        for pic in piclist:
            image_extension = pic.parts[-1]
            attach = MIMEBase('image', image_extension)
            attach.add_header(
                'Content-ID', '<{count}>'.format(count=counter))
            attach.set_payload(pic.read_bytes())
            encoders.encode_base64(attach)
            self.mail.attach(attach)
            counter += 1
        logging.info('已載入 {n}張 圖片'.format(n=len(piclist)))


    def send(self, send_to: str,from_email: Optional[str]=None, subject: str='Notitle'):
        if not from_email:
            from_email = config.get('mail', 'login')
        
        try:
            self.embed()
        except Exception as e:
            logger.critical('發送錯誤')
            logger.exception(e)

        self.mail.__dict__.update({'Subject': Header(subject, 'utf-8').encode()})
        status = self.smtp.sendmail(from_email, send_to, self.mail.as_string())
        if status:
            logger.error('{send_to} 郵件傳送失敗！'.format(send_to=send_to))
            logger.error(status)
        else:
            logger.info('{send_to} 郵件傳送成功！'.format(send_to=send_to))

        self.smtp.quit()
