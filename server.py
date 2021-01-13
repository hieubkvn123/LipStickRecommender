import cv2
import json
import numpy as np

from PIL import Image
from dl.recognition import _recognize_lip
from utils import _detect_lip, _estimate_lip_color, _get_color_distance

from flask import Flask
from flask import request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def hex2rgb(color):
    if(color.startswith('#')):
        color = color[1:]

    r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    return b, g, r

def rgb2hex(color):
    b, g, r = color
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

@app.route('/test')
def test():
    return '<h1>API is working properly</h1>'

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        print(request.files)
        file_ = request.files['img']
        img = Image.open(file_).convert("RGB")
        img = np.array(img)
        
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img, lips, contours = _detect_lip(img)

        if(len(lips) == 0):
            return 'no_face_detected'
        elif(len(lips) > 1):
            return 'more_than_one_face_detected'

        for lip in lips:
            lip_color = _estimate_lip_color(lip)
            lip_type  = _recognize_lip(lip)
            # print(lip_color) - uploaded color
            data = _get_color_distance('products.csv', lip_color)
            # print(json.dumps(data, sort_keys=True, indent=4)) - list of recommendations

        response = {
            "lip_color" : {
                "B" : int(lip_color[0]),
                "G" : int(lip_color[1]),
                "R" : int(lip_color[2]),
                'HEX' : rgb2hex(lip_color).upper()
            },
            'lip_type' : lip_type.upper(),
            "recommendation" : data
        }

        return json.dumps(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
