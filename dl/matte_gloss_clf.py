import os
import numpy as np 
import tensorflow as tf 

from tensorflow.keras.layers import *
from tensorflow.keras.models import Model 
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint

from utils import _load_data
from models import build_model

checkpoint_path = 'checkpoints/model.weights.hdf5'
H, W, C = 32, 128, 3
train_images, train_labels, test_images, test_labels = _load_data('data', width=W, height=H)
model = build_model(input_shape=(H, W, C))

### Check if the checkpoint dir is there ###
checkpoint_dir = os.path.dirname(checkpoint_path)
if(not os.path.exists(checkpoint_dir)): 
	print('[INFO] Creating checkpoint directory...')
	os.mkdir(checkpoint_dir)

ckpt = ModelCheckpoint(checkpoint_path, save_best_only=True, verbose=1)

print(train_labels.shape)
if(os.path.exists(checkpoint_path)):
	print('[INFO] Loading checkpoint ... ')
	model.load_weights(checkpoint_path)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit([train_images, train_labels],train_labels,  
	epochs=100, 
	validation_data=([test_images, test_labels], test_labels), 
	shuffle=True, 
	callbacks=[ckpt])