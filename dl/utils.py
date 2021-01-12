import os
import cv2
import numpy as np 

from sklearn.preprocessing import LabelEncoder

detector = cv2.CascadeClassifier('dl/haarcascade_mcs_mouth.xml')
# detector = cv2.CascadeClassifier('haarcascade_mcs_mouth.xml')
def _detect_lips(img):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	mouth_rects = detector.detectMultiScale(gray, 2.0, 17)

	lips = []
	for (x, y, w, h) in mouth_rects:
		lip = img[y:y+h, x:x+w]
		lips.append(lip)

	return lips 

'''
img = cv2.imread('data/train/glossy/14.jpeg')
lips = _detect_lips(img)

for i, lip in enumerate(lips):
	cv2.imshow("Lip #%d" % i, lip)

key = cv2.waitKey(0)
if(key == ord('q')):
	cv2.destroyAllWindows()
'''
def _load_data(data_dir, width=128, height=32):
	test_path = os.path.join(data_dir, 'test')
	train_path = os.path.join(data_dir, 'train')

	if(not os.path.exists(train_path) or not os.path.exists(test_path)):
		raise Exception('Training or testing dataset missing...')

	train_images = []
	train_labels = []
	### Load training data ###
	for (dir_, dirs, files) in os.walk(train_path):
		for file_ in files:
			abs_path = os.path.join(dir_, file_)
			image = cv2.imread(abs_path)

			lip_img = image
			lips = _detect_lips(image)
			if(len(lips) > 0):
				lip_img = lips[0]

			label = abs_path.split('/')[-2]

			lip_img = cv2.resize(lip_img, (width, height))
			train_images.append(lip_img)
			if(label == 'matte'):
				train_labels.append([0, 1])
			else:
				train_labels.append([1, 0])

	test_images = []
	test_labels = []
	### Load testing data ###
	for (dir_, dirs, files) in os.walk(test_path):
		for file_ in files:
			abs_path = os.path.join(dir_, file_)
			image = cv2.imread(abs_path)

			lip_img = image
			lips = _detect_lips(image)
			if(len(lips) > 0):
				lip_img = lips[0]

			label = abs_path.split('/')[-2]

			lip_img = cv2.resize(lip_img, (width, height))
			test_images.append(lip_img)
			if(label == 'matte'):
				test_labels.append([0, 1])
			else:
				test_labels.append([1, 0])

	test_images = (np.array(test_images, dtype=np.float32) - 127.5) / 127.5
	train_images = (np.array(train_images, dtype=np.float32) - 127.5) /127.5

	test_labels = np.array(test_labels)
	train_labels = np.array(train_labels)

	return train_images, train_labels, test_images, test_labels
