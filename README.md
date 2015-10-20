# Mailprint

A mail daemon which spools print jobs received over email

## Installation

On Athena, copy the `procmailrc` file into the `~/mail_scripts/` folder
of a locker you control which has mail scripts enabled, modifying it as
appropriate.  Make sure the `MAILPRINT_DIR` variable is set to the
installation location of mailprint.  The "daemon.scripts" user must also
have access to the installation location.  In addition, copy the `rlpr`
binary into the installation location (or modify `mailprint.py` to call
it in the appropriate way).

## Copying

Mailprint Copyright 2015 Istvan Chung

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
