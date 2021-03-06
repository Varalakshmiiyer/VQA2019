<!---
I'm providing a list of headers that the README MUST have below. You're free to add more content if you wish:
1. A brief abstract of your project including the problem statement and solution approach. If the project has cool visual results, you may provide one image or GIF of the results. See this for reference.
-->
# VQA : A CS763 Odyssey
## ABSTRACT
### Problem Statement
Given an input image and a question that can be answered by looking at the image.  
### Our Approach
Building on the idea of [this](https://arxiv.org/pdf/1708.02711.pdf) paper and [this](https://github.com/hengyuan-hu/bottom-up-attention-vqa) code, Our main expansion was following:
* Change the word embeddings used in the project to ELMO as the latter uses the semantics over a sentence and hence is a boost from earlier GloVe which is a simple word to vector mapping.
* Add an extra Square Distance loss in the training loop to output word embedding of answer which is then decoded back to word by another sister neural network which is a LSTM network taking word vector as input and characterwise predicts the output word corresponding to the embedding vector input.
* Add a side classifier which takes input the embedded form of question and outputs whether its a YES/NO type answerable question and if that is true, the whole search space of answer collapses to two and predicted word embedding should be near to true vector and farther from the false vector answer.


<!---
2. A list of code dependencies.
-->
## Code Dependencies

Please use Python2 for running this code
#### Packages required
* Cpickle
* torch
* numpy
* tensorboardX
* h5py


Make sure you are on a machine with a NVIDIA GPU with about 200 GB disk space and 16 GB RAM space.


<!---
3. Detailed instructions for running the code, preferably, command instructions that may reproduce the declared results. If your code requires a model that can't be provided on GitHub, store it somewhere else and provide a download link.
-->
## Setup
### Data Setup
All data should be downloaded to a 'data/' directory in the root
directory of this repository.

The easiest way to download the data is to run the provided script
`tools/download.sh` from the repository root. The features are
provided by and downloaded from the original authors'
[repo](https://github.com/peteanderson80/bottom-up-attention). Then run
`tools/process.sh` from the repository root to process the data to the
correct format.

### Training
Simply run `python2 main.py` to start training. The training and
validation scores will be printed every epoch, and the best model will
be saved under the directory "saved_models".  

Training vec2char is done as follows
```
cd vec2char
mkdir run
mkdir weights
python2 models.py
```


### Testing
Simply run `python2 test_main.py` for test and it will print the answer predicted and ground truth by using trained both models main and the side vec2char model.

<!---
4. Results: If numerical, mention them in tabular format. If visual, display. If you've done a great project, this is the area to show it!
-->
## Results
| Model | Validation Accuracy | HyperParameter tuned  
| --- | ----- | -- |
| Thier implementation| ~61 | Yes |  
| Elmo Embedding + MSE Loss | 58.47 | No |  
| ELMO + MSE + Binary classifier for Yes/No | 42.6 | No |  
<!---
* Running their tuned implementation ~61 
* Re-running their model after ELMO  embedding and adding MSE loss 58.47 *Hyper parameter untuned*
* Our latest model after adding additional classifier is not yet given any eval score. 
* vec2char model Good prediction for the dictionary of the words in VQA. 
![vec2char](https://github.com/aryanbdps9/VQA2019/blob/master/vec2char.png)
--->
### Note
* The accuracy was calculated using the [VQA evaluation metric](http://www.visualqa.org/evaluation.html), same as the base code used.
* For words not in Glove word dictionary, we replaced it with zero vector and hence in result for two word phrases, there is a consistent predication. 
<!---
5. Additional details, discussions, etc.
-->
## Additions Details
### Making the code running
Their provided implementation loaded all the data into the RAM which overflowed the RAM available to us. To make the code working, we modified the `__getitem__()` of dataset to be used by `nn.DataParallel` which loads the data whenever needed by the train function and hence started working with the limited RAM size available to us. Also as the data was available in `h5` format whose synchronous readers were not available for python2, we ended up making multiple calls of file opening and closing by each worker of `nn.DataParallel`. This again was a big setback in terms of running time of the program and we started doing multiple iteration over same data loaded before loading other batch of data.  
### Approaches Tried
* For Embedding to Char Network
  * Beam search over output of every step characater predicated. This approach had very bad gradient flow and ended up with model being almost untrained even after long runs of hours. Priority Queue was used for this part and even forced teacher training was tried.
  * Next was to keep the best prediction of every timestep of LSTM layer and but limiting the search space to top most frequent 1000 words. This was pretty sucessful but when extended to 4L words, the complete word dictionary size, this approach again failed. 
  * Pretrain model for 1000 word and then extend to 4L words to avoid the slowstart phase. This approach wasn't helpful either.
  * Extract the word dictionary from all words used in questions and answer of VQA dataset and learn this vector to word mapping over the dictionary size of ~3K
* Loading the data passed after ELMO embedding
  * For both the training data and validation data questions are separately passed through ELMO embedding and stored so that this extra pass over ELMO does not consume time over training of model which already was slow due to limited RAM and h5 being asynchronous.
* Final integration
  * Initially model trains over the data seperately. Model1 trying to predict embedding from question and image. Model2 predicting word from embedding.
  * Test time. Model1 first predicts whether it's a yes/no question or not. If yes, it uses it's own softmax which behaves as an custom embedding. For other cases, embedding predicted is passed to the trained Model2 for word prediction which is our final output answer



### Findings in VQAv2-dataset
* 40% of data has a Yes/No answer.
* 10% of data is labelled to have answer type of number but many of them are dates, part of address, other measurement answers and hence specifically working of these answers didn't seem much helpful
* 1% of yes/no answer is also corrupted but that instances are ignored during training and will be mispredicted by our model.

<!---
6. References.
-->
## Reference
1. [Tips and Tricks for Visual Question Answering:Learnings from the 2017 Challenge](https://arxiv.org/pdf/1708.02711.pdf)  
2. [A nice implementation of the above paper](https://github.com/hengyuan-hu/bottom-up-attention-vqa)










