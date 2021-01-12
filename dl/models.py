import os
import numpy as np 
import tensorflow as tf 

from tensorflow.keras.layers import *
from tensorflow.keras import regularizers
from tensorflow.keras.models import Model 
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K

class AngularMarginPenalty(tf.keras.layers.Layer):
	def __init__(self, n_classes=10, input_dim=512):
		super(AngularMarginPenalty, self).__init__()    
		self.s = 30 # the radius of the hypersphere
		self.m1 = 1.0
		self.m2 = 0.0005
		self.m3 = 0.02
		self.n_classes=n_classes
		self.input_dim = input_dim
		self.w_init = tf.random_normal_initializer()

		self.W = self.add_weight(name='W',
		                    shape=(input_dim, self.n_classes),
		                    initializer='glorot_uniform',
		                    trainable=True,
		                    regularizer=None)
		b_init = tf.zeros_initializer()

		### For now we are not gonna use bias ###

	def call(self, inputs):
		x, y = inputs
		c = K.shape(x)[-1]
		### normalize feature ###
		x = tf.nn.l2_normalize(x, axis=1)

		### normalize weights ###
		W = tf.nn.l2_normalize(self.W, axis=0)

		### dot product / cosines of thetas ###
		logits = x @ W

		### add margin ###
		''' 
		in the paper we have theta + m but here I am just gonna decrease theta 
		this is because most theta are within [0,pi/2] - in the decreasing region of cosine func
		'''

		# clip logits to prevent zero division when backward
		theta = tf.acos(K.clip(logits, -1.0 + K.epsilon(), 1.0 - K.epsilon()))

		marginal_logit = tf.cos((tf.math.maximum(theta*self.m1 + self.m2, 0)))  - self.m3 
		logits = logits + (marginal_logit - logits) * y

		#logits = logits + tf.cos((theta * self.m)) * y
		# feature re-scale
		logits *= self.s
		out = tf.nn.softmax(logits)

		return out

	def get_config(self):
		config = super().get_config().copy()
		config.update({
			'n_classes' : self.n_classes,
			'input_dim' : self.input_dim
		})

		return config



class ConvBlock(object):
	def __init__(self, 
		out_channels,
		input_dim=(128,128,3), 
		pooling=True, 
		upsampling=0,
		use_selu=False,
		batch_norm=False,
		reg_lambda=2e-4):
		
		super(ConvBlock, self).__init__()
		self.input_dim=input_dim
		self.pooling=pooling
		self.upsampling=upsampling
		self.use_selu=use_selu
		self.batch_norm=batch_norm
		self.out_channels=out_channels
		self.reg_lambda=reg_lambda

	def build(self):
		kernel_size = (3,3)
		pool_size = (2,2)
		activation = 'relu'
		if(self.use_selu):
			activation = 'selu'

		inputs = Input(shape=self.input_dim)
		x = Conv2D(self.out_channels[0], 
			kernel_size=kernel_size, 
			activation=activation, 
			use_bias=False, padding='same',
			kernel_regularizer=regularizers.l2(l2=self.reg_lambda/2))(inputs)

		for i, channel in enumerate(self.out_channels[1:]):
			x = Conv2D(channel, kernel_size=kernel_size, 
				activation=activation, 
				use_bias=False, 
				padding='same',
				kernel_regularizer=regularizers.l2(l2=self.reg_lambda/2))(x)
			if(self.batch_norm):
				x = BatchNormalization()(x)

		output = x

		if(self.pooling):
			output = MaxPooling2D(pool_size=pool_size)(output)

		return Model(inputs = inputs, outputs=output)

def build_model(input_shape=(32, 128, 3)):
	inputs = Input(shape=input_shape)
	inputs2 = Input(shape=(2,))
	#out1 = ConvBlock([4, 4], input_dim=inputs.shape[1:], pooling=True, upsampling=0, use_selu=False, batch_norm=True).build()(inputs)
	#out2 = ConvBlock([8, 8], input_dim=out1.shape[1:], pooling=True, upsampling=0, use_selu=False, batch_norm=True).build()(out1)
	#out3 = ConvBlock([16, 16], input_dim=out2.shape[1:], pooling=True, upsampling=0, use_selu=False, batch_norm=True).build()(out2)
	#out4 = ConvBlock([16, 16], input_dim=out2.shape[1:], pooling=True, upsampling=0, use_selu=False, batch_norm=True).build()(out2)
	x = Conv2D(32, kernel_size=(3, 3), activation='relu')(inputs)
	x = MaxPooling2D(pool_size=(2, 2))(x)
	x = Conv2D(64, kernel_size=(3, 3), activation='relu')(x)
	x = MaxPooling2D(pool_size=(2, 2))(x)

	x = BatchNormalization()(x)
	x = Dropout(0.5)(x)
	x = Flatten()(x)
	x = Dense(512, kernel_initializer='he_normal')(x)
	x = BatchNormalization()(x)

	x = Flatten()(x)
	x = Dropout(0.5)(x)
	x = Dense(64)(x)
	x = AngularMarginPenalty(n_classes=2, input_dim=64)([x, inputs2])
	# x = Dense(2, activation='sigmoid')(x)

	model =	Model(inputs=[inputs, inputs2], outputs=x)
	print(model.summary())

	return model

# print(build_model().summary())
