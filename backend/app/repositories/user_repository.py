"""
User repository with async Supabase operations.
Handles user data persistence and retrieval.
"""
import logging
from datetime import datetime
from uuid import UUID

from ..models.user import User, UserCreate, UserUpdate
from .supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class UserRepository(SupabaseRepository):
    """Repository for User entities with async Supabase client."""

    def __init__(self):
        super().__init__(table_name="users", model_class=User)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("email", email)
            result = await query.execute()

            data = self._handle_supabase_result(result, allow_empty=True, expect_single=True)

            if not data:
                return None

            return self.model_class(**data)

        except Exception as e:
            logger.error(f"Get by email failed: {e}")
            return None

    async def create_user(self, user_data: UserCreate, user_id: UUID) -> User:
        """Create a new user with proper validation."""
        try:
            existing_user = await self.get_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")

            user_dict = {
                "email": user_data.email,
                "full_name": user_data.full_name,
                "role": "user",
                "subscription_tier": "free",
                "is_active": True,
                "is_verified": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "total_queries": 0,
                "total_datasets": 0,
                "storage_used_mb": 0.0
            }

            return await super().create(user_dict, user_id=user_id)

        except Exception as e:
            logger.error(f"User creation failed: {e}")
            raise

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User | None:
        """Update user information."""
        try:
            update_data = user_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()

            return await super().update(user_id, update_data)

        except Exception as e:
            logger.error(f"User update failed: {e}")
            return None

    async def update_last_login(self, user_id: UUID) -> bool:
        """Update user's last login timestamp."""
        try:
            update_data = {
                "last_login_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = await super().update(user_id, update_data)
            return result is not None

        except Exception as e:
            logger.error(f"Last login update failed: {e}")
            return False

    async def update_usage_stats(
        self,
        user_id: UUID,
        query_increment: int = 0,
        dataset_increment: int = 0,
        storage_increment_mb: float = 0.0
    ) -> bool:
        """Update user usage statistics."""
        try:
            sql = """
            UPDATE users
            SET
                total_queries = total_queries + $1,
                total_datasets = total_datasets + $2,
                storage_used_mb = storage_used_mb + $3,
                updated_at = NOW()
            WHERE id = $4
            """

            await super().execute_sql(sql, [
                query_increment,
                dataset_increment,
                storage_increment_mb,
                str(user_id)
            ])

            return True

        except Exception as e:
            logger.error(f"Usage stats update failed: {e}")
            return False

    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user account."""
        try:
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = await super().update(user_id, update_data)
            return result is not None

        except Exception as e:
            logger.error(f"User deactivation failed: {e}")
            return False


# Global repository instance
user_repository = UserRepository()
