import os
import re
import nltk
import string
import argparse
import collections
import xlsxwriter
import pandas as pd
from itertools import groupby
from collections import Counter
from nltk.corpus import stopwords

# python topic_words.py ../network_output
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key) 

def most_common_in_community(component_filepath):
	component_df = pd.read_csv(component_filepath)

	title_freq_list = list(zip(component_df.article_title, component_df.in_degree))
	title_freq_list_split = [list(group) for k, group in groupby(title_freq_list, lambda x: pd.isna(x[0])) if not k]

	stop_words = nltk.corpus.stopwords.words()

	result = []

	for community_index, community_list in enumerate(title_freq_list_split):	
		count_dict_weighted = {}
		count_dict_unweighted = {}
		for article_index, article_title_freq in enumerate(community_list):
			article_title = article_title_freq[0]
			article_freq = int(article_title_freq[1])
			title_string = article_title.translate(str.maketrans('', '', string.punctuation))
			title_words = [word for word in title_string.lower().split() if word not in stop_words]
			
			for word in title_words:
				if word not in count_dict_weighted:
					count_dict_weighted[word] = article_freq
				else:
					count_dict_weighted[word] += article_freq

			for word in title_words:
				if word not in count_dict_unweighted:
					count_dict_unweighted[word] = 1
				else:
					count_dict_unweighted[word] += 1


		counter_weighted = Counter(count_dict_weighted)
		common_weighted = counter_weighted.most_common(10)

		counter_unweighted = Counter(count_dict_unweighted)
		common_unweighted = counter_unweighted.most_common(10)

		freqstring_weighted = "\n".join([word_count[0] + ": " + str(word_count[1]) for word_count in common_weighted])
		freqstring_unweighted = "\n".join([word_count[0] + ": " + str(word_count[1]) for word_count in common_unweighted])

		result.append([freqstring_weighted, freqstring_unweighted])

	print (result)
	return result

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('clusterDirectory', type = str, help = "Path to the directory with the cluster CSVs")
	
	args = parser.parse_args()
	clusterDirectory = args.clusterDirectory

	workbook = xlsxwriter.Workbook('community_terms.xlsx')
	wrap_format = workbook.add_format({'text_wrap': True})

	community_files = natural_sort(os.listdir(clusterDirectory))
	community_files = [file for file in community_files if ("main" in file or "component" in file) and file[0] != '.']

	for file in community_files:
		print(file)
		worksheet = workbook.add_worksheet(file)
		component_filepath = os.path.join(clusterDirectory, file)
		"""
		component_df = pd.read_csv(component_filepath)

		title_list = [title if not pd.isna(title) else "" for title in component_df["article_title"]]
		title_list_community_split = [list(community) for k, community in groupby(title_list, bool) if k]

		for i, community_list in enumerate(title_list_community_split):	
			title_string = " ".join(community_list).lower()
			title_string = title_string.translate(str.maketrans('', '', string.punctuation))
			stop_words = nltk.corpus.stopwords.words()
			title_words = [word for word in title_string.lower().split() if word not in stop_words]
			
			common = Counter(title_words).most_common(10)

			freqstring = "\n".join([word_count[0] + ": " + str(word_count[1]) for word_count in common])

			worksheet.set_column('A:A', 15)
			worksheet.set_column('B:B', 25)
			worksheet.write('A1', "Community Id")
			worksheet.write('B1', "Frequent Title Unigrams [Unweighted]")
			worksheet.write(i + 1, 0, i)
			worksheet.write(i + 1, 1, freqstring, wrap_format)

		most_common_in_community(component_filepath)
		"""
		community_frequents = most_common_in_community(component_filepath)
		worksheet.set_column('A:A', 15)
		worksheet.set_column('B:B', 25)
		worksheet.set_column('C:C', 25)
		worksheet.write('A1', "Community Id")
		worksheet.write('B1', "Frequent Title Unigrams [Weighted]")
		worksheet.write('C1', "Frequent Title Unigrams [Unweighted]")
		for i in range(len(community_frequents)):
			worksheet.write(i + 1, 0, i)
			worksheet.write(i + 1, 1, community_frequents[i][0], wrap_format)
			worksheet.write(i + 1, 2, community_frequents[i][1], wrap_format)

	
	workbook.close()

if __name__ == '__main__':
	main()

