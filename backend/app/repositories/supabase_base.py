"""
Supabase Repository 基類
遵循 CLAUDE.md 中的 Repository Layer 規範
"""
import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from supabase import AsyncClient

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SupabaseRepository(Generic[T]):
    """
    Supabase Repository 基類

    遵循 CLAUDE.md 規範：
    - MUST inherit from SupabaseRepository base class
    - MUST use _handle_supabase_result() for ALL query results
    - NEVER access result.data directly (bypasses error handling)
    - ALWAYS use base class CRUD methods (self.create(), self.get(), etc.)
    """

    def __init__(self, table_name: str, model_class: type[T]):
        self.table_name = table_name
        self.model_class = model_class
        self._client: AsyncClient | None = None

    async def get_client(self) -> AsyncClient:
        """取得 Async Supabase 客戶端"""
        if not self._client:
            from app.core.database import db_manager
            self._client = await db_manager.get_client()
            if not self._client:
                raise Exception("無法取得 Supabase 客戶端 - 請檢查設定")
        return self._client

    def _handle_supabase_result(
        self,
        result,
        allow_empty: bool = False,
        expect_single: bool = False,
        is_rpc_call: bool = False
    ) -> Any:
        """
        處理 Supabase 查詢結果 - 統一錯誤處理

        CRITICAL: 所有查詢都必須使用此方法處理結果
        NEVER access result.data directly
        """
        try:
            # 檢查是否有錯誤
            if hasattr(result, 'error') and result.error:
                error_msg = str(result.error)
                logger.error(f"Supabase 查詢錯誤: {error_msg}")
                raise Exception(f"資料庫查詢失敗: {error_msg}")

            # 處理資料
            data = getattr(result, 'data', None)

            # ✅ 增強 RPC 呼叫的結果處理
            if is_rpc_call:

                # 處理 RPC 錯誤情況
                if isinstance(data, dict):
                    if 'message' in data and 'JSON could not be generated' in str(data.get('message', '')):
                        # 檢查是否為成功的 SQL 執行
                        details = str(data.get('details', ''))
                        if 'SQL executed successfully' in details or 'rows affected' in details.lower():
                            logger.info("RPC SQL 執行成功（JSON 解析問題）")
                            return {'success': True, 'message': 'SQL executed successfully', 'details': details}
                        else:
                            # 真正的 SQL 錯誤
                            raise Exception(f"RPC SQL 執行失敗: {data.get('message', 'Unknown RPC error')}")

                    # 正常的 RPC 結果（dict 格式）
                    return data

                elif isinstance(data, list):
                    # 正常的 RPC 結果（list 格式）
                    return data

                # 空的 RPC 結果
                if data is None:
                    return {'success': True, 'rows_affected': 0}

            # 檢查空結果
            if data is None or (isinstance(data, list) and len(data) == 0):
                if allow_empty:
                    return [] if isinstance(data, list) else None
                else:
                    raise Exception("查詢未返回資料")

            # 檢查單筆結果
            if expect_single:
                if isinstance(data, list):
                    if len(data) != 1:
                        raise Exception(f"期望單筆結果，但返回了 {len(data)} 筆")
                    return data[0]
                return data

            return data

        except Exception as e:
            logger.error(f"處理 Supabase 結果失敗: {e}")
            logger.error(f"原始 result: {result}")
            logger.error(f"result 類型: {type(result)}")
            if hasattr(result, '__dict__'):
                logger.error(f"result 屬性: {result.__dict__}")
            raise Exception(f"處理 Supabase 結果失敗: {str(e)}") from e

    def _build_models(self, data_list: list[dict[str, Any]]) -> list[T]:
        """將資料庫記錄轉換為模型列表"""
        try:
            if not data_list:
                return []

            models = []
            for item in data_list:
                if self.model_class == dict:
                    models.append(item)
                else:
                    models.append(self.model_class(**item))

            return models

        except Exception as e:
            logger.error(f"轉換模型失敗: {e}")
            raise

    async def create(self, obj_in: dict[str, Any], user_id: UUID | None = None) -> T:
        """
        建立記錄 - 使用基類方法確保錯誤處理

        Args:
            obj_in: 要插入的資料
            user_id: 用戶 ID（用於 RLS）

        Returns:
            建立的模型實例
        """
        try:
            # 如果有 user_id，加入資料中
            if user_id:
                obj_in = {**obj_in, 'user_id': str(user_id)}

            client = await self.get_client()
            result = await client.from_(self.table_name).insert(obj_in).execute()

            # 使用統一錯誤處理
            data = self._handle_supabase_result(result, expect_single=True)

            # 轉換為模型
            if self.model_class == dict:
                return data
            else:
                return self.model_class(**data)

        except Exception as e:
            logger.error(f"建立記錄失敗 ({self.table_name}): {e}")
            raise

    async def get(self, record_id: UUID, user_id: UUID | None = None) -> T | None:
        """
        根據 ID 取得記錄

        Args:
            record_id: 記錄 ID
            user_id: 用戶 ID（用於 RLS）

        Returns:
            模型實例或 None
        """
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("id", str(record_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            result = await query.execute()

            # 使用統一錯誤處理，允許空結果
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            # 取第一筆結果
            first_record = data[0] if isinstance(data, list) else data

            if self.model_class == dict:
                return first_record
            else:
                return self.model_class(**first_record)

        except Exception as e:
            logger.error(f"取得記錄失敗 ({self.table_name}): {e}")
            raise

    async def get_many(
        self,
        filters: dict[str, Any] | None = None,
        user_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[T]:
        """
        取得多筆記錄

        Args:
            filters: 篩選條件
            user_id: 用戶 ID（用於 RLS）
            limit: 限制筆數
            offset: 偏移量

        Returns:
            模型實例列表
        """
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*")

            # 應用 RLS
            if user_id:
                query = query.eq("user_id", str(user_id))

            # 應用篩選條件
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # 應用分頁
            if limit > 0:
                query = query.range(offset, offset + limit - 1)

            result = await query.execute()

            # 使用統一錯誤處理
            data = self._handle_supabase_result(result, allow_empty=True)

            return self._build_models(data)

        except Exception as e:
            logger.error(f"取得多筆記錄失敗 ({self.table_name}): {e}")
            raise

    async def update(
        self,
        record_id: UUID,
        obj_in: dict[str, Any],
        user_id: UUID | None = None
    ) -> T | None:
        """
        更新記錄

        Args:
            record_id: 記錄 ID
            obj_in: 更新資料
            user_id: 用戶 ID（用於 RLS）

        Returns:
            更新後的模型實例或 None
        """
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).update(obj_in).eq("id", str(record_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            result = await query.execute()

            # 使用統一錯誤處理
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            # 取第一筆結果
            first_record = data[0] if isinstance(data, list) else data

            if self.model_class == dict:
                return first_record
            else:
                return self.model_class(**first_record)

        except Exception as e:
            logger.error(f"更新記錄失敗 ({self.table_name}): {e}")
            raise

    async def delete(self, record_id: UUID, user_id: UUID | None = None) -> bool:
        """
        刪除記錄

        Args:
            record_id: 記錄 ID
            user_id: 用戶 ID（用於 RLS）

        Returns:
            是否成功刪除
        """
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).delete().eq("id", str(record_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            result = await query.execute()

            # 使用統一錯誤處理
            self._handle_supabase_result(result, allow_empty=True)

            return True

        except Exception as e:
            logger.error(f"刪除記錄失敗 ({self.table_name}): {e}")
            return False

    async def count(
        self,
        filters: dict[str, Any] | None = None,
        user_id: UUID | None = None
    ) -> int:
        """
        計算記錄數量

        Args:
            filters: 篩選條件
            user_id: 用戶 ID（用於 RLS）

        Returns:
            記錄數量
        """
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*", count="exact")

            # 應用 RLS
            if user_id:
                query = query.eq("user_id", str(user_id))

            # 應用篩選條件
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            result = await query.execute()

            # 直接返回 count，不需要處理 data
            return getattr(result, 'count', 0) or 0

        except Exception as e:
            logger.error(f"計算記錄數量失敗 ({self.table_name}): {e}")
            return 0

    async def execute_sql(self, sql: str, params: list[Any] | None = None) -> Any:
        """
        執行原始 SQL - 統一的 SQL 執行方法

        Args:
            sql: SQL 查詢
            params: SQL 參數

        Returns:
            查詢結果
        """
        try:
            client = await self.get_client()
            logger.info(f"執行 SQL: {sql[:100]}..." + (f" 參數: {params}" if params else ""))

            # ✅ 改為使用更強健的 RPC 函數呼叫
            if params and len(params) > 0:
                result = await client.rpc('execute_sql_for_etl', {
                    'sql_query': sql,
                    'param_value': str(params[0])
                }).execute()
            else:
                result = await client.rpc('execute_sql_for_etl', {
                    'sql_query': sql
                }).execute()

            # ✅ MUST use _handle_supabase_result for all queries with RPC flag
            processed_result = self._handle_supabase_result(result, allow_empty=True, is_rpc_call=True)
            logger.info(f"SQL 執行成功，返回結果類型: {type(processed_result)}")
            return processed_result

        except Exception as e:
            # ✅ 增強錯誤處理和日誌記錄
            error_str = str(e)
            logger.error(f"SQL 執行錯誤: {error_str}")
            logger.error(f"SQL 內容: {sql}")

            # 特殊處理 Supabase RPC 的已知問題
            if 'JSON could not be generated' in error_str:
                if 'SQL executed successfully' in error_str:
                    logger.warning("RPC JSON 解析失敗，但 SQL 執行成功")
                    return {'success': True, 'message': 'SQL executed successfully', 'rows_affected': 0}
                else:
                    logger.error("RPC JSON 解析失敗且 SQL 執行也失敗")
                    raise Exception(f"SQL 執行失敗: JSON 解析錯誤 - {error_str}")

            # 其他類型的錯誤直接拰出
            raise Exception(f"SQL 執行失敗: {error_str}") from e

    async def batch_insert(self, records: list[dict[str, Any]]) -> list[T]:
        """
        批次插入記錄

        Args:
            records: 要插入的記錄列表

        Returns:
            插入的模型實例列表
        """
        try:
            client = await self.get_client()
            result = await client.from_(self.table_name).insert(records).execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result)

            return self._build_models(data)

        except Exception as e:
            logger.error(f"批次插入失敗 ({self.table_name}): {e}")
            raise
