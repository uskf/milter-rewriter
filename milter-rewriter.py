#!/usr/bin/python3
import sys
import os
import re
import Milter
from Milter.utils import *

class MilterRewriter(Milter.Base):
    "Milter for Mail Rewrite"

    def __init__(self):
        self.mailfrom = None
        self.envfromaddr = None
        self.fromheader = None
        self.messageid = None
        self.pid = os.getpid()
        self.queueid = None
        self.rewrite = None



    @Milter.noreply
    def envfrom(self, f, *str):
        self.mailfrom = f
        (_displayname, self.envfromaddr) = parseaddr(f)
        if re.fullmatch("foo@example\.org",self.envfromaddr):
            self.rewrite = True
        return Milter.CONTINUE



    @Milter.noreply
    def header(self, field, value):
        if re.fullmatch("From", field):
            self.fromheader = value
        return Milter.CONTINUE



    def eom(self):
        if self.rewrite:
            self.addheader("Cc", self.fromheader, 0)
            self.chgheader("From", 0, "admin@example.org")
        return Milter.ACCEPT

def main():
    if not os.path.exists('/var/spool/postfix/milter-rewriter'):
        os.mkdir('/var/spool/postfix/milter-rewriter', mode=0o777)

    f = open('/run/milter-rewriter/milter-rewriter.pid', mode='w')
    print(os.getpid(), file=f)
    f.close()

    Milter.factory = MilterRewriter
    Milter.runmilter('MRewriter', '/var/spool/postfix/milter-rewriter/milter-rewriter.sock', 240)

    # shutdown
    os.remove('/run/milter-rewriter/milter-rewriter.pid')

if __name__ == '__main__':
    main()

