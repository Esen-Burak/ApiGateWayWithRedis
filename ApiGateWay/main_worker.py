from flask import Flask, request, jsonify, abort
import redis
import os
import requests
from dotenv import load_dotenv
import logging
import smtplib
from email.mime.text import MIMEText

load_dotenv() 
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# Redis connection
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

# Mail sender
def send_error_email(subject, message):
    sender = 'xxx@mail.com'
    recipients = ['xxx@mail.com']
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('xxx@mail.com', 'xxx')
        server.sendmail(sender, recipients, msg.as_string())

# API Gateway 
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_gateway(path):
    api_key = request.headers.get('X-API-Key')
    if api_key not in os.getenv('APIKEYS', '').split(';'):
        logging.error(f'Invalid API key: {api_key}')
        abort(401, description="Unauthorized: Invalid API key")

    cache_key = f"cache:{path}:{request.args}"
    r.setex(cache_key, 300, "AAAAAAAAAAA")
    cached_response = r.get(cache_key)

    url_list = os.getenv('APIURLS', '').split(';')
    for url in url_list:
        try:
            logging.info(f'Making request to {url}')
            response = requests.request(
                method=request.method,
                url=f"{url}/{path}",
                headers=request.headers,
                params={"key": cache_key},
                data=request.data,
                timeout=300 
            )
            if response.ok:
                cached_response = r.get(cache_key)
                return jsonify(cached_response), response.status_code
        except requests.exceptions.RequestException as e:
            logging.error(f'Error during requests to {url}: {str(e)}')
            #send_error_email('API Gateway Error', str(e))
            continue

    logging.error('Failed to get a valid response from all URLs')
    #send_error_email('API Gateway Failure', 'All URL requests failed')
    return jsonify({'error': 'Service unavailable'}), 503

if __name__ == '__main__':
    app.run(host=os.environ.get('HOST',"localhost"),port=int(os.environ.get('PORT',10003)),debug=True)