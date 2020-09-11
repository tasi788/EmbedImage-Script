from MailCrawler import MailCrawler

if __name__ == '__main__':
    # init module
    client = MailCrawler()
    
    # do something
    client.send(send_to='mail')