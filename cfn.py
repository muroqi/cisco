#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'Ryota Muroki'
__copylight__ = 'Copyright (c) 2016 Ryota Muroki'
__license__ = 'MIT'
__version__ = '0.0'

try:
	import json,re,requests,demjson
except Exception as e:
	print(e)
	exit(1)


# 不正なjsonデータをpython用に整形する関数
def json_py(url):
	try:
		r = requests.get(url).text
	except Exception as e:
		print(e)
		exit(1)
	return demjson.decode(r)

# 30行以上の出力を分けて表示する関数
def more(dict,sort_p):
	rows = 0
	times = 0
	if len(dict) == 0:
		print('\nNone. Try again. ')
		return 2
	else:
		print("")
		for key,value in sorted(dict.items(),key=lambda x:x[1][sort_p]):
			rows = rows + 1
			if(rows < 30): 
				print(str(key)+':\t'+value[1])
			else:
				times = times + 1
				# 30行出力後のメッセージ
				pause_msg = '\n-- More --(' + str(int(times*3000/len(dict))) + '%)  ("n" : Next, "q" : Quit) '
				while(1):
					res = input(pause_msg)
					print("")
					if res == 'n':
						rows = 0
						break
					elif res == 'q':
						return 0
					else:
						continue


# 辞書データを正規表現でフィルタする関数
def filter_dict(pattern,dct):
	return dict((k,dct[k]) for k in dct if re.search(pattern,dct[k][1],re.IGNORECASE))


# 機能ワードに対して機能一覧（キーが順序番号、値がリスト（機能番号、機能名））を返す関数
def feature_dict(f_word):
	fid = 0
	f_word = f_word.replace(' ','%20')
	f_url = 'http://tools.cisco.com/ITDIT/CFN/jsp/Feature.json?'
	try:
		json_data = requests.get(f_url + '&flttxt=' + f_word).json()
	except Exception as e:
		print(e)
		exit(1)
	for feature in json_data['featureList']['feature']:
		fid += 1
		f_dict[fid] = [feature['id'],feature['name']]
	return f_dict


# 機能番号に対して製品一覧（キーが順序番号、値がリスト(製品番号、値が製品名)）を返す関数
def platform_dict(fid):
	pid = 0
	p_url = 'http://tools.cisco.com/ITDIT/CFN/jsp/PlatformTree.json?'
	# p_urlは不正なjson形式を返すので、json_py関数を使う
	p = json_py(p_url + '&featIds=' + str(f_dict[fid][0]))
	p_lst = []
	for pi in p['children']:
		for pj in pi['children']:
			pid += 1
			p_dict[pid] = [int(pj['nid']),pj['nvalue']]
	return p_dict


# 機能番号、製品番号に対して機能、製品を満たすライセンス一覧を返す関数
def license_lst(fid,pid):
	lc_lst = []
	i_url = 'http://tools.cisco.com/ITDIT/CFN/jsp/Image.json?'
	try:
		s = requests.get(i_url + '&featIds=' + str(f_dict[fid][0]) + '&platformId=' + str(p_dict[pid][0])).json()
	except Exception as e:
		print(e)
		exit(1)
	for i in s['imageList']['image']:
		if re.search(r'CAT',i['featureSet']):
			continue
		elif re.search(r'ISR',i['featureSet']):
			continue
		else:
			lc_lst.append(i['featureSet'])
	lc_lst = sorted(list(set(lc_lst)))
	return lc_lst


# state : 機能キーワード検索時(初期値)は1, 機能番号検索時は2, 
#         製品番号検索時は3, サービス選択時は4
state = 1

