from flask import Flask, request, jsonify, Response
from model import Model
from flask_cors import CORS
import json 

app = Flask(__name__)
CORS(app)

# Global variables to store the initialized model and tokenizer
model = None

@app.route('/init', methods=['POST'])
def initialize_model():
    global model
    print(model)
    if model is None:
        use_local = request.json.get('use_local', True)
        model = Model(verbose=True, use_local=use_local)

    return jsonify({'message': 'Model initialized successfully.'})

@app.route('/inference', methods=['POST'])
def perform_inference():
    global model
    input_text = request.json.get('input_text', None)
    context = request.json.get('context', None)
    if input_text is not None and context is not None:
        return jsonify({'input_text': input_text, 'output_text': model.inference(prompt=input_text, context=context)})
    else:
        return jsonify({'error': 'Input text and context is required.'}), 400
    
@app.route('/get-context', methods=['POST'])
def get_context():
    global model
    input_text = request.json.get('input_text', None)
    use_both = request.json.get('use_both', True)
    db_id = request.json.get('db_id', None)
    if input_text is not None and db_id is not None:
        context = model.get_context(input_text, db_id, useBoth=use_both)
        contextDict = []
        for item in context:
            contextDict.append(item.__dict__)
        return jsonify({'input_text': input_text, 'context': contextDict})
    else:
        return jsonify({'error': 'input_text and db_id is required.'}), 400
    

@app.route('/stream-inference', methods=['POST'])
def perform_streamed_inference():
    global model
    input_text = request.json.get('input_text', None)
    context = request.json.get('context', None)
    if input_text is not None and context is not None:
        return Response(model.stream_inference(input_text, context), content_type='text/plain', status=200)
    else:
        return jsonify({'error': 'Input text and context is required.'}), 400
    
# Handling OPTIONS requests for the same endpoint
@app.route('/stream-inference', methods=['OPTIONS'])
def handle_options_request():
    # Add the necessary headers to allow the actual request
    response = jsonify({"message": "Preflight request successful"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response

if __name__ == '__main__':
    app.run(debug=True)
