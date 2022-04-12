import json
import argparse
import os
import re

class RecordExtractor:

	def __init__(self, metadata_directory):
		self.facct_dict = {}
		self.incoming_dict = {}
		self.outgoing_dict = {}
		self.metadata_directory = metadata_directory

	def findWord(w, ignore_case = False):
		if ignore_case:
			return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search	
		return re.compile(r'\b({0})\b'.format(w)).search


	def facct_from_json_single(self, metadata_json_path):
		metadata = []
		with open(metadata_json_path) as f_metadata:
			for record_str in f_metadata:
				metadata.append(json.loads(record_str))

		facct_dict_single = {}
		for record in metadata:
			hit = 0
			if record["venue"]:
				if findWord("FAT")(record["venue"]) or findWord("FAccT")(record["venue"]):
					hit = 1
				venue_lower = record["venue"].lower()
				if ("fairness" in venue_lower) and ("accountability" in venue_lower) and \
				   ("transparency" in venue_lower) and ("conference" in venue_lower):
				   	hit = 1
			if record["journal"]:
				if "FAT" in record["journal"] or "FAccT" in record["journal"]:
					hit = 1
				journal_lower = record["journal"].lower()
				if ("fairness" in journal_lower) and ("accountability" in journal_lower) and \
				   ("transparency" in journal_lower) and ("conference" in journal_lower):
				   	hit = 1

			if hit:
				facct_dict_single[record["paper_id"]] = record
		return facct_dict_single


	def facct_from_json_all(self):
		combined_dict = {}

		for i in range(100):
			print("Creating FAccT json, read {} files".format(i))
			metadata_json_path = os.path.join(self.metadata_directory, "metadata_{}.jsonl".format(i))
			facct_dict_single = self.facct_from_json_single(metadata_json_path)
			combined_dict.update(facct_dict_single)

		with open("facct.json", "w") as f_facct:
			json.dump(combined_dict, f_facct)

		self.facct_dict = combined_dict


	def incoming_from_json_single(self, metadata_json_path):
		"""
		Obtain records from a single json correspond to citations incoming to FAccT
		"""
		metadata = []
		with open(metadata_json_path) as f_metadata:
			for record_str in f_metadata:
				metadata.append(json.loads(record_str))

		incoming_dict_single = {}
		for record in metadata:
			if record["has_outbound_citations"]:
				# Potential incoming citations to FAccT will be outgoing in the referring paper 
				for out_cite in record["outbound_citations"]:
				# out_cite is a single outgoing reference (paper_id) from the current paper	
					if out_cite in self.facct_dict:
					# If out_cite is in facct_fict, this means the current paper cites some FAccT paper
						incoming_dict_single[record["paper_id"]] = record
						# In this case, we add it to the dictionary of incoming citations (to FAccT)
		return incoming_dict_single


	def incoming_from_json_all(self):
		combined_dict = {}

		for i in range(100):
			print("Creating incoming json, read {} files".format(i))
			metadata_json_path = os.path.join(self.metadata_directory, "metadata_{}.jsonl".format(i))
			incoming_dict_single = self.incoming_from_json_single(metadata_json_path)
			combined_dict.update(incoming_dict_single)

		with open("incoming.json", "w") as f_incoming:
			json.dump(combined_dict, f_incoming)

		self.incoming_dict = combined_dict


	def populate_outgoing_keys(self):
		self.outgoing_dict = {}
		for record in self.facct_dict:
			if record["has_outbound_citations"]:
				record_dict = dict.from_keys(record["outbound_citations"], 0)
				self.outgoing_dict.update(record_dict)


	def outgoing_from_json_single(self, metadata_json_path):
		metadata = []
		with open(metadata_json_path) as f_metadata:
			for record_str in f_metadata:
				metadata.append(json.loads(record_str))

		for record in metadata:
			if record["paper_id"] in self.outgoing_dict:
				self.outgoing_dict[record["paper_id"]] = record


	def outgoing_from_json_all(self):
		for i in range(100):
			print("Creating outgoing json, read {} files".format(i))
			metadata_json_path = os.path.join(self.metadata_directory, "metadata_{}.jsonl".format(i))
			self.outgoing_from_json_single(metadata_json_path)

		with open("outgoing.json", "w") as f_outgoing:
			json.dump(self.outgoing_dict, f_outgoing)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('jsonDirectory', type = str, help = "Path to the directory of S2ORC jsonl files")

	args = parser.parse_args()
	jsonDirectory = args.jsonDirectory

	re = RecordExtractor(jsonDirectory)
	re.facct_from_json_all()
	re.incoming_from_json_all()
	re.outgoing_from_json_all()
