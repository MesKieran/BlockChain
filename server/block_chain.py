import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse
from hashlib import sha256

""" 
hash proof example 
x = 5
y = 0
while sha256(f'(x*y)'.encode()).hexdigest()[-1] != "0":
    y += 1
print(f'The solution is y = {y}')
"""

class BlockChain:
    def __init__(self):
        # store transction
        self.current_transactions = []
        # store blockchain
        self.chain = []
        # store node
        self.nodes = set()
        # create block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'https://localhost:5001'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block["previous_hash"] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        consensus algo to solve conflicts
        use the longest chain in the network
        :return: <bool> True   If the chain is replaced return true, else return false
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in the network
        for node in neighbours:
            response = requests.get(f'https://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, proof, previous_hash):
        """
        generate new block
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous Block
        :return:<dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """ generate new transcation info, add it to the next block that is to be mine
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the recipient
        :param amount: <int> Amount
        :return <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1
    @property
    def last_block(self):
        return self.chain[-1]
    @staticmethod
    def hash(block):
        """
        generate hash value (SHA-256)
        :param block: <dict> Block
        :return: <str>
        """
        # We must make sure hat the Dictionary is Ordered, or we'll have inconsistant hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    def proof_of_work(self, last_proof):
        """
        simple PoW:
        - find a p' that makes hash(pp') starts with 4 zeroes
        - p is the proof of the last block and p' is the proof of current block
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    @staticmethod
    def valid_proof(last_proof, proof):
        """
        validation proof: is hash(last_proof, proof) starts with 4 zeroes?
        :param last_proof:
        :param proof:
        :return:
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
