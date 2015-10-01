#!/usr/bin/python3


import sys
import email.parser, email.message
import re
import subprocess
import traceback
import os


ZEPHYR_CLASS = ['-c', 'mailprint']


def send_zephyr(zdest, instance, message):
    p = subprocess.Popen(['zwrite', '-d'] + zdest +
                         ['-i', 'mailprint: ' + instance,
                          '-S', 'mailprint',
                          '-s', 'printprintprintprintprint'],
                         stdin=subprocess.PIPE, universal_newlines=True)
    p.stdin.write(message)
    p.stdin.close()


def zephyr_error():
    send_zephyr(ZEPHYR_CLASS, 'error', ''.join(traceback.format_exc()))


class MailprintError(Exception):
    def __init__(self, msg, zdest=ZEPHYR_CLASS):
        self.message = msg
        self.zephyr_destination = zdest

    def send_zephyr(self):
        send_zephyr(self.zephyr_destination, 'error', self.message)


def spool_file(name, content, username, pdf):
    if pdf:
        conv = subprocess.Popen(['pdf2ps', '-', '-'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

    mailprint_dir = os.getenv('MAILPRINT_DIR', '.')
    p = subprocess.Popen([mailprint_dir + '/rlpr', '--no-bind',
                          '-P', 'bw@mitprint.mit.edu',  # TODO color print
                          '-C', name,
                          '-J', name,
                          '-T', name,
                          '-U', username],
                         stdin=(conv.stdout if pdf else subprocess.PIPE))

    pipe = (conv if pdf else p).stdin
    pipe.write(content)
    pipe.close()


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
            pdf = part.get_content_type() == 'application/pdf'
            spool_file(part.get_filename(), part.get_payload(decode=True),
                       username, pdf)
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
    except Exception:
        zephyr_error()
        raise

if __name__ == '__main__':
    main()
