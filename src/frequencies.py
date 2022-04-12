from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import argparse
import os

class MFDFrequencyExtractor:
	def __init__(self, dictionary_filepath):
		self.index_termList_dict, self.index_dimensionName_dict = self.read_dic(dictionary_filepath)

	def read_dic(self, dictionary_filepath):
		index_dimensionName_dict = {}
		index_termList_dict = {}
		with open(dictionary_filepath) as f:
			for line in f:
				if line[0].isdigit():
					index, dimension = line.strip("\n").split("\t")
					index_dimensionName_dict[int(index)] = dimension
					index_termList_dict[int(index)] = []
				if line[0].isalpha():
					term, labels = line.strip("\n").split("\t", 1)
					label_list = list(map(int, labels.split("\t")))
					for index in label_list:
						index_termList_dict[index].append(term)
		return (index_termList_dict, index_dimensionName_dict)

	def dimension_frequencies(self, year_directory_path, index, dimension):
		phrases = self.index_termList_dict[index]
		lens = [len(phrase.split()) for phrase in phrases]
		mn, mx = min(lens), max(lens)
		vect = CountVectorizer(vocabulary = phrases, ngram_range = (mn, mx))

		article_text_list = []
		for file in os.listdir(year_directory_path):
			f = open(os.path.join(year_directory_path, file))
			article_text = f.read()
			f.close()
			article_text_list.append(article_text)

		dtm = vect.fit_transform(article_text_list)
		df = pd.DataFrame(dtm.toarray(), columns = vect.get_feature_names()).T
		df.loc['Total',:]= df.sum(axis = 0)
		df.loc[:,'Total'] = df.sum(axis = 1)
		return df

	def mf_freqencies(self, excel_path, data_path):
		writer = pd.ExcelWriter(excel_path, engine = 'xlsxwriter')

		year_directory_path = data_path #change
		for index, dimension in self.index_dimensionName_dict.items():
			print (dimension)
			df = self.dimension_frequencies(year_directory_path, index, dimension)
			df.to_excel(writer, sheet_name = dimension)
			#writer.save()
		writer.close()

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--in", dest = 'dataDirectory', type = str, help = "Path to the data directory")
	parser.add_argument("--mfd", dest = 'mfd', type = str, help = "Path to the moral foundations dictionary")
	parser.add_argument("--out", dest = 'xlsxDirectory', type = str, help = "Path to the output directory")
	args = parser.parse_args()

	mfe = MFDFrequencyExtractor(args.mfd)
	mfe.mf_freqencies(args.xlsxDirectory, args.dataDirectory)


if __name__ == '__main__':
	main()
