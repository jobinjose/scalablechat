import socket
import sys
import re
import random
import queue
import threading
from threading import Thread

class Client_Thread(Thread):
    def __init__(self,socket,ip,port):
        Thread.__init__(self)
        self.socket = socket
        self.ip = ip
        self.port = port
        self.client_name = ''
        self.join_id = 0

    def get_roomID(self):
        for chatrm in chatroom_db:
            if chatrm == self.chatroom:
                return chatroom_db[self.chatroom]
        value = len(chatroom_db)+1
        chatroom_db[self.chatroom.lower()]=value
        return value
    def get_roomID_join(self,chat_chatroom):
        for chatrm in chatroom_db:
            if chatrm == chat_chatroom:
                return chatroom_db[chat_chatroom]
        value = len(chatroom_db)+1
        chatroom_db[chat_chatroom.lower()]=value
        return value

    def get_clientID(self):
        for id in user_db:
            if id == self.client_name:
                return user_db[self.client_name]
        return self.set_clientID()

    def get_clientID_disconnect(self,disc_clientname):
        return user_db[disc_clientname]

    def set_clientID(self):
        value = len(user_db)+1
        user_db[self.client_name]=value
        return value

    def set_user_rnum(self):
        for room in user_rnum:
            if self.room_ref == room:
                user_rnum[self.room_ref].append(self.join_id)
                return
        user_rnum[self.room_ref] = [self.join_id]
    def set_user_rnum_chat(self,chat_roomref):
        for room in user_rnum:
            if chat_roomref == room:
                user_rnum[chat_roomref].append(self.join_id)
                return
        user_rnum[chat_roomref] = [self.join_id]

    def set_user_roomcount(self):
        for user in user_roomcount:
            if user == self.join_id:
                user_roomcount[self.join_id] = user_roomcount[self.join_id]+1
                return
        user_roomcount[self.join_id] = 1

    def set_user_room(self,join_roomref):
        for user in user_room:
            if user == self.client_name:
                for room in user_room[self.client_name]:
                    if room == join_roomref:
                        return
                user_room[self.client_name].append(join_roomref)
                return
        user_room[self.client_name] = [join_roomref]

    def get_user_room_disconnect(self,disc_client_name):
        return user_room[disc_client_name]

    def reduce_user_roomcount(self):
        user_roomcount[self.join_id] = user_roomcount[self.join_id]-1
        if user_roomcount[self.join_id] == 0:
            del user_roomcount[self.join_id]

    def reduce_roomcount_after_disconnect(self,disc_joinid):
        try:
            user_roomcount[disc_joinid] = user_roomcount[disc_joinid] - 1
            if user_roomcount[disc_joinid] == 0:
                del user_roomcount[disc_joinid]
        except KeyError:
            pass

    def remove_user_from_room_leave(self,leave_roomref):
        user_rnum[leave_roomref].remove(self.join_id)

    def remove_user_rnum_disconnect(self,disc_roomref,disc_joinid):
        for jid in user_rnum[disc_roomref]:
            if jid == disc_joinid:
                user_rnum[disc_roomref].remove(disc_joinid)

    def get_users_in_room(self):
        return user_rnum[self.room_ref]

    def get_users_in_room_chat_conv(self,conv_roomref):
        return user_rnum[conv_roomref]

    def set_user_filenum_desc_chat(self,chat_roomref):
        user_filenum_desc[(chat_roomref,self.join_id)] = self.socket.fileno()

    def get_user_filenum_desc_gen(self, gen_roomref, other_join_id):
        return user_filenum_desc[(gen_roomref,other_join_id)]

    def delete_user_filenum_desc_leave(self,leave_roomref):
        del user_filenum_desc[(leave_roomref,self.join_id)]

    def delete_user_filenum_desc_disconnect(self,disc_roomref,disc_joinid):
        try:
            del user_filenum_desc[(disc_roomref,disc_joinid)]
        except KeyError as e:
            pass

    def broadcast(self,file_no):
        try:
            message = send_que[file_no].get(False)
            print("Message to be broadcast: " + message)
            send_queue_filenum_desc_client[file_no].send(message.encode())
        except queue.Empty:
            message = "No message to broadcast"
        except KeyError as e:
            pass

    def broadcast_data(self):
        send_queue_filenum_desc_client[self.socket.fileno()] = self.socket

    def run(self):
        #loop for each message from client
        while True:
            try:
                msg_from_client=self.socket.recv(buff_size).decode()
            except ConnectionResetError:
                pass
            if "JOIN_CHATROOM" in msg_from_client:
                try:
                    msg_split = re.findall(r"[\w']+", msg_from_client)
                    join_chatroom = msg_split[1]
                    self.client_name = msg_split[7]
                    join_room_ref = self.get_roomID_join(join_chatroom)
                    self.join_id = self.get_clientID()
                    self.set_user_rnum_chat(join_room_ref)
                    self.set_user_roomcount()
                    self.set_user_room(join_room_ref)
                    self.set_user_filenum_desc_chat(join_room_ref)
                    self.broadcast_data()
                    join_msgto_client = "JOINED_CHATROOM: " + str(join_chatroom) + "\nSERVER_IP: "+str(ip)+"\nPORT: "+str(port)+"\nROOM_REF: "+str(join_room_ref)+"\nJOIN_ID: "+str(self.join_id)+"\n"
                    self.socket.send(join_msgto_client.encode())
                    allusers_in_room = self.get_users_in_room_chat_conv(join_room_ref)
                    join_message_to_room = str(self.client_name) + " has joined this chatroom\n"
                    join_message_to_room_format = "CHAT: "+ str(join_room_ref) + "\nCLIENT_NAME: "+str(self.client_name) + "\nMESSAGE: "+str(join_message_to_room)+"\n"
                    lock.acquire()
                    Tosend_fileno = []
                    for user_id in allusers_in_room:
                        Tosend_fileno.append(self.get_user_filenum_desc_gen(join_room_ref,user_id))
                    for i, j in zip(send_que.values(), send_que):
                        if j in Tosend_fileno:
                            i.put(join_message_to_room_format)
                    lock.release()
                    for ts in Tosend_fileno:
                        self.broadcast(ts)
                except:
                    err_msgto_client = "ERROR_CODE: 101"+"\nERROR_DESCRIPTION: "+str(sys.exec_info()[0])+"\n"
                    self.socket.send(err_msgto_client.encode())

            elif "HELO" in msg_from_client:
                try:
                    print("Message : ", msg_from_client)
                    host_name = socket.gethostname()
                    host_ip = socket.gethostbyname(host_name)
                    host_port = port
                    message = msg_from_client+"IP:"+str(host_ip)+"\nPort:"+str(host_port)+"\nStudentID:17312296"
                    self.socket.send(message.encode())
                except:
                    err_msgto_client = "ERROR_CODE: 102"+"\nERROR_DESCRIPTION: "+str(sys.exec_info()[0])+"\n"
                    self.socket.send(err_msgto_client.encode())

            elif "KILL_SERVICE" in msg_from_client:
                print("Got kill request. Server shutting down...")
                tcp_socket.shutdown(0)
                tcp_socket.close()
                break

            elif "DISCONNECT" in msg_from_client:
                try:
                    print("Message : ", msg_from_client)
                    msg_split = re.findall(r"[\w']+", msg_from_client)
                    disconnect_client_name = msg_split[5]
                    disconnect_joinid = self.get_clientID_disconnect(disconnect_client_name)
                    roomlist_of_disc_client = self.get_user_room_disconnect(disconnect_client_name)
                    message = disconnect_client_name + " has disconnected.."
                    for dr in roomlist_of_disc_client:
                        print("rooms_refs : ",dr)
                        disconnect_message_format = "CHAT: "+str(dr)+ "\nCLIENT_NAME: "+str(disconnect_client_name) + "\nMESSAGE: "+str(message)+"\n\n"
                        allusers_in_room = self.get_users_in_room_chat_conv(dr)
                        lock.acquire()
                        Tosend_fileno = []
                        for user_id in allusers_in_room:
                            Tosend_fileno.append(self.get_user_filenum_desc_gen(dr,user_id))
                        for i, j in zip(send_que.values(), send_que):
                            if j in Tosend_fileno:
                                i.put(disconnect_message_format)
                        lock.release()
                        for ts in Tosend_fileno:
                            self.broadcast(ts)
                        self.remove_user_rnum_disconnect(dr,disconnect_joinid)
                        self.reduce_roomcount_after_disconnect(disconnect_joinid)
                        self.delete_user_filenum_desc_disconnect(dr,disconnect_joinid)
                except:
                    err_msgto_client = "ERROR_CODE: 103"+"\nERROR_DESCRIPTION: "+str(sys.exec_info()[0])+"\n"
                    self.socket.send(err_msgto_client.encode())

            elif "LEAVE_CHATROOM" in msg_from_client:
                try:
                    print("Message : ", msg_from_client)
                    msg_split = re.findall(r"[\w']+", msg_from_client)
                    leave_client_name = msg_split[5]
                    leave_room_ref = int(msg_split[1])
                    leave_join_id = msg_split[3]
                    msg = "LEFT_CHATROOM: " + str(leave_room_ref) + "\nJOIN_ID: " + str(leave_join_id)+"\n"
                    self.socket.send(msg.encode())
                    message = leave_client_name + " has left this chatroom.."
                    leave_message_format = "CHAT: "+ str(leave_room_ref) + "\nCLIENT_NAME: "+str(leave_client_name) + "\nMESSAGE: "+str(message)+"\n\n"
                    allusers_in_room = self.get_users_in_room_chat_conv(leave_room_ref)
                    lock.acquire()
                    Tosend_fileno = []
                    for user_id in allusers_in_room:
                        Tosend_fileno.append(self.get_user_filenum_desc_gen(leave_room_ref,user_id))
                    for i, j in zip(send_que.values(), send_que):
                        if j in Tosend_fileno:
                            i.put(leave_message_format)
                    lock.release()
                    for ts in Tosend_fileno:
                        self.broadcast(ts)
                    self.remove_user_from_room_leave(leave_room_ref)
                    self.reduce_user_roomcount()
                    self.delete_user_filenum_desc_leave(leave_room_ref)
                    print(user_rnum)
                    print("Break")
                except:
                    err_msgto_client = "ERROR_CODE: 104"+"\nERROR_DESCRIPTION: "+str(sys.exec_info()[0])+"\n"
                    self.socket.send(err_msgto_client.encode())
            elif "CHAT:" in msg_from_client:
                try:
                    print("Message : ", msg_from_client)
                    message = msg_from_client
                    print("Message : ", message)
                    msg_split = re.findall(r"[\w']+", msg_from_client)
                    print("Split message :", msg_split)
                    conv_client_name = msg_split[5]
                    conv_room_ref = int(msg_split[1])
                    conv_join_id = msg_split[3]
                    conv_message = msg_split[7]
                    for msgsp in msg_split[8:]:
                        conv_message = conv_message +" "+ msgsp
                    msg = "CHAT: " + str(conv_room_ref) + "\nCLIENT_NAME: " + str(conv_client_name) + "\nMESSAGE: " + str(conv_message) + "\n\n"
                    allusers_in_room = self.get_users_in_room_chat_conv(conv_room_ref)
                    lock.acquire()
                    Tosend_fileno = []
                    for user_id in allusers_in_room:
                        Tosend_fileno.append(self.get_user_filenum_desc_gen(conv_room_ref,user_id))
                    for i, j in zip(send_que.values(), send_que):
                        if j in Tosend_fileno:
                            i.put(msg)
                    lock.release()
                    for ts in Tosend_fileno:
                        self.broadcast(ts)
                except:
                    err_msgto_client = "ERROR_CODE: 105"+"\nERROR_DESCRIPTION: "+str(sys.exec_info()[0])+"\n"
                    self.socket.send(err_msgto_client.encode())
no_of_clients = 0
user_rnum = {}
user_roomcount = {}
user_room = {}
chatroom_db = {}
user_db = {}
user_filenum_desc = {}
send_queue_filenum_desc_client = {}
buff_size = 2048
lock = threading.Lock()
send_que = {}
ip = '0.0.0.0'
port = int(sys.argv[1])
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_socket.bind(('',port))

client_thread = []
while True:
    tcp_socket.listen(6)
    print("Server up and running. Waiting for Clients to join...")
    try:
        (client_soc,(client_ip,client_port)) = tcp_socket.accept()
    except OSError as err:
        sys.exit(0)
    no_of_clients = no_of_clients + 1
    print("Number of threads: " + str(no_of_clients))
    q = queue.Queue()
    lock.acquire()
    send_que[client_soc.fileno()] = q
    lock.release()
    print("<" + client_ip + "," + str(client_port) + "> connected")
    client_thread = Client_Thread(client_soc,client_ip,client_port)
    client_thread.daemon = True
    client_thread.start()
