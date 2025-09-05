"""
序列化工具函數
處理 numpy/pandas 數據類型轉換為 Python 原生類型，確保可以被 JSON 序列化
"""
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def convert_numpy_types(obj: Any) -> Any:
    """
    遞歸轉換 numpy/pandas 數據類型為 Python 原生類型

    Args:
        obj: 要轉換的物件

    Returns:
        轉換後的物件，保證可以被 JSON 序列化
    """
    # ✅ 首先檢查基本 Python 類型，直接返回（避免被後續邏輯誤判）
    if isinstance(obj, int | float | str | bool) or obj is None:
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, np.integer | pd.Int64Dtype):
        return int(obj)
    elif isinstance(obj, np.floating | pd.Float64Dtype):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series | pd.Index):
        return [convert_numpy_types(x) for x in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'tolist') and hasattr(obj, '__len__'):
        # 處理其他 pandas/numpy 對象
        try:
            return [convert_numpy_types(x) for x in obj.tolist()]
        except (ValueError, TypeError):
            return str(obj)
    elif hasattr(obj, '__array__') and hasattr(obj, 'size'):
        # 處理 pandas/numpy 數組，避免布林值錯誤
        try:
            if obj.size == 1:
                return convert_numpy_types(obj.item())
            else:
                return [convert_numpy_types(x) for x in obj.tolist()]
        except (ValueError, AttributeError):
            return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list | tuple):
        return [convert_numpy_types(item) for item in obj]
    else:
        # ✅ 最後的處理邏輯
        try:
            # 檢查是否是 datetime-like 物件
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()

            # 檢查是否有 to_dict 方法 (Pydantic 模型)
            if hasattr(obj, 'model_dump'):
                return convert_numpy_types(obj.model_dump())
            elif hasattr(obj, 'dict'):
                return convert_numpy_types(obj.dict())

            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            else:
                # 對於無法處理的物件，保持原值
                return obj
        except (ValueError, TypeError, AttributeError):
            # 最後的兜底處理：保持原值
            return obj


def safe_dict_conversion(data: dict[str, Any]) -> dict[str, Any]:
    """
    安全地轉換字典中的所有值為可序列化的類型

    Args:
        data: 原始字典

    Returns:
        轉換後的字典
    """
    return convert_numpy_types(data)


def safe_sum(series: pd.Series) -> int | float:
    """
    安全地計算 pandas Series 的總和，處理 NaN 值

    Args:
        series: pandas Series

    Returns:
        總和的 Python 原生數值類型
    """
    try:
        # 先處理非數值數據
        numeric_series = pd.to_numeric(series, errors='coerce')
        result = numeric_series.sum()

        # 檢查是否為 NaN 或無效值
        if pd.isna(result) or not np.isfinite(result):
            return 0

        return convert_numpy_types(result)
    except Exception:
        return 0


def safe_mean(series: pd.Series) -> int | float:
    """
    安全地計算 pandas Series 的平均值，處理 NaN 值

    Args:
        series: pandas Series

    Returns:
        平均值的 Python 原生數值類型
    """
    try:
        # 先處理非數值數據
        numeric_series = pd.to_numeric(series, errors='coerce')
        result = numeric_series.mean()

        # 檢查是否為 NaN 或無效值
        if pd.isna(result) or not np.isfinite(result):
            return 0

        return convert_numpy_types(result)
    except Exception:
        return 0


def safe_count(series: pd.Series) -> int:
    """
    安全地計算 pandas Series 的非空值數量

    Args:
        series: pandas Series

    Returns:
        數量（整數）
    """
    try:
        return int(series.count())
    except Exception:
        return 0


def safe_nunique(series: pd.Series) -> int:
    """
    安全地計算 pandas Series 的唯一值數量

    Args:
        series: pandas Series

    Returns:
        唯一值數量（整數）
    """
    try:
        return int(series.nunique())
    except Exception:
        return 0


def safe_value_counts_dict(series: pd.Series, top_n: int = 5) -> dict[str, int]:
    """
    安全地獲取 pandas Series 的值計數字典

    Args:
        series: pandas Series
        top_n: 返回前 N 個最常見的值

    Returns:
        值計數字典
    """
    try:
        value_counts = series.value_counts().head(top_n)
        return {str(k): int(v) for k, v in value_counts.items()}
    except Exception:
        return {}


def safe_tolist(series: pd.Series, limit: int = 10) -> list[Any]:
    """
    安全地將 pandas Series 轉換為列表

    Args:
        series: pandas Series
        limit: 最大元素數量

    Returns:
        可序列化的列表
    """
    try:
        items = series.head(limit).tolist()
        return [convert_numpy_types(item) for item in items]
    except Exception:
        return []
