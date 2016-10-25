#!/usr/bin/python3


# Copyright 2015 Istvan Chung

# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import email.parser, email.message
import re
import subprocess
import traceback
import os
import random
import datetime


ZEPHYR_CLASS = ['-c', 'mailprint']
TYPE_WHITELIST = ['application/pdf', 'application/postscript']


def send_zephyr(zdest, instance, message):
    p = subprocess.Popen(['zwrite', '-d'] + zdest +
                         ['-i', 'mailprint: ' + instance,
                          '-S', 'mailprint',
                          '-s', 'print' * random.randint(1, 5) + '!'],
                         stdin=subprocess.PIPE, universal_newlines=True)
    p.stdin.write(message)
    p.stdin.close()


def zephyr_error():
    send_zephyr(ZEPHYR_CLASS,
                'error',
                ''.join(traceback.format_exc()))

class MailprintError(Exception):
    def __init__(self, msg, zdest=ZEPHYR_CLASS):
        self.message = msg
        self.zephyr_destination = zdest

    def send_zephyr(self):
        send_zephyr(self.zephyr_destination, 'error', self.message)


def spool_file(name, content, username, pdf, color=False):
    if pdf:
        # rlpr can't print pdf directly
        conv = subprocess.Popen(['pdf2ps', '-', '-'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

    mailprint_dir = os.getenv('MAILPRINT_DIR', '.')
    # printers aren't configured on the scripts servers, so use rlpr to
    # print over the network
    p = subprocess.Popen([mailprint_dir + '/rlpr', '--no-bind',
                          '-P',
                          ('color' if color else 'bw') + '@mitprint.mit.edu',
                          '-C', name,
                          '-J', name,
                          '-T', name,
                          '-U', username],
                         stdin=(conv.stdout if pdf else subprocess.PIPE))

    pipe = (conv if pdf else p).stdin
    pipe.write(content)
    pipe.close()


def search_mit_user(s):
    if s:
        match = re.search(r'\b([a-zA-Z]+)@mit\.edu\b', s)
        if match:
            return match.group(1)
    return None


def get_username(msg):
    u = search_mit_user(msg.get_unixfrom())
    if u:
        return u
    u = search_mit_user(msg.get('Sender'))
    if u:
        return u
    u = search_mit_user(msg.get('From'))
    if u:
        return u

    return None


def main():
    username = None
    try:
        # EmailMessage doesn't exist before 3.4
        # parser = email.parser.Parser(_class=email.message.EmailMessage)
        parser = email.parser.Parser()
        msg = parser.parse(sys.stdin)
        username = get_username(msg)
        if not username:
            raise MailprintError(
                'could not identify sender: {} | {} | {}'.format(
                    msg.get_unixfrom(), msg.get('Sender'), msg.get('From')))
        print('[{}] incoming message from {}'.format(
                datetime.datetime.now(), username), file=sys.stderr)
        subject = msg.get('Subject')
        if not subject:
            subject = ''
        spooled_file = False
        for part in msg.walk():
            name = part.get_filename()
            if not name:
                continue
            mimetype = part.get_content_type()
            if (mimetype not in TYPE_WHITELIST and
                part.get_content_maintype() != 'text'):
                send_zephyr([username], 'error',
                            'file ' + part.get_filename() +
                            ' has illegal type ' + mimetype +
                            '\nplease send a text file, ' +
                            'or a file with type:\n' +
                            '\n'.join(TYPE_WHITELIST))
                continue
            pdf = mimetype == 'application/pdf'
            spool_file(name, part.get_payload(decode=True), username, pdf,
                       'color' in subject)
            send_zephyr([username], 'info', 'Spooled file: ' + name)
            spooled_file = True
        if not spooled_file:
            send_zephyr([username], 'error',
                        'Your print request with subject:\n' + subject +
                        '\nwas received, but had no printable attachments.')
    except MailprintError as e:
        e.send_zephyr()
        raise
    except Exception:
        zephyr_error()
        raise

if __name__ == '__main__':
    main()
