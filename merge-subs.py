#!/usr/bin/python3

#from __future__ import unicode_literals
import re
import copy
import sys
import argparse
import math

parser = argparse.ArgumentParser(description='Merge subtitles of different languages from youtube.')
argparse.version = '1.0'

parser.add_argument('paths',
                    action='store',
                    nargs=argparse.REMAINDER,
                    type=str,
                    help='Subtitles to be merged.'
)

args = parser.parse_args()

class Sub:
	def __init__(self, id, timestamp):
		self.timestamp = timestamp
		self.id = id
		self.langs = [[]]
		time = Sub.timestamp_to_seconds(timestamp)
		self.st = time[0]
		self.et = time[1]

	@staticmethod
	def time_to_string(x, n):
		if(x >= 10 ** (n-1)):
			return str(x)
		else:
			concat_string = ''
			for i in range(n-len(str(x))):
				concat_string += '0'
			return concat_string+str(x)

	@staticmethod
	def seconds_to_time(sec):
		sec = sec % (24 * 3600)
		hour = sec // 3600
		sec %= 3600
		min = sec // 60
		sec %= 60
		cs = sec % 1
		cs = round(cs, 3)
		sec = math.floor(sec)

		hour = Sub.time_to_string(round(hour), 2)
		min = Sub.time_to_string(round(min), 2)
		sec = Sub.time_to_string(round(sec), 2)
		cs = Sub.time_to_string(round(1000*cs), 3)

		return [hour, min, sec, cs]

	@staticmethod
	def seconds_to_timestamp(st, et):
		stl = Sub.seconds_to_time(st)
		etl = Sub.seconds_to_time(et)
		st_timestamp = stl[0]+':'+stl[1]+':'+stl[2]+'.'+stl[3]
		et_timestamp = etl[0]+':'+etl[1]+':'+etl[2]+'.'+etl[3]
		return st_timestamp+' --> '+et_timestamp

	@staticmethod
	def timestamp_to_seconds(timestamp):
		times = Sub.timestamp_to_time(timestamp)
		start_time = int(times[0][0])*60*60 + int(times[0][1])*60 + int(times[0][2]) + int(times[0][3]) / 1000
		end_time   = int(times[1][0])*60*60 + int(times[1][1])*60 + int(times[1][2]) + int(times[1][3]) / 1000
		return [start_time, end_time]

	@staticmethod
	def timestamp_to_time(timestamp):
		start_time = 0
		end_time   = 0
		start_timestamp = re.search('^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}', timestamp)
		end_timestamp   = re.search('[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}$', timestamp)

		stl = re.split('[:.]', start_timestamp.group())
		etl = re.split('[:.]', end_timestamp.group())

		return [stl, etl]

class MergeSubs:
	@staticmethod
	def merge_subs(sub_dics, threshhold):
		return_dic={
			'filename': sub_dics[0]['filename'],
			'header': sub_dics[0]['header'],
			'kind': sub_dics[0]['kind'],
			'language': '',
			'subs': [],
		}
		for sub_dic in sub_dics:
			is_first_sub_dic = (sub_dics.index(sub_dic) == 0)
			concat_strings = [[],[]]
			i = 0
			times = []
			if(not is_first_sub_dic):
				for sub_1 in sub_dics[0]['subs']:
					concat_strings[1] = []
					test = False
					for sub_2 in sub_dic['subs']:
						is_start_time_within_threshhold = sub_2.st-threshhold <= sub_1.st <= sub_2.st+threshhold
						is_end_time_within_threshhold = sub_2.et-threshhold <= sub_1.et <= sub_2.et+threshhold
						is_start_time_over_threshhold = sub_1.st <= sub_2.st+threshhold
						if(test == True):
							print('!!!ERROR!!!')
						if(is_start_time_over_threshhold):
							for string in sub_2.langs[0]:
								concat_strings[1].append(string)
						if(times != []):
							is_start_time_within_threshhold = sub_2.st-threshhold <= times[0] <= sub_2.st+threshhold
							is_end_time_within_threshhold = sub_2.et-threshhold <= sub_1.et <= sub_2.et+threshhold
							if(is_start_time_within_threshhold and is_start_time_within_threshhold):
								return_dic['subs'].append(Sub(i+1, Sub.seconds_to_timestamp(times[0], sub_1.et)))
								return_dic['subs'][i].langs.append([])
								for string in sub_1.langs[0]:
									concat_strings[0].append(string)
								for string in concat_strings[0]:
									return_dic['subs'][i].langs[0].append(string)
								concat_strings[0] = []
								times = []
								for string in sub_2.langs[0]:
									concat_strings[1].append(string)
								for string in concat_strings[1]:
									return_dic['subs'][i].langs[-1].append(string)
								i += 1
								break
						if(is_end_time_within_threshhold):
							index = sub_dics[0]['subs'].index(sub_1)
							return_dic['subs'].append(Sub(i+1, sub_1.timestamp))
							return_dic['subs'][i].langs.append([])
							for string in sub_1.langs[0]:
								return_dic['subs'][i].langs[0].append(string)
							for string in concat_strings[1]:
								return_dic['subs'][i].langs[-1].append(string)
							i += 1
							break
						if(sub_dic['subs'].index(sub_2) == len(sub_dic['subs'])-1):
							test = True
							for string in sub_1.langs[0]:
								concat_strings[0].append(string)
							times=[sub_1.st, sub_1.et]

		return return_dic

