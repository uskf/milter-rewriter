#!/usr/bin/python3
import sys
import os
import re
import Milter
from Milter.utils import *
from yaml import safe_load


class MilterRewriter(Milter.Base):
    "Milter for Mail Rewrite"

    def __init__(self):
        self.mailfrom = None
        self.envfromaddr = None
        self.fromheader = None
        self.messageid = None
        self.pid = os.getpid()
        self.status = []
        self.__reset_status()


    @Milter.noreply
    def envfrom(self, f, *str):
        self.mailfrom = f
        (_displayname, self.envfromaddr) = parseaddr(f)
        self.__header_search("EnvFrom", f)
        return Milter.CONTINUE


    @Milter.noreply
    def header(self, field, value):
        self.__header_search(field, value)
        return Milter.CONTINUE


    def eom(self):
        queueid = self.getsymval('i')
        for num, check_restult in enumerate(self.status):
            if all(check_restult):
                for rwt in rule_definition[num]["rewrites"]:
                    if rwt['action'] == "addheader":
                        self.addheader(rwt["field"], rwt['value'], 0)
                        print("[{0}] add header {1}:{2}".format(queueid, rwt["field"], rwt["value"]))
                    elif rwt['action'] == "chgheader":
                        self.chgheader(rwt["field"], 0, rwt['value'])
                        print("[{0}] change header {1}:{2}".format(queueid, rwt["field"], rwt["value"]))
                self.__reset_status()
                return Milter.ACCEPT

        print("[{0}] No rewrite rule matched".format(queueid))
        self.__reset_status()
        return Milter.ACCEPT


    def __reset_status(self):
        self.status = []
        for r in rule_definition:
            self.status.append([False]*len(r['conditions']))


    def __header_search(self, fieldname, value):
        if fieldname in reverse_map:
            for p in reverse_map[fieldname]:
                if p.search(value):
                    for r,c in reverse_map[fieldname][p]:
                        self.status[r][c]=True


def init_reversemap(rules):
    reversemap = {}
    for r, rule in enumerate(rules):
        for c, cond in enumerate(rule["conditions"]):
            fieldname = list(cond.keys())[0]
            pattern = list(cond.values())[0]
            compiled = re.compile(pattern)
            if fieldname not in reversemap:
                reversemap[fieldname]={}
            if compiled in reversemap[fieldname]:
                reversemap[fieldname][compiled].append([r,c])
            else:
                reversemap[fieldname][compiled]=[[r,c]]
    return(reversemap)


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
    yamlfile = open('/etc/rewrite-rules.yaml', mode="r")
    rule_definition = safe_load(yamlfile)
    yamlfile.close()
    reverse_map = init_reversemap(rule_definition)

    main()
