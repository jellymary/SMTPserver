from smtp_client import SMTPClient

FOLDER_PATH = 'conf'


def read_file(name: str) -> str:
    with open(name, 'r', encoding='utf-8') as f:
        return f.read()


def read_conf_file(name: str):
    conf = read_file(name).split('\n')
    receivers = conf[0].split(', ')
    subject = conf[1]
    attachments = [FOLDER_PATH + '/' + name for name in conf[2].split(', ')]
    return receivers, subject, attachments


def main():
    receivers, subject, attachs = read_conf_file(FOLDER_PATH + '/config.txt')
    letter = read_file(FOLDER_PATH + '/letter.txt')

    client = SMTPClient('smtp.yandex.ru', 465)
    client.login('honey.mara@yandex.ru', 'h1o2n3e4y')
    client.send_message(receivers, subject, letter, attachs)


if __name__ == '__main__':
    main()
