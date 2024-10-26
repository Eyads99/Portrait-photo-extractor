from flask import Flask
from flask_restful import Api, Resource, reqparse, fields, abort
from werkzeug.datastructures import FileStorage
import os
import numpy as np
import cv2
import base64

app = Flask(__name__)
api = Api(app)


portrait_request_args = reqparse.RequestParser()
portrait_request_args.add_argument("name", type=str, help="Name of the portrait", required=True, location='form')
portrait_request_args.add_argument("image", type=FileStorage, help="Image with a portrait", required=False, location='files')

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class Portrait(Resource):
    def post(self):
        return {"message": "This endpoint accepts GET requests with images"}
                
    def put(self):
        return {"message": "This endpoint accepts GET requests with images"}
      
    def delete(self):        
        return {"message": "This endpoint accepts GET requests with images"}
    
    def get(self):
        args = portrait_request_args.parse_args()
        
        image_file = args['image']
        
        # Convert the uploaded file to an image array
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            abort(400, message="Invalid image format")
        
        # Convert the image to base64
        _, image_encoded = cv2.imencode('.png', image)
        image_base64 = base64.b64encode(image_encoded).decode('utf-8')
        
        # Ensure directory exists
        save_folder = 'rawdata'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        # Save the base64 image to a file
        with open(os.path.join(save_folder, 'img'), 'w') as image_file:
            image_file.write(image_base64)
        
        return {"image": image_base64}

api.add_resource(Portrait, "/portrait_extract/")
@app.route("/")
def index():
        return "For documentation go to /docs"

if __name__ == "__main__":
        app.run(debug=True)