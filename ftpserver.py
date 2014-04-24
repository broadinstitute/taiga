# based on https://gist.github.com/scturtle/1035886#file-ftpserver-py
#!/usr/bin/env python2
# coding: utf-8

import socket,threading,time,StringIO
import requests
import json
#import traceback

#local_ip =  socket.gethostbyname(socket.gethostname())
local_ip = "10.1.4.27"
local_port = 9021

class FTPserverThread(threading.Thread):
    def __init__(self,(conn,addr), list_dir_callback, open_file_callback):
        self.conn=conn
        self.addr=addr
        self.cwd="/"
        self.rest=False
        self.pasv_mode=False
        self.list_dir_callback = list_dir_callback
        self.open_file_callback = open_file_callback
        threading.Thread.__init__(self)

    def run(self):
        self.conn.send('220 Welcome!\r\n')
        while True:
            cmd=self.conn.recv(256)
            if not cmd: break
            else:
                print 'Recieved:',cmd
                try:
                    func=getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    #traceback.print_exc()
                    self.conn.send('500 Sorry.\r\n')
        print "connection broken"

    def SYST(self,cmd):
        self.conn.send('215 UNIX Type: L8\r\n')
    def OPTS(self,cmd):
        if cmd[5:-2].upper()=='UTF8 ON':
            self.conn.send('200 OK.\r\n')
        else:
            self.conn.send('451 Sorry.\r\n')
    def USER(self,cmd):
        self.conn.send('331 OK.\r\n')
    def PASS(self,cmd):
        self.conn.send('230 OK.\r\n')
        #self.conn.send('530 Incorrect.\r\n')
    def QUIT(self,cmd):
        self.conn.send('221 Goodbye.\r\n')
    def NOOP(self,cmd):
        self.conn.send('200 OK.\r\n')
    def TYPE(self,cmd):
        self.mode=cmd[5]
        self.conn.send('200 Binary mode.\r\n')

    def CDUP(self,cmd):
        self.conn.send('200 OK.\r\n')

    def PWD(self,cmd):
        self.conn.send('257 \"%s\"\r\n' % self.cwd)

    def CWD(self,cmd):
        self.cwd=cmd[4:-2]
        self.conn.send('250 OK.\r\n')

    def PORT(self,cmd):
        if self.pasv_mode:
            self.servsock.close()
            self.pasv_mode = False
        l=cmd[5:].split(',')
        self.dataAddr='.'.join(l[:4])
        self.dataPort=(int(l[4])<<8)+int(l[5])
        self.conn.send('200 Get port.\r\n')

    def PASV(self,cmd): # from http://goo.gl/3if2U
        self.pasv_mode = True
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.bind((local_ip,0))
        self.servsock.listen(1)
        ip, port = self.servsock.getsockname()
        print 'open', ip, port
        self.conn.send('227 Entering Passive Mode (%s,%u,%u).\r\n' %
                (','.join(ip.split('.')), port>>8&0xFF, port&0xFF))
        print "sent info"

    def start_datasock(self):
        if self.pasv_mode:
            print "waiting for connect"
            self.datasock, addr = self.servsock.accept()
            print 'connect:', addr
        else:
            print "connecting..."
            self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.datasock.connect((self.dataAddr,self.dataPort))

    def stop_datasock(self):
        print "stop datasock"
        self.datasock.close()
        if self.pasv_mode:
            self.servsock.close()

    def LIST(self,cmd):
        self.conn.send('150 Here comes the directory listing.\r\n')
        print 'list:', self.cwd
        self.start_datasock()
        for t in self.list_dir_callback(self.cwd):
            k=self.toListItem(t)
            self.datasock.send(k+'\r\n')
        self.stop_datasock()
        self.conn.send('226 Directory send OK.\r\n')

    def toListItem(self, fn):
        mode='r--r--r--'
        d='-'
        size=1
        ftime=time.strftime(' %b %d %H:%M ', time.gmtime(time.time()))
        return d+mode+' 1 user group '+str(size)+ftime+fn

    def MKD(self,cmd):
        self.conn.send('450 Not allowed.\r\n')

    def RMD(self,cmd):
        self.conn.send('450 Not allowed.\r\n')

    def DELE(self,cmd):
        self.conn.send('450 Not allowed.\r\n')

    def RNFR(self,cmd):
        self.conn.send('350 Ready.\r\n')

    def RNTO(self,cmd):
        self.conn.send('450 Not allowed.\r\n')

    def REST(self,cmd):
        self.pos=int(cmd[5:-2])
        self.rest=True
        self.conn.send('250 File position reseted.\r\n')

    def SIZE(self, cmd):
        filename = cmd[5:-2]
        self.conn.send('450 Not allowed.\r\n')

    def RETR(self,cmd):
        filename = cmd[5:-2]
        fi = self.open_file_callback(self.cwd, filename, self.mode)
        print 'Downloading:',filename
        self.conn.send('150 Opening data connection.\r\n')
        if self.rest:
            fi.seek(self.pos)
            self.rest=False
        data = fi.read(1024)
        self.start_datasock()
        while data:
            self.datasock.send(data)
            data=fi.read(1024)
        fi.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')

    def STOR(self,cmd):
        self.conn.send('450 Not allowed.\r\n')

class TaigaClient(object):
  def __init__(self, url):
    self.url = url
  
  def find_dataset_ids_by_tag(self, tag):
    url = self.url + "/rest/v0/triples/find"
    data = {"query":[[{"var":"dataset"}, {"id":"hasTag"}, tag]]}
    print "query", data
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    response = r.json()
    print "response", response
    return [x["dataset"]["id"] for x in response["results"]]
  
  def get_name(self, dataset_id):
    url = self.url + "/rest/v0/metadata/" + dataset_id
    r = requests.get(url)
    response = r.json()
    return response['name']
  
  def get_name_map(self, dirname):
    dataset_ids = self.find_dataset_ids_by_tag(dirname)
    def construct_name_tuple(dsid):
      n = self.get_name(dsid)
      return (n.replace(" ","_").replace(",","_")+".csv", n)
    return dict([construct_name_tuple(dsid) for dsid in dataset_ids])
    
  def list_dir_callback(self, dirname):
    m = self.get_name_map(dirname)
    return m.keys()
    
  def open_file_callback(self, dirname, filename, mode):
    m = self.get_name_map(dirname)
    orig_name = m[filename]
    return StringIO.StringIO("virtual file %s" % orig_name)

class FTPserver(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((local_ip,local_port))
        threading.Thread.__init__(self)

    def run(self):
        self.sock.listen(5)
        while True:
            tc=TaigaClient("http://localhost:8999")
            th=FTPserverThread(self.sock.accept(), tc.list_dir_callback, tc.open_file_callback)
            th.daemon=True
            th.start()

    def stop(self):
        self.sock.close()

if __name__=='__main__':
    ftp=FTPserver()
    ftp.daemon=True
    ftp.start()
    print 'On', local_ip, ':', local_port
    while True:
        raw_input('Kill via ^C...\n')
    #ftp.stop()
