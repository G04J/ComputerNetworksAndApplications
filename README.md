# DNS Implementation - COMP3331/9331 Assignment

A simplified DNS (Domain Name System) client-server implementation using UDP protocol in Python.

## Author
**Gul Jain**

## Overview

This project implements a basic DNS resolver consisting of:
- **Client**: Sends DNS queries and displays responses
- **Server**: Processes queries using resource records from a master file and returns appropriate responses

All communication occurs over UDP on localhost (127.0.0.1).

## Programming Language

**Python 3.11**

The project was developed using Python due to:
- Versatility and ease of use
- Rich standard library support
- Strong familiarity with the language (used since 2019)

## Project Structure

```
.
├── client.py          # DNS client implementation
├── server.py          # DNS server implementation
├── master.txt         # Resource records file (required for server)
├── report.pdf         # Assignment report
└── README.md          # This file
```

## Requirements

- Python 3.11 or higher
- Standard Python libraries (no external dependencies):
  - `socket`
  - `struct`
  - `random`
  - `sys`
  - `time`
  - `datetime`
  - `threading`

## Master File Format

The server reads DNS resource records from `master.txt`. Each line contains one record in the format:

```
<domain-name> <type> <data>
```

### Supported Record Types:
- **A**: IPv4 address (e.g., `example.com. A 93.184.215.14`)
- **NS**: Name server (e.g., `. NS a.root-servers.net.`)
- **CNAME**: Canonical name/alias (e.g., `bar.example.com. CNAME foobar.example.com.`)

### Example master.txt:
```
example.com. A 93.184.215.14
. NS a.root-servers.net.
. NS b.root-servers.net.
a.root-servers.net. A 198.41.0.4
bar.example.com. CNAME foobar.example.com.
foobar.example.com. A 192.0.2.23
```

**Note**: The master.txt file must be in the same directory as server.py

## Installation & Setup

1. Ensure Python 3.11+ is installed:
   ```bash
   python3 --version
   ```

2. Clone or download the project files

3. Ensure `master.txt` exists in the project directory

## Usage

### Starting the Server

```bash
python3 server.py <server_port>
```

**Example:**
```bash
python3 server.py 54321
```

The server will:
- Load resource records from `master.txt`
- Bind to the specified port on localhost
- Listen for client queries indefinitely
- Support multiple concurrent clients using multithreading
- Apply random delays (0-4 seconds) to simulate real DNS behavior

### Running the Client

```bash
python3 client.py <server_port> <qname> <qtype> <timeout>
```

**Parameters:**
- `server_port`: UDP port number (must match server port)
- `qname`: Domain name to query (must end with `.`)
- `qtype`: Query type (A, NS, or CNAME)
- `timeout`: Timeout in seconds (1-15)

**Examples:**
```bash
# Query for A record
python3 client.py 54321 example.com. A 5

# Query for NS record
python3 client.py 54321 . NS 5

# Query for CNAME record
python3 client.py 54321 bar.example.com. CNAME 5
```

## Sample Interactions

### Simple A Record Query
```bash
$ python3 client.py 54321 example.com. A 5
QID: 17564

QUESTION SECTION:
example.com. A

ANSWER: 
example.com.                       A                                  93.184.215.14
```

### CNAME Resolution with Multiple Records
```bash
$ python3 client.py 54321 bar.example.com. A 5
QID: 266

QUESTION SECTION:
bar.example.com. A

ANSWER: 
bar.example.com.                   CNAME                              foobar.example.com.
foobar.example.com.                A                                  192.0.2.23
foobar.example.com.                A                                  192.0.2.24
```

### Referral (Authority Section)
```bash
$ python3 client.py 54321 example.org. A 5
QID: 51716

QUESTION SECTION:
example.org. A

AUTHORITY:
.                                  NS                                 b.root-servers.net.
.                                  NS                                 a.root-servers.net.

ADDITIONAL SECTION:
a.root-servers.net.                A                                  198.41.0.4
```

### Timeout
```bash
$ python3 client.py 54321 example.com. A 1
timed out
```