class ManipulateSubs:
	@staticmethod
	def parse_vtt(path):
		f = open(path, 'r')
		lines = f.readlines()
		subIndex=0
		path_without_extensions = re.search("^[^\.]*", path).group()
		filename = re.search('[^/]*$', path_without_extensions).group()
		sub_dic={
			'filename': filename,
			'header': '',
			'kind': '',
			'language': '',
			'subs': [],
		}

		for line in lines:
			timestamp_match=re.search("[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}", line)
			isTimeStamp = (timestamp_match == None)
			isHeader = subIndex == 0

			if(not isTimeStamp):
				subIndex = subIndex+1
				timestamp = timestamp_match.group()
				sub = Sub(subIndex, timestamp)

				sub_dic['subs'].append(sub)
			elif(not isHeader):
				sub_dic['subs'][subIndex-1].langs[0].append(line)
			else:
				header_match=re.search("WEBVTT", line)
				kind_match=re.search("Kind:", line)
				language_match=re.search("Language:", line)

				if(header_match!= None):
					sub_dic['header']=header_match.string
				if(kind_match!= None):
					sub_dic['kind']=kind_match.string
				if(language_match!= None):
					sub_dic['language']=language_match.string

		return(sub_dic)

	@staticmethod
	def create_concat_string(strings):
		concat_string = ''
		for string in strings:
			ends_on_special_char = re.search('[!?\.,:;"\(\)~]$', string)
			if(string != '\n'):
				if(ends_on_special_char == None):
					replace_newlines=re.sub('\n', ', ', string)
				else:
					replace_newlines=re.sub('\n', ' ', string)
				concat_string+=replace_newlines
		concat_string = concat_string.rstrip(' ,')
		concat_string = re.sub(' +', ' ', concat_string)

		return concat_string

	@staticmethod
	def write_lrc(sub_dic):
		f = open(sub_dic['filename']+'.lrc', 'w')
		seperator = '|'
		for sub in sub_dic['subs']:
			st = Sub.timestamp_to_time(sub.timestamp)[0]
			concat_string = ''
			for lang in sub.langs:
				concat_string += ManipulateSubs.create_concat_string(lang)+' '+seperator+' '
			concat_string = concat_string.rstrip(' '+seperator)

			f.write('['+str(st[1])+':'+str(st[2])+'.'+str(st[3])[:-1]+']'+concat_string+'\n')

	@staticmethod
	def write_srt(sub_dic):
		wf = open(sub_dic['filename']+'.srt', "w")

		for sub in sub_dic['subs']:
			wf.write(str(sub.id) + "\n")
			wf.write(sub.timestamp + "\n")
			for lang in sub.langs:
				concat_string = ManipulateSubs.create_concat_string(lang)
				wf.write(concat_string+'\n')
			wf.write('\n')

paths = args.paths
print(paths)
dics = []
for path in paths:
	dics.append(ManipulateSubs.parse_vtt(path))
dic3 = MergeSubs.merge_subs(dics, 0.75)
ManipulateSubs.write_lrc(dic3)
ManipulateSubs.write_srt(dic3)
