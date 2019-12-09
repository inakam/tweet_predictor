python tweet_get.py
python rand_split.py
./fasttext supervised -input tweet_data/tweet_data_train.txt -output result/alpha_tweet -dim 10 -lr 0.1 -wordNgrams 2 -minCount 1 -bucket 10000000 -epoch 100 -thread 4
./fasttext test result/alpha_tweet.bin tweet_data/tweet_data_test.txt