## Implementation Details

### Client (client.py)

**Key Functions:**
- `encode_client_query()`: Constructs the DNS query message
- `encode_question()`: Encodes the question section (qname + qtype)
- `encode_header()`: Encodes the header (query length + query ID)
- `decode_response()`: Parses the server response
- `print_rr()`: Formats and displays resource records

**Operation Flow:**
1. Generate random 16-bit query ID
2. Encode query with header and question sections
3. Send query via UDP to server
4. Wait for response (with timeout)
5. Decode and display response sections (Answer, Authority, Additional)

### Server (server.py)

**Data Structures:**
- `addr_dict`: Stores A records (domain → list of IP addresses)
- `cname_dict`: Stores CNAME records (alias → canonical name)
- `ns_dict`: Stores NS records (domain → list of name servers)

**Key Functions:**
- `load_rrs()`: Loads resource records from master.txt
- `add_record()`: Adds records to appropriate dictionaries
- `get_resource_records()`: Retrieves matching records for a query
- `fetch_ns_a_record()`: Finds referral records for unresolved queries
- `generate_response()`: Constructs the DNS response message
- `generate_request_response()`: Processes queries in separate threads

**Operation Flow:**
1. Load master.txt into memory dictionaries
2. Listen for UDP queries on specified port
3. For each query:
   - Spawn new thread
   - Apply random delay (0-4 seconds)
   - Match query against resource records
   - Handle CNAME chaining recursively
   - Generate response with Answer/Authority/Additional sections
   - Send response back to client

**Multithreading:**
- Uses Python's `threading.Thread` for concurrent query handling
- Each query processed in isolated thread
- Allows server to handle multiple simultaneous clients

## Message Format

### Client Query
```
+------------------+
| Header (4 bytes) |
|  - Size (2)      |
|  - QID (2)       |
+------------------+
| Question         |
|  - QName length  |
|  - QType         |
|  - QName         |
+------------------+
```

### Server Response
```
+------------------+
| Header (4 bytes) |
+------------------+
| Question         |
+------------------+
| Answer RRs       |
+------------------+
| Authority RRs    |
+------------------+
| Additional RRs   |
+------------------+
```

## Server Logging

Server logs all queries and responses with millisecond-precision timestamps:

```
2024-05-21 19:20:31.750 rcv 62370: 17564 example.com. A (delay: 3s)
2024-05-21 19:20:34.756 snd 62370: 17564 example.com. A
```

**Log Format:** `<timestamp> <rcv|snd> <client_port>: <qid> <qname> <qtype> (delay: <seconds>s)`

## Known Limitations

1. **Error Handling**: Could be more robust with edge cases
2. **Output Formatting**: Record alignment is not perfectly consistent
3. **Global Variables**: Uses global dictionaries for resource records (not ideal practice)
4. **Code Redundancy**: Some helper functions could be consolidated
5. **Query ID Range**: Uses port range (49152-65535) instead of full 16-bit range

## Testing on CSE Servers

The code is designed to run on CSE servers with Python 3.11. To test:

```bash
# On CSE server
cd /path/to/project

# Start server
python3 server.py 54321

# In another terminal, run client
python3 client.py 54321 example.com. A 5
```

## References

- Computer Networking: A Top-Down Approach, 7th Edition (Section 2.7.1 - Socket Programming with UDP)
- Python struct module documentation: https://docs.python.org/3/library/struct.html
- GeeksforGeeks struct module reference: https://www.geeksforgeeks.org/struct-module-python/
- Various StackOverflow posts for specific implementation details

## Assignment Submission

Files to submit:
- `client.py`
- `server.py`
- `report.pdf`

No Makefile required for Python implementation.

## License

This is an academic assignment for COMP3331/9331 Computer Networks and Applications.

## Contact

For questions or issues, refer to the course discussion forum or contact course staff.

---
**Course**: COMP3331/9331 Computer Networks and Applications  
**Term**: 2, 2024  
**Institution**: UNSW Sydney
