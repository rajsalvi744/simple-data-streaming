import logging
import time

from pyspark.sql.types import *
from pyspark.sql.functions import *


def create_keyspace(session):
    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS spark_streams WITH
    replication = {'class': 'SimpleStrategy','replication_factor': '1'};
    """)
    print("Keyspace Created Successfully")


def create_table(session):
    session.execute("""
    CREATE TABLE IF NOT EXISTS spark_streams.users(
    user_id UUID PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    date_of_birth TEXT,
    address TEXT,
    postcode TEXT,
    nationality TEXT,
    email TEXT,
    phone TEXT,
    username TEXT,
    photo TEXT);
    """)
    print("Table Created Successfully")


def create_spark_session():
    from pyspark.sql import SparkSession
    spark = None

    try:
        spark = (SparkSession.builder.appName("spark-stream")
                 .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0"
                                                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
                 .config("spark.cassandra.connection.host", "172.22.0.3")
                 .config("spark.cassandra.connection.port", "9042")
                 .getOrCreate())
        spark.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")

    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return spark


def create_cassandra_connection():
    cassandra_session = None
    from cassandra.cluster import Cluster
    try:
        cluster = Cluster(['172.22.0.3'], port=9042)
        cassandra_session = cluster.connect()

    except Exception as e:
        print(f"Could Not Create Cassandra Session: {e}")

    return cassandra_session


def connect_to_kafka(spark):
    spark_df = None

    try:
        spark_df = (spark.readStream
                    .format("kafka")
                    .option("kafka.bootstrap.servers", "broker:29092")
                    .option('subscribe', 'users_created')
                    .option("startingOffset", "earliest")
                    .load())
        logging.info("Kafka Dataframe Created Successfully")
    except Exception as e:
        logging.warning(f"Could Not Create Kafka Dataframe:{e}")

    return spark_df


def format_kafka_dataframe(spark_df):
    schema = StructType([
        StructField('user_id', StringType(), False),
        StructField('first_name', StringType(), False),
        StructField('last_name', StringType(), False),
        StructField('gender', StringType(), False),
        StructField('date_of_birth', StringType(), False),
        StructField('address', StringType(), False),
        StructField('postcode', StringType(), False),
        StructField('nationality', StringType(), False),
        StructField('email', StringType(), False),
        StructField('phone', StringType(), False),
        StructField('username', StringType(), False),
        StructField('photo', StringType(), False)
    ])
    spark_df = spark_df.selectExpr("CAST(value as STRING)").select(from_json(col('value'), schema).alias('data')) \
        .select("data.*")

    return spark_df


if __name__ == "__main__":

    spark = create_spark_session()

    if spark is not None:
        spark_df = connect_to_kafka(spark)
        spark_df = format_kafka_dataframe(spark_df)
        session = create_cassandra_connection()

        if session is not None:
            create_keyspace(session)
            create_table(session)

            logging.info("Streaming Is Being Started")

            streaming_query = (spark_df.writeStream
                               .format("org.apache.spark.sql.cassandra")
                               .option('keyspace', 'spark_streams')
                               .option('table', 'users')
                               .option('checkpointLocation', '/tmp/checkpoint')
                               .start())
            time.sleep(60)
            streaming_query.stop()
