# -*- coding: utf-8 -*-
"""A2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VjjSvRCFvuFyq8qYqn0SNHwdkxiVR7GB
"""

#!pip install pyspark

#from google.colab import drive
#drive.mount('/content/drive')

from pyspark.sql import SparkSession
spark = SparkSession \
    .builder \
    .appName("COMP5349 A2") \
    .getOrCreate()

test_data = "test.json"
test_init_df = spark.read.json(test_data)
#train_data = "/Assignment_2_data/train_separate_questions.json"
#train_init_df = spark.read.json(train_data)
#all_data = "/Assignment_2_data/CUADv1.json"
#all_init_df = spark.read.json(all_data)

test_init_df.printSchema()

from pyspark.sql.functions import explode
test_data_df= test_init_df.select((explode("data").alias('data')))
test_paragraph_df = test_data_df.select(explode("data.paragraphs").alias("paragraph"))
qas_context_df = test_paragraph_df.select(explode("paragraph.qas").alias("qas"),"paragraph.context")
df1 = qas_context_df.withColumnRenamed("paragraph.context","context")
df = df1.select('qas.id','context','qas.question',explode("qas.answers").alias("answers"),'qas.is_impossible')

df.show()
df2 = df.withColumnRenamed("qas.id","id")
df3 = df2.withColumnRenamed("qas.question","question")
df4 = df3.withColumnRenamed("qas.is_impossible","is_impossible")
exploded_df  =  df4.select('id','context', 'question', "answers.answer_start","answers.text",'is_impossible')
exploded_df.collect()[100]

exploded_df.show()

def extraction(row):
  #Get the category name from the id, last element split by '_'
  category = row[0].split('_')[-1]

  context  = row[1]

  question  = row[2]

  answer_start = row[3]
  answer = row[4]
  if answer == None:
    answer_start = 0
    answer_end = 0
  else:
    answer_end = answer_start + len(answer)
  #contract segment
  slide = 4096
  stride = 2048
  context_len = len(context)
  if context_len%stride==0:
    seq_len = context_len/stride
  else:
    seq_len = context_len//stride + 1
  seq = []
  for i in range(seq_len):
    #(context[0:4096],0)(context[2048:6144],2048)..
    seq.append([context[i*stride:i*stride+slide],i*stride])

  


  is_impossible = row[5]

  return(category, question, answer, answer_start, answer_end, is_impossible,seq)

extracted_df = exploded_df.rdd.map(extraction)

extracted_df.take(5)

def expand(row):
  for i in row[6]:
    return ((row[0],row[1],row[2],row[3],row[4],row[5]),i)

extracted_df1 = extracted_df.map(expand)

extracted_df1.take(10)

# step 2

def categorize(row):
  is_impossible = row[0][-1]

  if is_impossible == True:
    return(row[0][0],'impossible negative'),(row[1][0],row[0][1],row[0][2],0,0)
  else:
    answer_start = row[0][3]
    answer_end = row[0][4]
    seq_start = row[1][1]

    if answer_start - seq_start >=0 and answer_end - seq_start <=4096:
      return(row[0][0],'positive'),(row[1][0],row[0][1],row[0][2],answer_start - seq_start,answer_end - seq_start)
    else:
      return(row[0][0],'possible negative'),(row[1][0],row[0][1],row[0][2],0,0)

labelled_df = extracted_df1.map(categorize)

labelled_df.take(5)

# For an impossible question in a contract, the number of impossible negative samples
# to keep equals the average number of positive samples of that question in other
# contracts that have at least one positive sample for the same question.

# For each contract, the number of possible negative samples to keep for each question
# equals the number of positive samples of that question in this contract.

count = labelled_df.countByKey()

def countPos(row):
  label = row[0][1]
  if label == 'positive':
    id = row[0][0]
    question = row[1][1]
    return((question,id),label)


pos_count = labelled_df.map(countPos).filter(lambda x: x is not None).groupByKey().mapValues(list).map(lambda x: (x[0],len(x[1]))).collect()
print(pos_count)

def balanceResult(row):
  num_of_positive = count[row[0][0],"positive"]
  label = row[0][1]
  
  if label == 'possible negative':
    return row[0],row[1][:num_of_positive]
  elif label == 'impossible negative':
    question = row[1][2]
    id = row[0][0]
    total = []
    for i in pos_count:
      if i[0][0] == question and i[0][1]!=id:
        total.append(i[1])
    average = round(sum(total) / len(total))
    return row[0],row[1][:average]
  else:
    return row





group_key_df= labelled_df.groupByKey().mapValues(list).map(balanceResult).filter(lambda x: x is not None)
group_key_df.take(10)

# def getFinal(row):
#   for content in row[1]:
#     return (content[0],content[1],content[3],content[4])

final = group_key_df.flatMap(lambda x : x[1]).map(lambda x:(x[0],x[1],x[3],x[4])).toDF(["source", "question", "answer_start", "answer_end"])

final.printSchema()
final.show()
final.write.mode("Overwrite").json("output.json")