while(1):
	if state == 1:
		f_word = input('\nInput feature word: ')
		# 終了・エスケープ・例外処理
		if f_word == 'end' or f_word == 'exit':
			exit(0)
		elif f_word == '':
			continue
		else:
			# 機能の辞書を出力
			f_dict = {}
			f_dict = feature_dict(f_word)
			if len(f_dict) == 0:
				print('\nNo features. Try again. ')
				continue
			# 追加入力で機能を絞り込み(正規表現可)
			pattern = input('\n' + str(len(f_dict)) + ' features found. Filter? (word) ')
			# 結果を表示(機能番号で昇順ソート)する
			if more(filter_dict(pattern,f_dict),0) == 2:
				continue
			# 正常出力ならstate 2へ移動
			else:
				state = 2
	
	elif state == 2:
		fid = input('\nInput feature number: ')
		# 終了・エスケープ・例外処理
		if fid == 'end':
			exit(0)
		elif fid == 'exit':
			state = 1
			continue
		elif fid == '':
			continue
		elif not(fid.isdigit()):
			print('\nError: Only number.')
			continue
		elif int(fid) not in f_dict:
			print('\nError: Input number not listed. Try again.')
			continue
		# 正常処理
		else:
			# 製品辞書を出力
			fid = int(fid)
			p_dict = {}
			p_dict = platform_dict(fid)
			# 追加入力で製品を絞り込み(正規表現可)
			pattern = input('\n' + str(len(p_dict)) + ' platforms found. Filter? (word) ')
			# 結果を表示(製品名で昇順ソート)する
			if more(filter_dict(pattern,p_dict),1) == 2:
				continue
			# 正常出力ならstate 3へ移動
			else:
				state = 3

	elif state == 3:
		pids = input('\nInput platform numbers: (CSV format) ')
		# pidsをリストに変換する
		pid_lst = pids.split(',')
		# 終了・エスケープ・例外処理
		again = 0
		for pid in pid_lst:
			if pid == 'end':
				exit(0)
			elif pid == 'exit':
				state = 2
				again = 1
			elif pid == '':
				print('\nError: Illegal syntax. Try again.')
				again = 1
			elif not(pid.isdigit()):
				print('\nError: Only number.')
				again = 1
			elif int(pid) not in p_dict:
				print('\nError: Input number not listed. Try again.')
				again = 1
		if again == 1:
			continue
		# 製品番号を整数へ変換
		pid_lst = map(int,pid_lst)
		# ライセンスリストを出力し、state 4へ移動
		delim1 = ' '
		delim2 = '-'
		output = "\n\n\n** " + f_dict[int(fid)][1] + " (" + str(fid) + ") **\n"
		output += "\n\nPlatform" + delim1*19 + "Feature Set/License/Supervisor(NX-OS)\n"
		output += delim2*22 + delim1*5 + delim2*50 + '\n'
		# 最初の製品idにフラグを立てる
		pid_flg = 1
		# ライセンスリストを出力
		for pid in pid_lst:
			# 最初のライセンスにフラグを立てる
			lic_flg = 1
			p_length = len(p_dict[pid][1])
			for lic in license_lst(fid,pid):
				# 最初の製品は改行なしで出力
				if pid_flg == 1 and lic_flg == 1:
					if(p_length < 25):
						output += p_dict[pid][1] + delim1*(27 - p_length) + lic + '\n'
					else:
						output += p_dict[pid][1][0:25] + delim1*2 + lic + '\n'
					# ライセンスのフラグを下げる
					lic_flg = 0
				# 2番目以降の製品は改行してから出力
				elif pid_flg == 0 and lic_flg == 1:
					if(p_length < 25):
						output += '\n' + p_dict[pid][1] + delim1*(27 - p_length) + lic + '\n'
					else:
						output += '\n' + p_dict[pid][1][0:25] + delim1*2 + lic + '\n'
					lic_flg = 0
				# 2番目以降のライセンスの出力
				else:
					output += delim1*27 + lic + '\n'
			# 製品idのフラグを下げる
			pid_flg = 0
		# 結果を出力
		print(output)
		# state 4へ移動
		state = 4
	
	elif state == 4:
		while(1):
			print('\n\n(1) Feature_word  (2) Feature_number  (3) Platform_number')
			req = input('Select number: ')
			# 各stateへ移動
			if req == '1':
				state = 1
				break
			elif req == '2':
				state = 2
				break
			elif req == '3' or req == 'exit':
				state = 3
				break
			# 終了・例外処理
			elif req == 'end':
				exit(0)
			else:
				continue
