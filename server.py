from random import randrange
from datetime import datetime
from threading import Thread
import socket
import struct
import sys
import time

# initializing global variables

# dictinary to store rrs into their respective rtype
addr_dict = {}
cname_dict = {}
ns_dict = {}

# contains to showcase qtpye and their respective values 
A = 1 
NS = 2 
CNAME = 5 

# encode rtype to value 
def encodeRtype(rtype): 
    if rtype == 1:
        return "answer"
    elif rtype == 2:
        return "authority"
    elif rtype == 3:
        return "additional"

# decode rtype from value
def decodeRtype(rtype): 
    if rtype == "answer":
        return 1
    elif rtype == "authority":
        return 2
    elif rtype == "additional":
        return 3

# encode qtype to value
def encodeQtype(qtype):
    if (qtype == 'A'): 
        return A
    elif (qtype == 'NS'):
        return NS
    elif (qtype == 'CNAME'):
        return CNAME

# decode qtype from value
def decodeQtype(qtype):
    if (qtype == A): 
        return 'A'
    elif (qtype == NS):
        return 'NS'
    elif (qtype == CNAME):
        return 'CNAME'

# encode header function
def encode_header(size, qid):
    return struct.pack('<HH', size, qid)

# decode header function
def decode_header(data):
    size = struct.unpack_from('<H', data, 0)[0]
    qid = struct.unpack_from('<H', data, 2)[0]
    return size, qid

# encode response question
def encode_res_ques(qtype, qname):
    
    # encode q_type (get respective value)
    qtype = encodeQtype(qtype)    
    encoded_payload_length = struct.pack('<H', len(qname))
    encoded_query_payload = struct.pack(f'<{len(qname)}s', qname.encode())
    encoded_query_type = struct.pack('<H', qtype)

    encoded_resource_question = encoded_payload_length + encoded_query_type + encoded_query_payload
   
    return encoded_resource_question

# encode response resource record
def encode_rr(rtype, ans):
    
    r_type = decodeRtype(rtype)
    payload_length_encoded = struct.pack('<H', len(ans))
    payload_data_encoded = struct.pack(f'<{len(ans)}s', ans.encode())
    r_type_encoded = struct.pack('<H', r_type)
    total_payload_encoded = payload_length_encoded + r_type_encoded + payload_data_encoded
    
    return total_payload_encoded

# decode query question
def decode_question(data):
    
    # fetch qsize and qtype from decoded data
    qsize, qtype = struct.unpack_from('<HH', data, 4)
    # decode qtype
    qtype = decodeQtype(qtype)
    # fetch qname
    qname = data[8:8 + qsize].decode()
    return (qtype, qname)

# generate server response 
def generate_response(header, question, ans_list, auth_list, add_list):
    
    response_size = 0 
    
    qname = question[1]
    qtype = question[0]
    
    # encode response question 
    encoded_question = encode_res_ques(qtype, qname)
    response_size += len(encoded_question)

    ans_encoded = b""
    for ans in ans_list:
        ans_encoded += encode_rr("answer", ans)
        response_size += len(encode_rr("answer", ans))

    auth_encoded = b""
    for auth in auth_list:
        
        encoded_auth = encode_rr("authority", auth)
        auth_encoded += encoded_auth
        response_size += len(encoded_auth)

    add_encoded = b""
    for add in add_list:
        
        encoded_add = encode_rr("additional", add)
        add_encoded += encoded_add
        response_size += len(encoded_add)
        
    header_encoded = encode_header(response_size, header[1])
    response = header_encoded + encoded_question + ans_encoded + auth_encoded + add_encoded
    return response

# function to get rrs into their respective lists
def get_resouce_records(qtype, qname, ans_list, auths_list, adds_list):
    
    # if list is None create an empty list

    if qtype == "A" and qname in addr_dict:

        # geting all the addresses
        addresses = addr_dict[qname]
        
        # iterating over each address 
        for address in addresses:
            
            # adding each record to the list
            ans_list.append("%s A %s" % (qname, address))
    
    elif (qtype == "NS" and qname in ns_dict):
        
        # fetching name server 
        name_servers = ns_dict[qname]
        
        # iterating over each name server
        for name_server in name_servers:
            
            # adding each record to auths_list list
            auths_list.append("%s NS %s" % (qname, name_server))
            
            # if name server found in addr_dict
            if name_server in addr_dict:
                
                # add the records to additional rr. 
                adds_list.extend(f"{name_server} A {addr_record}" for addr_record in addr_dict[name_server])
                
    elif (qtype == "CNAME" and qname in cname_dict): 
        ans_list.append("%s CNAME %s" % (qname, cname_dict[qname]))
    
    elif (qtype != "CNAME" and qname in cname_dict):
        ans_list.append("%s CNAME %s" % (qname, cname_dict[qname]))
    
        # recursively calling the function again 
        return get_resouce_records(qtype, cname_dict[qname], ans_list, auths_list, adds_list)
    else:
        
        # finding 
        fetch_ns_a_record(qname, auths_list, adds_list)
    
    # returning the resultant lists
    return ans_list, auths_list, adds_list

