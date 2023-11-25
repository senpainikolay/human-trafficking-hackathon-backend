from flask import Flask , request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO  
import os  
from PyPDF2 import PdfReader

import utils,resume_and_cosine
import threading  
from flask_cors import CORS
import logging 
import json


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'db.sqlite') 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLACHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) 


# Enable CORS for all domains on all routes
CORS(app, resources={r"/*": {"origins": "*"}})


class Upload(db.Model):
    id  = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50)) 
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(500)) 
    description = db.Column(db.String(500))
    sumerize = db.Column(db.String(500))
    access_type = db.Column(db.String(10))
    data = db.Column(db.LargeBinary) 
    pdf_kek = db.Column(db.LargeBinary) 
    doc_type = db.Column(db.String(10))

with app.app_context():
    db.create_all() 


def update_doc(entity_id, text_data):
    with app.app_context():
        try:
            my_entity = Upload.query.filter_by(id=entity_id).first()
            if my_entity:
                json_string_res = resume_and_cosine.sumarize_text(text_data) 
                json_map = json.loads(json_string_res)
                my_entity.description = json_map['description'] 
                my_entity.sumerize = json_map['text'] 
                my_entity.title = json_map['title']
                db.session.commit()
                logging.info(f"Updated entity {entity_id} successfully.")
            else:
                logging.warning(f"Entity with ID {entity_id} not found.")
        except Exception as e:
            logging.error(f"Error updating entity {entity_id}: {e}")

@app.route('/upload', methods  = ['POST'])
def upload_doc_to_db():
    file = request.files['file']
    user_id = request.form['user_id']
    access_type = request.form['access_type'] 
    doc_type = request.form['doc_type']

    data = ''

    pdf_kek = file.read()

    if doc_type == 'pdf':
        reader = PdfReader(BytesIO(pdf_kek))
        text = ''

        for page in reader.pages:
            text += page.extract_text() 
        data = text
    else:
        data = pdf_kek


    upload = Upload(filename =file.filename, data=data.encode('utf-8'),user_id=user_id, access_type=access_type, doc_type=doc_type, pdf_kek=pdf_kek)  
    db.session.add(upload)
    db.session.commit() 

    background_thread = threading.Thread(target=update_doc, args=(upload.id,data))
    background_thread.start()
 
    return f'Uploaded: {file.filename}' 



@app.route('/search', methods=['GET'])
def read_all_files():
    raw_keywords = request.args.get('keywords', '')
    keywords = raw_keywords.split('_')
    pattern = utils.build_search_pattern(keywords)
    try:
        uploads = Upload.query.all()
        result = []
        for doc in uploads:

                result.append({
                    'id': doc.id,
                    'title': doc.title,
                    'description': doc.description,
                    'matched_keywords': utils.count_word_occurrences(doc.data.decode('utf-8'),pattern)
                })

        return jsonify({'data': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@app.route('/user/<id>/documents', methods  = ['GET'])
def get_user_docs(id): 
    uploads = Upload.query.filter_by(user_id=id).all()
    files = [{'title': upload.title, 'id': upload.id, 'description': upload.description} for upload in uploads]
    return jsonify({'data': files}) 

@app.route('/document/<id>', methods  = ['GET'])
def get_doc_by_id(id): 
    upload = Upload.query.filter_by(id=id).first()  
    uploads = Upload.query.all()  
    recs = []
    sorted_recs = []
    for up in uploads:
        if up == upload:
            continue 

        score = resume_and_cosine.find_similarity(upload.sumerize, up.sumerize)
        recs.append({"score" : score, "id" : up.id, "title" : up.title, "description" : up.description}) 
        # Sorting the recs list of dictionaries by the "score" key
        sorted_recs = sorted(recs, key=lambda x: x["score"], reverse=True)[:3]

    files = {'title' : upload.title, 'summarize' : upload.sumerize, 'recs' : sorted_recs }
    return jsonify(files)

@app.route('/download/<upload_id>') 
def download(upload_id):
    try:
        upload = Upload.query.get(upload_id)   
        kkkk = BytesIO(upload.pdf_kek)
        # Send PDF as a file to the Flask request
        return send_file(kkkk, download_name="output.pdf", as_attachment=True) 
    except Exception as e:
        return str(e)
   
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug = True)