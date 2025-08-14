import socket
import struct
from random import randrange
import sys

# initializing global variables
A = 1 
NS = 2 
CNAME = 5 
BYTE_4 = 4 
DIST = 35
# function to decode rtype
def decodeRtype(rtype): 
    if (rtype == 1):
        return"Answer"
    elif (rtype == 2):
        return"Authority"
    elif (rtype == 3):
        return "Additional"

# function to decode qType
def encodeQType(qType):
    if (qType == 'A'): 
        return A
    elif (qType == 'NS'):
        return NS
    elif (qType == 'CNAME'):
        return CNAME

# function to encode question
def encode_question(qType, qName):
    qname_encoded = qName.encode()
    qtype_value = encodeQType(qType)
    qtype_encoded = struct.pack('<H', qtype_value)
    qname_length = struct.pack('<H', len(qname_encoded))
    return qname_length + qtype_encoded + qname_encoded

# function to encode header
def encode_header(question, qId):
    ques_len = len(question)
    return struct.pack('<HH', ques_len, qId)

# function to decode reponse 
def decode_response(data):
    
    # fetch length of qName 
    qname_length = struct.unpack('<H', data[BYTE_4:6])[0]
    
    # initialize empty array to store rrs 
    rrs = []
    
    # skip the header and question 
    offset = 2*BYTE_4 + qname_length
    
    # iterate through the data and decode rrs
    while offset < len(data):

        # fetch rr val and rr_len length
        rr_len = struct.unpack('<H', data[offset: offset + 2])[0]
        rr_val = struct.unpack('<H', data[offset + 2: offset + BYTE_4])[0]

        # decode rtype
        rtype = decodeRtype(rr_val)

        # fetch record 
        rec = data[offset + BYTE_4: offset + BYTE_4 + rr_len]
        payload_data = struct.unpack(f'<{rr_len}s', rec)[0].decode()
        
        rrs.append((rtype, payload_data))
        # go to the next record
        offset += BYTE_4 + rr_len

    return rrs

# function to encode client query
def encode_client_query(qId, qName, qType):

    question = encode_question(qType, qName)
    
    header = encode_header(question, qId)
    return header + question


def client(server_port, qName, qType, timeout):
    
    # choose a random qId 
    qId = randrange(49152, 65535)
    
    # encode client query 
    bytes = encode_client_query(qId, qName, qType)

    # initiate client socket 
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # setting timeout
    clientSocket.settimeout(timeout)
    clientSocket.sendto(bytes, ("localhost", server_port))
    
    print(f"QID: %s\n" % qId)
    print("QUESTION SECTION:")
    print(qName, qType, "\n")
    try:
        res, _ = clientSocket.recvfrom(2048)
        rrs = decode_response(res)
        
        print("ANSWER: ")
        for rr in rrs: 
            if (rr[0] == "Answer"):
                print_rr(rr)
        print('\n')
        print("AUTHORITY:")
        for rr in rrs: 
            if (rr[0] == "Authority"):
                print_rr(rr)
        print('\n')
        print("ADITIONAL SECTION:")
        for rr in rrs: 
            if (rr[0] == "Additional"):
                print_rr(rr)
        print('\n')
            
    except socket.timeout:
        print('timed out')
    clientSocket.close()
# print out resource records 
def print_rr(rr):
    
    record = rr[1]
    record = record.split(' ')
    qname = record[0]
    rtype = record[1]
    data = record[2]
    print(f"{qname:<{DIST}} {rtype:<{DIST}} {data}")
    
    
# step 1: take in the arguments 
if __name__ == "__main__":

    # checking if correct arguments are passed 
    if len(sys.argv) != 5:
        print("Usage: python3 client.py <server_port> <qName> <qType> <timeout>")
        sys.exit(1)

    qName = sys.argv[2]
    qType = sys.argv[3]
    # checking if timeout is an integer
    try: 
        timeoutTime = int(sys.argv[4])
        server_port = int(sys.argv[1])
    except ValueError:
        print("Given value must be an integer.")
        sys.exit(1)

    # calling the client function
    client(server_port, qName, qType, timeoutTime)
