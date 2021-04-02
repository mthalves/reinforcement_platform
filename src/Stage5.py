import tkinter
from tkinter import *
from utils import *
from Screen import Screen
import numpy as np
import log
import utils


class Stage5(Screen):
	
	def __init__(self, master, prev_sc, main_bg):
    	# 1. Initializing the necessary variables
		# a. GUI variables
		super().__init__(master, prev_sc, main_bg,screen_name='Stage 5')
		self.init_variables()

		# b. reinforce vectors
		self.VR20_index = 0
		
		# 2. creating the result file
		log.create_file(self.nickname,self.group,self.stage,self.start_time)

		# a. interface components
		self.createButtons(self.center_h, self.center_w, self.radius)
		utils.ableButtonsAndMouse(self)

		# b. points counter
		self.createPointCounter()

		# c. sound effects
		self.load_sfx()

		self.reinforced_clicks = []
		self.reinforce_index = 0
		self.setReinforcedClicks()	

		# reseting the mouse
		if self.settings['return_click']:
			utils.reset_mouse_position(self)

		# d. auto-play
		if self.test:
			self.auto_play()
		else:
			print("Amigo estou aqui")

	def nextStage(self):
		txt = "| Going to Stage 6 Screen"
		print(txt)

		self.stage = 6
		from IntroStage import IntroStage
		IntroStage(self.master,self,self.main_bg)

	#check this function for other blocks (frequency is acumulating )
	def conditionalReinforce(self):
		# checking the reinforcement for group 1 [VR-20]
		if self.group == 1:
			current_click = sum(self.game[-1]['frequency'].values())
			if current_click > self.reinforced_clicks[-1]:
				self.setReinforcedClicks(offset=current_click-1)
				return (current_click in self.reinforced_clicks)
			else:
				return (current_click in self.reinforced_clicks)
		# checking the reinforcement for group 2 [VI (aco)]
		elif self.group == 2:
			time_vector_stage3 = np.cumsum([time.total_seconds() for g in self.game \
				if g['stage'] == self.game[-1]['stage'] for time in g['time2answer'] ])
			time2ans_cum = time_vector_stage3[-1] if len(time_vector_stage3) > 0 else 0
			time2ans_cum +=  (datetime.datetime.now() - self.round_start_time).total_seconds()

			# - checking the reinforce
			positive_reinforce = False
			if self.reinforce_index < len(self.reinforced_clicks):
				if self.reinforced_clicks[self.reinforce_index] <= time2ans_cum:
					while self.reinforce_index < len(self.reinforced_clicks) and \
					 self.reinforced_clicks[self.reinforce_index] <= time2ans_cum:
						self.reinforce_index += 1
					positive_reinforce = True

			# - checking the reinforce overlap
			while self.reinforce_index == len(self.reinforced_clicks):
				self.reinforce_index = 0
				self.setReinforcedClicks(offset=self.reinforce_clicks[-1])
				
				while self.reinforce_index < len(self.reinforced_clicks) and \
				self.reinforced_clicks[self.reinforce_index] <= time2ans_cum:
					self.reinforce_index += 1	

			return positive_reinforce
		# checking the reinforcement for group 3 [VR (aco)]
		else:
			if sum(self.game[-1]['frequency'].values()) > self.reinforced_clicks[-1]:
				self.setReinforcedClicks(sum(self.game[-1]['frequency'].values()))
				return False
			else:
				return (sum(self.game[-1]['frequency'].values()) in self.reinforced_clicks)

	# THE STAGE METHODS
	def check_stage_end_conditions(self): 
		# if the number of blocks is greather than the min of blocks
		# and the average IRT is less then the IRT threshold, finish the stage
		if self.number_of_blocks() >= self.settings['min_blocks']\
		and self.averageIRT() < self.settings['IRT_threshold']:
			return True
		# else keep playing
		return False

	def setReinforcedClicks(self,offset=0):
		print("Here")
		if self.group == 1: # applying the VR scheme [G1]
			if self.VR20_index == 0:
				self.VR20 = [[6, 3, 66, 12, 38, 9, 28, 1, 21, 16],[3, 12, 6, 66, 38, 28, 9, 1, 16, 21],\
					[1, 3, 6, 66, 21, 12, 38, 9, 16, 28],[3, 6, 66, 12, 9, 38, 28, 1, 21, 16]]

			self.reinforced_clicks = self.VR20[self.VR20_index]
			self.reinforced_clicks = np.array(np.cumsum(self.reinforced_clicks)) # accumulated sum of list VR5 without replacement
			self.reinforced_clicks += offset # addition of offset clicks
			self.VR20_index = (self.VR20_index+1) % 4

		else:
			# a. choosing the file to aco
			print('ACO FILE:',self.aco_file)
			
			# b. defining the reinforcement condition
			if self.group == 2: # applying the VI(aco) scheme [G2]
				counter, self.reinforced_clicks = 0, []
				with open("./results/"+self.aco_file) as ref_file:
					for line in ref_file:
						reinf_flag = line.split(';')[0]
						cum_time = line.split(';')[7]
						if counter != 0 and reinf_flag == 'SIM':
							self.reinforced_clicks.append(float(cum_time) + offset)
						counter += 1

			else: # applying the VR(aco) scheme [G3]
				counter, self.reinforced_clicks = 0, []
				with open("./results/"+self.aco_file) as ref_file:
					for line in ref_file:
						reinf_flag = line.split(';')[0]
						if counter != 0 and reinf_flag == 'SIM':
							self.reinforced_clicks.append(counter + offset)
						counter += 1