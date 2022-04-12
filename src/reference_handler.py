import re
import pandas as pd
import os
import argparse
from pathlib import Path

class Reference:
	#id = 0
	def __init__(self, reference_string, conference_year):
		self.article_title = self.authorlist_str = self.venue = self.year = ""

		if conference_year != 2018:
			reference_elements = [element.strip() for element in re.split("([0-9]+[-]?[0-9]*?\. )", reference_string, maxsplit = 1)]
			#print(reference_string)
			#print(reference_elements)
			
			if len(reference_elements) == 3:
				reference_elements[2] = Reference.strip_string(reference_elements[2])
				if '.' in reference_elements[2]:
					self.article_title, self.venue = reference_elements[2].split(".", 1)
				else:
					self.article_title = reference_elements[2]
				self.authorlist_str = reference_elements[0]
				self.year = reference_elements[1]

			elif len(reference_elements) == 2:
				self.article_title = reference_elements[0]
				self.year = reference_elements[1]
			else:
				self.article_title = reference_elements[0]

		else:
			reference_elements = [element.strip() for element in re.split("\.", reference_string, 2)]
			
			if len(reference_elements) == 3:
				reference_elements[2] = Reference.strip_string(reference_elements[2])
				self.authorlist_str = reference_elements[0]
				self.article_title = reference_elements[1]
				self.venue = reference_elements[2]

			elif len(reference_elements) == 2:
				self.authorlist_str = reference_elements[0]
				self.article_title = reference_elements[1]
			else:
				self.article_title = reference_elements[0]
			self.year = re.search("[ \n][0-9]{4}[^0-9:–]|$", reference_string).group(0)[:5]

		self.article_title = Reference.strip_string(self.article_title)
		self.authorlist_str = Reference.strip_string(self.authorlist_str)
		self.venue = Reference.strip_string(self.venue)
		self.year = Reference.strip_string(self.year)


	@staticmethod
	def strip_string(string):
		to_remove = [' ', '.']
		begin = end = 0
		for index, char in enumerate(string):
			if char not in to_remove:
				begin = index
				break
		for index, char in enumerate(reversed(string)):
			if char not in to_remove:
				end = index
				break
		stripped_string = string[begin:len(string) - end]
		return stripped_string


	def get_reference_as_list(self):
		return list([self.authorlist_str, self.article_title, self.venue, self.year])


def generate_dataframe(inputDirectory, year, combined_df, i):
		reference_list = []
		df = pd.DataFrame(columns = combined_df.columns)
		
		for file in os.listdir(inputDirectory):
			filepath = os.path.join(inputDirectory, file)
			f = open(filepath, mode = 'r', newline = '')
			article_text = f.read()	
			f.close()
			
			if year != 2018:
				# Extracting the References section of the article and removing line breaks
				try:
					reference_split = re.split("References\n\[[0-9]*\]", article_text, flags = re.IGNORECASE)[1].replace("-\n", "").replace("\n"," ")
				except IndexError:
					print ("REFERENCES not found in", file)
					continue

				# Splitting the References section into a list (of strings) of references using the reference format that starts with "[NUMBER]"
				reference_text_list = list(map(str.strip, re.split("\[[0-9]*\]", reference_split)))

			else:
				# Extracting the References section of the article and removing line breaks
				try:
					reference_split = article_text.split("References")[1].replace("-\n", "").replace("\n"," ")
				except IndexError:
					print ("References not found in", file)
					continue

				# Splitting the References section into a list (of strings) of references using the reference format that starts with "[NUMBER]"
				reference_text_list = list(map(str.strip, re.split("\*\*", reference_split)))
				#print (reference_text_list)

			# Removing empty strings from the reference list
			reference_text_list = list(filter(None, reference_text_list))

			# Generating list of Reference objects
			reference_object_list = list(map(lambda ref_str: Reference(ref_str, year), reference_text_list))

			article_title = file
			reference_list_list = list(map(lambda ref: ref.get_reference_as_list(), reference_object_list))
			for reference in reference_list_list:
				reference.insert(0, article_title) 
				reference.insert(0, i)
			#print(reference_list_list)

			df_temp = pd.DataFrame(reference_list_list, columns = df.columns)
			#print(df.columns)
			df = df.append(df_temp)

			i += 1

		return (df, i)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--in", dest = 'inputDirectory', type = str, help = "Path to the input directory")
	parser.add_argument("--out", dest = 'outputDirectory', type = str, help = "Path to the output directory")
	args = parser.parse_args()
	
	#year = args.year
	inputDirectory = args.inputDirectory
	outputDirectory = args.outputDirectory

	combined_df = pd.DataFrame(columns = ["Id", "Source Article", "Authors", "Referenced Article", "Venue", "Year"])

	index = 0
	for year in range(2018, 2021):
		directory = os.path.join(inputDirectory, str(year))
		print (directory)
		df, index = generate_dataframe(directory, year, combined_df, index)
		#print(df)
		combined_df = combined_df.append(df)
	

	if not os.path.exists(outputDirectory):
		os.makedirs(outputDirectory)
	out_file_name = "combined.csv"
	combined_df.to_csv(os.path.join(outputDirectory, out_file_name))