from flask import Flask, jsonify, request
import redis
import logging

app = Flask(__name__)
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

@app.route('/example', methods=['GET'])
def example_api():
    key = request.args.get('key')
    value = r.get(key)
    if value:
        logging.info('Returning value from Redis')
        return jsonify({'response': value}), 200
    else:
        new_value = "Example Value"
        r.setex(key, 300, new_value)  # Store new value for 5 minutes
        logging.info('Stored new value in Redis and returning')
        return jsonify({'response': new_value}), 201

if __name__ == '__main__':
    app.run(host="localhost",port=10001)