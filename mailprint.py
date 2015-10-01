#!/usr/bin/python3


import sys
import email.parser, email.message
import re
import subprocess
import traceback


ZEPHYR_CLASS = ['-c', 'mailprint']


def send_zephyr(zdest, instance, message):
    p = subprocess.Popen(['zwrite', '-d'] + zdest +
                         ['-i', 'mailprint: ' + instance,
                          '-S', 'mailprint',
                          '-s', 'printprintprintprintprint'],
                         stdin=subprocess.PIPE, universal_newlines=True)
    p.stdin.write(message)
    p.stdin.close()


def zephyr_error(e):
    send_zephyr(ZEPHYR_CLASS, 'error', traceback.format_exc(e))


class MailprintError(Exception):
    def __init__(self, msg, zdest=ZEPHYR_CLASS):
        self.message = msg
        self.zephyr_destination = zdest

    def send_zephyr(self):
        send_zephyr(self.zephyr_destination, 'error', self.message)


def spool_file(name, content, username, doublesided=False):
    p = subprocess.Popen(['lpr',
                          '-P', 'mitprint',
                          '-C', name,
                          '-U', username] +
                         (['-o', 'sides=two-sided-long-edge']
                          if doublesided
                          else ['-o', 'sides=one-sided']),
                         stdin=subprocess.PIPE)
    p.stdin.write(content)
    p.stdin.close()


def main():
    username = None
    try:
        # EmailMessage doesn't exist before 3.4
        # parser = email.parser.Parser(_class=email.message.EmailMessage)
        parser = email.parser.Parser()
        msg = parser.parse(sys.stdin)
        match = re.search(r'\b([a-zA-Z]+)@mit\.edu\b', msg.get_unixfrom())
        if not match:
            raise MailprintError('could not identify sender: ' +
                                 msg.get_unixfrom())
        username = match.group(1)
        spooled_file = False
        for part in msg.walk():
            if not part.get_filename():
                continue
            spool_file(part.get_filename(), part.get_payload(decode=True),
                       username)
            send_zephyr([username], 'info',
                        'Spooled file: ' + part.get_filename())
            spooled_file = True
        if not spooled_file:
            subject = msg.get('Subject')
            send_zephyr([username], 'info',
                        'Your print request with subject:\n' + subject +
                        '\nwas received, but had no attachments.')
    except MailprintError as e:
        e.send_zephyr()
        raise
    except Exception as e:
        zephyr_error(e)
        raise

if __name__ == '__main__':
    main()
