import os
import cv2
import numpy as np 
import tensorflow as tf 

from dl.utils import _load_data
from dl.utils import _detect_lips
from dl.models import build_model
from tensorflow.keras.models import Model 

H, W, C = 32, 128, 3
model = build_model(input_shape=(H, W, C))
model.load_weights('dl/checkpoints/model.weights.hdf5')
model = Model(inputs=model.inputs[0], outputs=model.layers[-3].output)
print(model.summary())

'''
	Idea :
		+ Take all glossy images latent vectors
		+ Take all matte images  latent vectors
		+ average them out 
		+ when new image comes -> compare it to both mean vectors 
		+ whichever is closer will have glossy or matte class
'''

train_images, train_labels, test_images, test_labels = _load_data('dl/data', width=W, height=H)
# images = np.concatenate((train_images, test_images), axis=0)
# labels = np.concatenate((train_labels, test_labels), axis=0)

images = train_images
labels = train_labels
images_matte = images[np.array(np.argmax(labels, axis=1)) == 1]
images_gloss = images[np.array(np.argmax(labels, axis=1)) == 0]

embs_matte = model.predict(images_matte)
embs_gloss = model.predict(images_gloss)

embs_matte /= np.linalg.norm(embs_matte, axis=0)
embs_gloss /= np.linalg.norm(embs_gloss, axis=0)

mean_emb_matte = np.mean(embs_matte, axis=0)
mean_emb_gloss = np.mean(embs_gloss, axis=0)

def _recognize_lip(img):
	''' Input lip image '''
	global H, W, C 
	lips = _detect_lips(img)
	if(len(lips) > 0):
		print('Lip recognized')
		img = lips[0]

	img = cv2.resize(img, (W, H))
	img = (img - 127.5 ) / 127.5

	img = np.array([img])
	y = model.predict(img)[0]
	y = y / np.linalg.norm(y)

	dist_matte = np.sqrt(((y - mean_emb_matte) ** 2).sum())
	dist_gloss = np.sqrt(((y - mean_emb_gloss) ** 2).sum())

	if(dist_matte < dist_gloss):
		return 'matte'
	else:
		return 'glossy'


'''
img = cv2.imread('data/test/matte/7.jpeg')
label = _recognize_lip(img)
print(label)
'''