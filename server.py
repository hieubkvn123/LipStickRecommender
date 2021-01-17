import cv2
import json
import numpy as np

from PIL import Image
from dl.recognition import _recognize_lip
from utils import _detect_lip, _estimate_lip_color
from utils import _pairwise_color_distance, _get_color_distance
from argparse import ArgumentParser

from flask import Flask
from flask import request
from flask_cors import CORS

parser = ArgumentParser()
parser.add_argument('--debug', required=True, type=bool, help='Weather to run server in debug mode')
args = vars(parser.parse_args())

DEBUG = False
if(args['debug']):
    debug = True

app = Flask(__name__)
CORS(app)

### Read the colors chart in advance ###
color_chart_str = open('mac_matte.json', 'r').read().replace('\n','').replace('\t','')
color_chart = json.loads(color_chart_str)

def get_best_from_colorchart(lip_color, top_pick=2):
    distances = {}
    for color in color_chart:
        color_ = color['hex']
        b, g, r = hex2rgb(color_)
        distance = _pairwise_color_distance([b, g, r], lip_color)
        distances[color['hex']] = distance 

    ### Sort map by distance ###
    distances = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}
    keys = list(distances.keys())

    ### Final selection ###
    final = []
    for i in range(top_pick):
        data_item = {}
        data_item['color_code'] = keys[i].upper()
        for color in color_chart:
            if(color['hex'].upper() == data_item['color_code']):
                data_item['color_name'] = color['name'].upper()

        #final.append(keys[i])
        final.append(data_item)

    return final

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

        best_colors = get_best_from_colorchart(lip_color)
        response = {
            "lip_color" : {
                "B" : int(lip_color[0]),
                "G" : int(lip_color[1]),
                "R" : int(lip_color[2]),
                'HEX' : rgb2hex(lip_color).upper()
            },
            'lip_type' : lip_type.upper(),
            "recommendation" : data,
            "best_colors" : best_colors
        }

        return json.dumps(response)

if __name__ == '__main__':
    if(DEBUG):
        print('[INFO] Running in debugging mode ... ')
    else:
        print('[INFO] Running in deploying mode ... ')

    app.run(host='0.0.0.0', port=8080, debug=DEBUG)
