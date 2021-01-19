#from __future__ import unicode_literals
import re
import copy
import youtube_dl
import sys
import argparse
import math

parser = argparse.ArgumentParser(description='Merge subtitles of different languages from youtube.')
argparse.version = '1.0'

parser.add_argument('-r',
                    '--remove-japanese-lines',
                    action='store_true',
                    help='Removes any lines containing japanese characters.'
)
parser.add_argument('yt_url',
                    metavar='yt-url',
                    action='store',
                    type=str,
                    help='The youtube hyperlink from which the subtitles will be downloaded and merged from.'
)
parser.add_argument('export_format',
                    metavar='export-format',
                    action='store',
                    type=str,
                    help='Specifies the output format. Valid values are srt and lrc.'
)
parser.add_argument('languages',
                    action='store',
                    nargs=argparse.REMAINDER,
                    type=str,
                    help='Languages which are to be downloaded.'
)

args = parser.parse_args()

class Sub:
	def __init__(self, id, timestamp):
		self.timestamp = timestamp
		self.id = id
		self.langs = [[]]
		time = ConvertSubs.timestamp_to_seconds(timestamp)
		self.st = time[0]
		self.et = time[1]

	def appendString(self, string):
		self.strings.append(string)

class ConvertSubs:
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

		hour = ConvertSubs.time_to_string(round(hour), 2)
		min = ConvertSubs.time_to_string(round(min), 2)
		sec = ConvertSubs.time_to_string(round(sec), 2)
		cs = ConvertSubs.time_to_string(round(1000*cs), 3)

		return [hour, min, sec, cs]

	@staticmethod
	def seconds_to_timestamp(st, et):
		stl = ConvertSubs.seconds_to_time(st)
		etl = ConvertSubs.seconds_to_time(et)
		st_timestamp = stl[0]+':'+stl[1]+':'+stl[2]+'.'+stl[3]
		et_timestamp = etl[0]+':'+etl[1]+':'+etl[2]+'.'+etl[3]
		return st_timestamp+' --> '+et_timestamp

	@staticmethod
	def timestamp_to_seconds(timestamp):
		times = ConvertSubs.timestamp_to_time(timestamp)
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

#	@staticmethod
#	def merge_subs(sub_dics, threshhold):
#		return_dic = copy.deepcopy(sub_dics[0])
#		return_dic['language'] = ''
#		for sub_dic in sub_dics:
#			is_first_sub_dic = (sub_dics.index(sub_dic) == 0)
#			return_dic['subs']
#			concat_strings = [[],[]]
#			temp_times = [[-200, -200],[-200,-200]]
#			if(not is_first_sub_dic):
#				for sub_1 in sub_dics[0]['subs']:
#					if(concat_strings[1] != []):
#						if(concat_strings[0] == []):
#							temp_times[0] = [sub_1.st, sub_1.et]
#						for string in sub_1.langs[0]:
#							concat_strings[0].append(string)
#					concat_strings[1] = []
#					for sub_2 in sub_dic['subs']:
#						i = 0
#						is_start_time_within_threshhold = sub_2.st-threshhold <= sub_1.st <= sub_2.st+threshhold
#						is_end_time_within_threshhold = sub_2.et-threshhold <= sub_1.et <= sub_2.et+threshhold
#						is_start_time_over_threshhold = sub_1.st <= sub_2.st+threshhold
#						if(is_start_time_over_threshhold):
#							if(temp_times[1] == [-200,-200]):
#								temp_times[1] = [sub_2.st, sub_2.et]
#							for string in sub_2.langs[0]:
#								concat_strings[1].append(string)
#						print(temp_times)
#						if(is_end_time_within_threshhold):
#							print('sub_2.st: '+str(sub_2.st))
#							print('temp_times[1][0]: '+str(temp_times[1][0]))
#							if(sub_2.st-threshhold <= temp_times[1][0] <= sub_2.st+threshhold):
#								print('PASS')
#								temp_times[1] = [-200, -200]
#								index = sub_dics[0]['subs'].index(sub_1)
#								return_dic['subs'][index].langs.append([])
#								for string in concat_strings[1]:
#									return_dic['subs'][index].langs[-1].append(string)
#								break
#						if(sub_dic['subs'].index(sub_2) == len(sub_dic['subs'])-1):
#							print('ERROR')
#							temp_times[1] = [-200, -200]
#						else:
#							i += 1
#		return return_dic

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
							print(str(i)+': C')
							for string in sub_2.langs[0]:
								concat_strings[1].append(string)
						if(times != []):
							print(str(i)+': A')
							is_start_time_within_threshhold = sub_2.st-threshhold <= times[0] <= sub_2.st+threshhold
							is_end_time_within_threshhold = sub_2.et-threshhold <= sub_1.et <= sub_2.et+threshhold
							#print('sub1_langs[0]:')
							#print(sub_1.langs[0])
							#print('concatstrings[0]:')
							#print(concat_strings[0])
							#print('concatstrings[1]:')
							#print(concat_strings[1])
							#print(str(sub_2.st-threshhold)+' <= '+str(times[0])+' <= '+str(sub_2.st+threshhold))
							#print(str(sub_2.et-threshhold)+' <= '+str(sub_1.et)+' <= '+str(sub_2.et+threshhold))
							if(is_start_time_within_threshhold and is_start_time_within_threshhold):
								print(str(i)+': B')
								return_dic['subs'].append(Sub(i+1, ConvertSubs.seconds_to_timestamp(times[0], sub_1.et)))
								print(ConvertSubs.seconds_to_timestamp(times[0], sub_1.et))
								print(times[0])
								print(sub_1.et)
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
							print(str(i)+': D')
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
							print(str(i)+': E')
							print()
							test = True
							for string in sub_1.langs[0]:
								concat_strings[0].append(string)
							times=[sub_1.st, sub_1.et]

		return return_dic

