import socket,sys,threading
def run(fam,addr,port):
    s=socket.socket(fam);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind((addr,port));s.listen(50)
    while True:
        c,_=s.accept();c.close()
for f,a,p in ((socket.AF_INET,'127.0.0.1',47811),(socket.AF_INET6,'::1',47811)):
    threading.Thread(target=run,args=(f,a,p),daemon=True).start()
import time;time.sleep(3000)
