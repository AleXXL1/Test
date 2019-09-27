"""
Библиотека рекомендательных систем Лаборатории по искусственному интеллекту
"""
from datetime import datetime
from typing import Tuple

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit
from pyspark.sql.types import TimestampType


class ValidationSchemes:
    """ различные методы разбиения на обучающую и тестовую выборки """

    def __init__(self, spark: SparkSession):
        """
        :param spark: сессия Spark, в рамках которой будет происходить
        обработка данных
        """
        self.spark = spark

    @staticmethod
    def _drop_cold_items(train: DataFrame, test: DataFrame) -> DataFrame:
        return test.join(
            train.select("item_id").distinct(),
            how="inner",
            on="item_id"
        )

    @staticmethod
    def _drop_cold_users(train: DataFrame, test: DataFrame) -> DataFrame:
        return test.join(
            train.select("user_id").distinct(),
            how="inner",
            on="user_id"
        )

    @staticmethod
    def log_split_by_date(
            log: DataFrame,
            test_start: datetime,
            drop_cold_items: bool,
            drop_cold_users: bool
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        разбить лог действий пользователей по дате на обучающую и тестовую
        выборки

        :param log: таблица с колонками
        (timestamp, user_id, item_id, context, relevance)
        :param test_start: дата в формате yyyy-mm-dd
        :param drop_cold_items: исключать ли из тестовой выборки объекты,
        которых нет в обучающей
        :param drop_cold_users: исключать ли из тестовой выборки пользователей,
        которых нет в обучающей
        :returns: тройка таблиц структуры, аналогичной входной
        (train, test_input, test)
        """
        train = log.filter(
            col("timestamp") < lit(test_start).cast(TimestampType())
        )
        test = log.filter(
            col("timestamp") >= lit(test_start).cast(TimestampType())
        )
        if drop_cold_items:
            test = ValidationSchemes._drop_cold_items(train, test)
        if drop_cold_users:
            test = ValidationSchemes._drop_cold_users(train, test)
        return train, train, test

    @staticmethod
    def log_split_randomly(
            log: DataFrame,
            test_size: float,
            drop_cold_items: bool,
            drop_cold_users: bool,
            seed: int = 1234
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        разбить лог действий пользователей рандомно на обучающую и тестовую
        выборки

        :param seed: рандомный сид, нужен для повторения разбиения
        :param test_size: размер тестовой выборки, от 0 до 1
        :param log: таблица с колонками
        (timestamp, user_id, item_id, context, relevance)
        :param drop_cold_items: исключать ли из тестовой выборки объекты,
        которых нет в обучающей
        :param drop_cold_users: исключать ли из тестовой выборки пользователей,
        которых нет в обучающей
        :returns: тройка таблиц структуры, аналогичной входной
        (train, test_input, test)
        """
        train, test = log.randomSplit([1 - test_size, test_size], seed)

        if drop_cold_items:
            test = ValidationSchemes._drop_cold_items(train, test)
        if drop_cold_users:
            test = ValidationSchemes._drop_cold_users(train, test)
        return train, train, test