# master file contains at least one NS record for the root zone, and its 
# corresponding A record, meaning the server can always refer the client to some other name server 
# which will provide eventual access to an answer.

def fetch_ns_a_record(qname, auths_list, adds_list):
    # Split the domain name into parts based on dots.
    domain_parts = qname.split(".")[1:]
    
    # Initialize the subdomain to the domain without the first part.
    subDomain = ".".join(domain_parts) if domain_parts else "."

    # Iterate to find the closest subdomain in the ns_dict.
    while subDomain not in ns_dict and domain_parts:
        # Remove the first index
        domain_parts = domain_parts[1:]
        
        # Update the subdomain to the remaining parts joined by dots.
        if domain_parts:
            subDomain = ".".join(domain_parts)
        else:
            # If no parts remain, set subdomain to the root domain.
            subDomain = "."

    # Retrieve NS records for the found subdomain from ns_dict.
    for ns_record in ns_dict.get(subDomain, []):
        # Add the NS record to the auths_list.
        auths_list.append("%s NS %s" % (subDomain, ns_record))
        
        # If the NS record has corresponding A records in addr_dict, add them to adds_list.
        if ns_record in addr_dict:
            adds_list.extend("%s A %s" % (ns_record, addr_record) for addr_record in addr_dict[ns_record])

# function to print server log 
def print_server_log(client_port, query_id, qname, qtype):
    # fetching corrent time 
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    # generating a random delay
    delay = randrange(0, 3)
    # printing receive server log 
    print("%s rcv %s: %s %s %s (delay: %ss)" % (time_stamp, client_port, query_id, qtype, qname, delay))

    time.sleep(delay)
    # fetching current time 
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    # printing send server log 
    print("%s snd %s: %s %s %s\n" % (time_stamp, client_port, query_id, qtype, qname))
    
# function to process requests 
def generate_request_response(header, question, client_address, server_sock):

    # extracting values from agruments into respective variables
    client_port = client_address[1]
    query_id = header[1]
    qname = question[1]
    qtype = question[0]
    
    # calling function to print server logs
    print_server_log(client_port, query_id, qtype, qname)    
    
    # fetching resource records for the query
    ans_list = []
    auths_list = []
    adds_list = []
    ans_list, auths_list, adds_list = get_resouce_records(qtype, qname, ans_list, auths_list, adds_list)
    
    # generate a response 
    dns_res = generate_response(header, question, ans_list, auths_list, adds_list)
    
    # send response to client 
    server_sock.sendto(dns_res, client_address)

def server(server_port):
    
    # creating server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', server_port))
    
    print(f'Server running on localhost: {server_port}')
    
    # looping forever to listen for queries 
    while (True):
        try:
            # receiving query from client  
            data, client_addr = sock.recvfrom(2048)

            # decoding the question and header from the query 
            question = decode_question(data)
            header = decode_header(data[:4])
            
            # multi threading 
            Thread(target=generate_request_response, args=(header, question, client_addr, sock)).start()
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")

# adding record to the respective record dict 
def add_record(domain_name, rtype, data): 
    
    if (rtype == "A"):

        # if entry does not already exist 
        if domain_name not in addr_dict:
            addr_dict[domain_name] = []
        addr_dict[domain_name].append(data)
    
    elif (rtype == "NS"):
    
        if domain_name not in ns_dict:
            ns_dict[domain_name] = []
        ns_dict[domain_name].append(data)
    
    elif (rtype == "CNAME"):
        cname_dict[domain_name] = data   

    # invalid record type passed
    else:
        print(f"ERROR: Invalid record type given: {rtype}")

def load_rrs(filename):
    try:
        file = open(filename, 'r')
        for line in file:
            parts = line.strip().split()
            if len(parts) != 3:
                print(f"invalid data")
                continue

            domain_name, rtype, data = parts
            add_record(domain_name, rtype, data)
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        file.close()
    
if __name__ == '__main__':

    # checking if correct arguments were passed 
    if len(sys.argv) != 2:
        print('Usage: server.py <server_port>')
        exit(1)
    try: 
        server_port = int(sys.argv[1])
    except ValueError:
        print('Given value must be an integer.')
        exit(1)

    # loading rrs from master file
    load_rrs("master.txt")
    
    # running the server 
    server(server_port)
