from flask import Flask, request
from flask_restful import Api, Resource, reqparse, fields, abort
from werkzeug.datastructures import FileStorage
import os
import numpy as np
import cv2
import base64
import re

app = Flask(__name__)
api = Api(app)


portrait_request_args = reqparse.RequestParser()
portrait_request_args.add_argument("image", type=FileStorage, help="Image with a portrait", required=False, location='files')
portrait_request_args.add_argument("base64_image", type=str, help="Base64 encoded image string", required=False, location='form')

@app.route("/docs")
def docs():
    return  f"""
        /portrait_extract/ 
    - Description: Extracts and processes portrait images.
    - Required Parameters (one of): 
        - image (file, optional): Image file containing the portrait
        - base64_image (string, optional): Base64 encoded image string
    - Responses: 
        - 200 OK: Successfully processed the image.
        - 400 Bad Request: No image uploaded or invalid image format."""
            

class Portrait(Resource):
    def get(self):
        return {"message": "This endpoint only accepts POST requests with images"}
                
    def put(self):
        return {"message": "This endpoint only accepts POST requests with images"}
      
    def delete(self):        
        return {"message": "This endpoint only accepts POST requests with images"}
    
    def post(self):
        try:
            args = portrait_request_args.parse_args()
            image_file = args['image']
            base64_image = args['base64_image']
            print(args)
            if not image_file and not base64_image:
                return {
                    "error": "No image data received",
                    "help": "Please send either an image file using the field name 'image' or a base64 encoded image string using 'base64_image'",
                }, 400

            if image_file:
                # Process file upload
                if not request.files:
                    return {
                        "error": "No files received",
                        "help": "Please send an image file using the field name image",
                        "logs": f"{request.files}"
                    }, 400

                received_fields = list(reqparse.request.files.keys())
                
                if 'image' not in received_fields:
                    return {
                        "error": "Image field image not found in request",
                        "received_fields": received_fields,
                        "help": "Please use image as the field name. Example: -F 'image=@your_image.jpg'"
                    }, 400                        
                
                image_file.seek(0)
                file_bytes = np.frombuffer(image_file.read(), np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                if image_file and image_file.filename.split('.')[-1].lower() not in ['png', 'jpg', 'jpeg']:
                    return {
                        "error": "Image field has unsupported image type",
                        "received_fields": received_fields,
                        "help": "Please use image type jpg, jpeg or png"
                    }, 400
            else:
                # Process base64 input
                try:
                    # Remove metadata if present
                    if ',' in base64_image:
                        base64_image = base64_image.split(',')[1]
                    
                    image_bytes = base64.b64decode(base64_image)
                    file_bytes = np.frombuffer(image_bytes, np.uint8)
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                except Exception as e:
                    return {
                        "error": "Invalid base64 image format",
                        "help": "Please provide a valid base64 encoded image string",
                        "details": str(e)
                    }, 400
            
            if image is None:
                return {
                    "error": "Image data is empty or invalid",
                    "help": "Please check the image data and try again"
                }, 400              
            
        except Exception as e:
            abort(500, message="Internal server error loading image: " + str(e))

        try:    
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            grayScale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            faces = face_cascade.detectMultiScale(
                grayScale,
                scaleFactor = 1.05,
                minNeighbors = 8,
                minSize = (25, 25)
            )
            
            if len(faces) == 0:
                return {
                    "error": "No portrait was detected in the image",
                    "help": "Please ensure the correct file was uploaded"
                }, 400             
            
            x, y, w, h = faces[0]
            
            padding = int(max(w, h) * 0.25)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(w + 2*padding, image.shape[1] - x)
            h = min(h + 2*padding, image.shape[0] - y)
            
            face_image = image[y:y+h, x:x+w]
            
            _, image_encoded = cv2.imencode('.png', face_image)
            image_base64 = base64.b64encode(image_encoded).decode('utf-8')
            
        except Exception as e:
            abort(500, message="Internal server error processing image: " + str(e)) 
                
        try:    
            if(app.debug):
                save_folder = 'rawdata'
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                
                with open(os.path.join(save_folder, 'img.out'), 'w') as image_file:
                    image_file.write(image_base64)

            return {"base64_image": image_base64, "single_portrait": len(faces)==1}
        except Exception as e:
            abort(500, message="Internal server error sending image: " + str(e)) 

api.add_resource(Portrait, "/portrait_extract/")
@app.route("/")
def index():
    return "For documentation go to /docs"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)