#	@staticmethod
#	def merge_subs(sub_dics, threshhold):
#		return_dic = copy.deepcopy(sub_dics[0])
#		for sub_1 in return_dic['subs']:
#			for sub_dic in sub_dics:
#				is_first_sub_dic = (sub_dics.index(sub_dic) == 0)
#				if(not is_first_sub_dic):
#					i = 0
#					append_strings = []
#					print(len(sub_1.langs))
#					sub_1.langs.append([])
#					for sub_2 in sub_dic['subs']:
#						times_1 = ConvertSubs.timestamp_to_seconds(sub_1.timestamp)
#						times_2 = ConvertSubs.timestamp_to_seconds(sub_2.timestamp)
#						is_start_time_over_threshhold = times_1[0] <= times_2[0]+threshhold
#						is_end_time_within_threshhold = times_2[1]-threshhold <= times_1[1] <= times_2[1]+threshhold
#						if(is_start_time_over_threshhold):
#							for string in sub_2.langs[0]:
#								append_strings.append(string)
#						if(is_end_time_within_threshhold):
#							for string in append_strings:
#								sub_1.langs[-1].append(string)
#							break
#						if(i >= len(sub_dics[1]['subs'])):
#							print('ERROR')
#						else:
#							i += 1
#		return return_dic
#
	@staticmethod
	def vtt_to_sub_dic(path):
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
	def create_concat_string_lrc(strings):
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
			st = ConvertSubs.timestamp_to_time(sub.timestamp)[0]
			concat_string = ''
			for lang in sub.langs:
				concat_string += ConvertSubs.create_concat_string_lrc(lang)+' '+seperator+' '
			concat_string = concat_string.rstrip(' '+seperator)

			f.write('['+str(st[1])+':'+str(st[2])+'.'+str(st[3])[:-1]+']'+concat_string+'\n')

	@staticmethod
	def write_srt(sub_dic):
		wf = open(sub_dic['filename']+'.srt', "w")

		for sub in sub_dic['subs']:
			wf.write(str(sub.id) + "\n")
			wf.write(sub.timestamp + "\n")
			for lang in sub.langs:
				concat_string = ConvertSubs.create_concat_string_lrc(lang)
				wf.write(concat_string+'\n')
			wf.write('\n')

	@staticmethod
	def remove_japanese_lines(sub_dic):
		return_sub_dic = copy.deepcopy(sub_dic)
		for sub in return_sub_dic['subs']:
			for lang in sub.langs:
				for string in lang:
					x = re.search('([\u3040-\u309f]|[\u30a0-\u30ff]|[\u2e80-\u2fd5]|[\u4e00-\u9fbf]|[\uff5f-\uff9f]|[\u3000-\u303f])', string)
					if(x!=None):
						lang.remove(string)

		return return_sub_dic

	@staticmethod
	def ydl(url, langs):
		ydl_opts = {
			'outtmpl': '/tmp/%(title)s.%(ext)s',
			'writesubtitles': True,
			'skip_download': True,
			'subtitleslangs': langs,
		}

		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
			info_dict = ydl.extract_info(url, download=False)
			video_title = info_dict.get('title', None).replace('/', '_')

		return_paths = []
		for lang in langs:
			return_paths.append('/tmp/'+video_title+'.'+lang+'.vtt')

		return return_paths

url = args.yt_url
langs = args.languages

paths = ConvertSubs.ydl(url, langs)
dics = []
for path in paths:
	dics.append(ConvertSubs.vtt_to_sub_dic(path))
dic3 = ConvertSubs.merge_subs(dics, 0.75)
if(args.remove_japanese_lines):
	dic3 = ConvertSubs.remove_japanese_lines(dic3)
ConvertSubs.write_lrc(dics[1])
ConvertSubs.write_srt(dic3)

