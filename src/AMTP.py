import socket
import sys
import threading

class Message_from_server:
    def __init__(self,raw_message):
        lines = raw_message.split("\n")
        self.response_code = int(lines[0])
        self.headers = {}
        for i in range(1,len(lines)):
            parts = lines[i].split(":")
            self.headers[parts[0].strip()] = parts[1].strip()

class Message_to_server:
    def __init__(self,command, headers, protocol="AMTP/0.0"):
        self.command = command
        self.headers = headers
        self.protocol = protocol
    def __str__(self):
        header_block = ""
        for key in self.headers:
            header_block += key+": "+self.headers[key]+"\n"

        return self.protocol+" "+self.command+"\n"+header_block+"\n"

class AMTP_client:
    def __init__(self,token, message_handler):
        self.message_handler = message_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server = ("localhost",1805)

        self.sock.connect(server)

        self.my_slot = -1
        self.buffer = ""
        threading.Thread(target=self.read_thread).start()

        auth_require_message = Message_to_server("CLAIM",{"Role":"Player","Secret":token,"Identifier":"Auth"})
        self.send(auth_require_message)
        print(auth_require_message)

    def send(self,msg: Message_to_server):
        self.sock.sendall(str(msg).encode())

    def read_thread(self):
        while True:
            data = self.sock.recv(1024)
            self.buffer += data.decode()
            while "\n\n" in self.buffer:
                raw_message = self.buffer[:self.buffer.index("\n\n")]
                self.buffer = self.buffer[len(raw_message)+2:]
                try:
                    self.on_message(raw_message)
                except:
                    pass

    def on_message(self,raw_message):
        message = Message_from_server(raw_message)
        if "Identifier" in message.headers:
            if message.response_code == 9:
                print("Server requesting shutdown")
                sys.exit(0)

            if message.headers["Identifier"] == "Auth":
                if message.response_code == 0:
                    self.my_slot = int(message.headers["Slot"])
                    print("Authentication successful: ",self.my_slot)
                else:
                    print("ERROR: Authentication failed, exiting")
                    sys.exit(1)
        if "ActionRequiredBy" in message.headers:
            arb_header = message.headers["ActionRequiredBy"]
            if arb_header == "*" or arb_header == str(self.my_slot):
                self.message_handler(message,True)
            else:
                self.message_handler(message,False)
        else:
            self.message_handler(message,False)

