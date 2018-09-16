from socket import *
import ssl
import base64
from collections import namedtuple

Auth = namedtuple('Auth', ['email', 'password'])


class SMTPClient:
    CRLF = b'\r\n'
    BOUNDARY = b'my boundary'

    def __init__(self, address: str, port: int):
        self.auth = None
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((address, port))
        self.sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv23)
        if '554' in self.handle_response():
            self.quit()

    def login(self, email: str, password: str):
        self.auth = Auth(email, password)
        self.send_and_receive(b'EHLO ' + email.encode(encoding='ascii'))

        self.send_and_receive(b'AUTH LOGIN')
        self.send_and_receive(base64.b64encode(email.encode(encoding='ascii')))
        self.send_and_receive(base64.b64encode(password.encode(encoding='ascii')))

    def send_and_receive(self, command: bytes, printed: bool = True) -> list:
        if printed:
            print(command)
        self.sock.send(command + self.CRLF)
        return self.handle_response()

    def handle_response(self) -> list:
        response = self.sock.recv(1024).decode()
        print(response)
        codes = [res.split(' ')[0] for res in response.split('\r\n')]
        # print(codes)
        return codes

    def send_message(self, recipients: list, subject: str, letter: str, attachments_names: list):
        self.send_and_receive(b'MAIL FROM:<' + self.auth.email.encode(encoding='ascii') + b'>')
        for recipient in recipients:
            self.send_and_receive(b'RCPT TO:<' + recipient.encode(encoding='ascii') + b'>')

        message = self.create_message(recipients, subject, letter, attachments_names)
        self.send_and_receive(b'DATA')
        self.send_and_receive(message, False)
        self.quit()

    def create_message(self, recipients: list, subject, letter: str, attachments_names: list) -> bytes:
        message = b''
        message += self.get_header(recipients, subject)
        message += self.get_letter_text(letter)
        for attach in attachments_names:
            message += self.get_attachment(attach)
        message += self.get_trailer()
        return message

    def get_header(self, recipients: list, subject: str) -> bytes:
        header = b'from: ' + self.auth.email.encode(encoding='ascii') + self.CRLF
        header += b'to: ' + (', '.join(recipients)).encode(encoding='ascii') + self.CRLF

        header += b'Subject: '
        header += subject.encode(encoding='utf-8') + self.CRLF

        header += b'MIME-Version: 1.0' + self.CRLF
        header += b'Content-Type: multipart/mixed; boundary="' + self.BOUNDARY + b'"' + self.CRLF * 2
        return header

    def get_letter_text(self, letter: str) -> bytes:
        text = b'--' + self.BOUNDARY + self.CRLF
        text += b'Content-Type: text/plain; charset="UTF-8"' + self.CRLF
        text += b'Content-Transfer-Encoding: base64' + self.CRLF * 2
        text += base64.encodebytes(letter.encode(encoding='utf-8'))
        return text

    def get_attachment(self, attach_name) -> bytes:
        attach = b'--' + self.BOUNDARY + self.CRLF
        attach += b'Content-Type: application/octet-stream' + self.CRLF
        attach += b'Content-Disposition: attachment;'
        attach += b'filename=' + attach_name.encode(encoding='utf-8') + self.CRLF
        attach += b'Content-Transfer-Encoding: base64' + self.CRLF * 2
        with open(attach_name, 'rb') as f:
            content = f.read()
        attach += base64.encodebytes(content) + self.CRLF
        return attach

    def get_trailer(self) -> bytes:
        return b'--' + self.BOUNDARY + b'--' + self.CRLF + b'.'

    def quit(self):
        self.send_and_receive(b'QUIT')
