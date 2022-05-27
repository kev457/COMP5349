# COMP5349
# How to Submit to EMR Cluster
1. Create an Amazon EMR 6.5.0 Cluster with Hadoop 3.2.1 and Spark 3.1.2 Application
2. Open the ssh to the server
3. Install git: sudo yum install git
4. Clone the repository: git clone https://github.com/kev457/COMP5349.git 
5. Download the test.json file to the root diretory by: aws s3 cp s3://comp5349-2022/test.json ./COMP5349/test.json
6. Put the data file on HDFS: 1. hdfs dfs -put ./COMP5349/test.json test.json 2. hdfs dfs -put ./COMP5349/a2_cluster.py a2_cluster.py 3. hdfs dfs -put ./COMP5349/a2.sh a2.sh
7. Go to the file direcotry: cd COMP5349
8. Enable the execute permission bit for the file owner of a2.sh: chmod 700 a2.sh
9. Run the Script: ./a2.sh
