from server import app
from flask import request, jsonify
import uuid
from server.block_chain import BlockChain

# create a random name for the node
node_identifier = str(uuid.uuid4()).replace('-', '')
block_chain = BlockChain()

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = block_chain.last_block
    last_proof = last_block['proof']
    proof = block_chain.proof_of_work(last_proof)
    # provide PoW validation for reward
    # sender is 0 indicate new coin mined
    block_chain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount='1',
    )
    # Forge the new Block by adding it to the chain
    block = block_chain.new_block(proof, None)

    response = {
        'message': "New Block Forged",
        "index": block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    #create a new Transacrion
    index = block_chain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': block_chain.chain,
        'length': len(block_chain.chain),
    }
    return jsonify(response), 200
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        block_chain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_node': list(block_chain.nodes),
    }
    return jsonify(response), 201


@app.route('/node/resolve', methods=['GET'])
def consensus():
    replaced = block_chain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': block_chain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoriatative',
            'chain': block_chain.chain
        }
    return jsonify(response), 200