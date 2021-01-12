import os
import cv2 
import json
import dlib
import requests
import imutils
import pandas as pd
import numpy as np

from imutils import face_utils
from PIL import Image

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

'''
    To estimate color : use HSV
    To compare colors : use LAB
'''

def _read_data(data_file, product_type, with_image=True):
    data = pd.read_csv(data_file, header=0)
    data['product_type'] = data['product_type'].astype(str).apply(lambda x : x.replace('\n', ''))

    ### Check if product type exists ###
    if(product_type not in np.unique(data['product_type'].values)):
        raise Exception('Product name does not exists') 

    chosen_product = data[data['product_type'] == product_type]
    if(with_image):
        chosen_product = chosen_product[chosen_product['img'].notnull()]

    return chosen_product

def _detect_lip(img, landmark_predictor_path='shape_predictor_68_face_landmarks.dat'):
    ''' Input : the original image '''
    detector  = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(landmark_predictor_path)

    rects = detector(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1)
    lips = []
    contours = []
    for (i, rect) in enumerate(rects):
        shape = predictor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), rect)
        shape = face_utils.shape_to_np(shape)
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()
        img = cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

        for (name, (x_, y_)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
            if(name == 'mouth'):
                x, y, w, h = cv2.boundingRect(np.array([shape[x_:y_]]))
                contour = cv2.convexHull(shape[x_:y_])
                roi = img[y:y+h, x:x+w]

                lips.append(roi)
                contours.append(contour)

    return img, lips, contours

def _estimate_lip_color(lip_img):
    ''' Input : the cropped lip region '''
    ### Easier to estimate color in HSV ###
    hsv = cv2.cvtColor(lip_img, cv2.COLOR_BGR2HSV)

    ### Range for lower red ###
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red, upper_red)

    ### Range for upper red ###
    lower_red = np.array([170, 120, 70])
    upper_red = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv, lower_red, upper_red)

    final = mask1 + mask2
    lip_img_copy = lip_img.copy()
    lip_img_copy[final == 0] = [0, 0, 0]

    ### Calculate color ###
    H, W = lip_img_copy.shape[:2]
    num_pixels = np.sum(final) / 255.0
    lip_color = lip_img_copy.reshape(H * W, 3).sum(axis=0)  / num_pixels
    lip_color = lip_color.astype(np.uint8)

    return lip_color
                
def _visualize(img):
    img, lips, contours = _detect_lip(img)
    _grid = len(lips)
    _size_w = 12
    _size_h = _grid * 4

    fig, ax = plt.subplots(_grid, 3, figsize=(_size_w, _size_h))
    for i, lip in enumerate(lips):
        lip_norm = lip / 255.0
        dist_mat = ((lip_norm - np.array([0.2, 0.2, 1.0])) ** 2).sum(axis=2)
        lip_seg, lip_color = _estimate_lip_color(lip)
        lip_color_img = np.zeros((50,50,3), dtype=np.uint8)
        lip_color_img[:] = lip_color

        lip = cv2.cvtColor(lip, cv2.COLOR_BGR2RGB)
        lip_seg = cv2.cvtColor(lip_seg, cv2.COLOR_BGR2RGB)
        lip_color_img = cv2.cvtColor(lip_color_img, cv2.COLOR_BGR2RGB)
        
        if(len(lips) > 1):
            ax[i][0].imshow(lip)
            ax[i][1].imshow(lip_seg)
            ax[i][2].imshow(lip_color_img)
        else:
            ax[0].imshow(lip)
            ax[1].imshow(lip_seg)
            ax[2].imshow(lip_color_img)

    plt.show()

# _visualize(cv2.imread('data/chi6.jpeg'))
def _get_lipstick_color(path):
    img = None
    try:
        img = Image.open(requests.get(path, stream=True).raw)
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    except:
        print('[INFO] Failed reading image at %s ' % path)

    if(img is None):
        return img

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    ### Range for lower red ###
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red, upper_red)

    ### Range for upper red ###
    lower_red = np.array([170, 120, 70])
    upper_red = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv, lower_red, upper_red)

    final = mask1 + mask2
    lip_img_copy = img.copy()
    lip_img_copy[final == 0] = [0, 0, 0]

    ### Calculate color ###
    H, W = lip_img_copy.shape[:2]
    num_pixels = np.sum(final) / 255.0
    lip_color = lip_img_copy.reshape(H * W, 3).sum(axis=0)  / num_pixels
    lip_color = lip_color.astype(np.uint8)
    
    return lip_color

def _get_color_distance(data_file, color, output_file_path='data.json', top_pick=5):
    ### Compare one color with every colors ###
    data = None
    original_color = np.array([[color]]).astype('uint8')
    original_color = cv2.cvtColor(original_color, cv2.COLOR_BGR2LAB)
    if(os.path.exists(output_file_path)):
        print('[INFO] Data file exists ...')
        data = json.load(open(output_file_path, 'r'))
    else:
        products = _read_data('products.csv', 'Lipstick', with_image=True)
        products = products[['img', 'brand', 'name']].values
        data = []
        for i, item in enumerate(products):
            path, brand, name = item
            data_item = {}
            lip_color = _get_lipstick_color(path)
            
            if(lip_color is None):
                continue 
            
            data_item['B'] = int(lip_color[0])
            data_item['G'] = int(lip_color[1])
            data_item['R'] = int(lip_color[2])
            data_item['url'] = path
            data_item['brand'] = brand
            data_item['name'] = name
            print(data_item)
            data.append(data_item)
        
        output_file = open(output_file_path, 'w')
        json.dump(data, output_file, indent=4)

    ### Comparing the colors ###
    distance_map = {}
    for i, data_item in enumerate(data):
        bgr_color = np.array([[[data_item['B'], data_item['G'], data_item['R']]]]).astype('uint8')
        bgr_color = cv2.cvtColor(bgr_color, cv2.COLOR_BGR2LAB)
        distance = np.sqrt((bgr_color - original_color) ** 2)
        distance_map[i] = distance.sum()

    ### Sort map by distance ###
    distance_map = {k: v for k, v in sorted(distance_map.items(), key=lambda item: item[1])}
    keys = list(distance_map.keys())

    ### Final selection ###
    final = []
    for i in range(top_pick):
        final.append(data[keys[i]])
    
    return final

''' Sample programme '''
'''
image = cv2.imread('data/chi4.jpeg')
image, lips, contours = _detect_lip(image)

for lip in lips:
    lip_color = _estimate_lip_color(lip)
    print(lip_color)
    data = _get_color_distance('products.csv', lip_color)
    print(json.dumps(data, sort_keys=True, indent=4))
'''
