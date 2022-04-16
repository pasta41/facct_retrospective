# Topic Modeling 

As discussed in the paper (Section 3.2), we use the python wrapper for the Java MALLET library to perform Latent Direchlet Allocation (LDA) in order to produce our topic model. We chose this tool because MALLET implements Gibbs-sampling-based LDA, which has been observed to produced better results on small-text corpora like the one we have used in this project in comparison to tools like gensim, which use variational inference.

## Dependencies
- python >=3.7
- [little-mallet-wrapper](https://github.com/maria-antoniak/little-mallet-wrapper) for generating the topic model. Please refer to the README in this repository for how to install the wrapper and necessary dependencies (including MALLET installation and setup, which requires a Java SDK installation)
- [pandas](https://pandas.pydata.org/) and [numpy](https://numpy.org/) for data manipulation
- [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/) for generating the heatmaps
- [jupyter notebooks](https://jupyter.org/)

## Summary of files in this directory
- ``explore_topics.ipynb``: The code to replicate our experiments
- ``ouput``: The directory used by ``explore_topics.ipynb`` to store the trained LDA model outputs. The exact model we reported in the paper can be found here (and loaded up to regenerate the figures we provide in Section 3.2). We have also included additional figures (e.g., per-paper topic distribution heatmaps) in this directory.
- ``txt_cleaning_tracker.csv``: A file that documents per-paper changes we made during the data cleaning process in order to improve the quality of our topic model

## Generating the paper's LDA heatmaps
We have provided a documented [jupyter notebook](https://jupyter.org/) for easy replication.  After downloading the necessary dependencies, run ``jupyter notebook explore_topics.ipynb`` to run through our experimental procedure, line-by-line. 

One can walk through the notebook to regenerate the topic model from scratch, or one look to the bottom of the notebook for how to form the figures (and additional heatmaps that contain per-paper topic distributions) from the exact model that we report in the paper. This latter-half of the notebook loads up this saved model (from the ``output`` directory) to generate the figures.

## Data cleanup log
In order to perform LDA, we needed to clean up and tokenize the corpus of FAccT papers. Our cleanup procedure is documented in the jupyter notebook discussed above. We include a file that tracks the changes made to clean up the corpus (e.g., removing math symbols, re-joining words that have been hyphenated for line-breaks in the PDFs of papers, etc...). Please refer to ``txt_cleaning_tracker.csv`` for per-paper details.

