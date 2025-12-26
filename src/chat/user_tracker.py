"""
User Tracker Module
Handles user registration, activation, and usage analytics
"""
import psycopg2
from datetime import datetime
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()


class UserTracker:
    """Track Telegram user activity and manage access control"""
    
    def __init__(self):
        """Initialize user tracker with database connection"""
        # Get database credentials
        db_url = os.getenv('DATABASE_URL')
        
        if not db_url:
            # Construct from individual variables
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            
            if not all([db_name, db_user, db_password]):
                raise ValueError("Database credentials not configured")
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.db_url = db_url
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    # ========================================================================
    # User Registration & Management
    # ========================================================================
    
    def register_user(self, user_id: int, username: str = None, 
                     first_name: str = None, last_name: str = None,
                     is_active: bool = False) -> bool:
        """
        Register new user (inactive by default, requires admin approval)
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            is_active: Whether user is active (default: False)
            
        Returns:
            True if registered successfully
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO telegram_users 
                            (user_id, username, first_name, last_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET 
                            username = EXCLUDED.username,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            last_seen = NOW()
                    """, (user_id, username, first_name, last_name, is_active))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    def is_user_active(self, user_id: int) -> bool:
        """
        Check if user is active (approved)
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is active
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT is_active 
                        FROM telegram_users 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    row = cur.fetchone()
                    return row[0] if row else False
        except Exception as e:
            print(f"Error checking user status: {e}")
            return False
    
    def activate_user(self, user_id: int) -> bool:
        """
        Activate user (admin approval)
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if activated successfully
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE telegram_users 
                        SET is_active = true,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error activating user: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user (revoke access)
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if deactivated successfully
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE telegram_users 
                        SET is_active = false,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    def get_pending_users(self) -> List[Dict]:
        """
        Get list of users awaiting approval
        
        Returns:
            List of pending user dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, username, first_name, last_name, first_seen
                        FROM telegram_users 
                        WHERE is_active = false
                        ORDER BY first_seen DESC
                    """)
                    
                    users = []
                    for row in cur.fetchall():
                        users.append({
                            'user_id': row[0],
                            'username': row[1] or 'N/A',
                            'name': f"{row[2]} {row[3] or ''}".strip(),
                            'first_seen': row[4]
                        })
                    return users
        except Exception as e:
            print(f"Error getting pending users: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """
        Get list of all users (active and inactive)
        
        Returns:
            List of all user dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, username, first_name, last_name, is_active, first_seen, last_seen
                        FROM telegram_users 
                        ORDER BY first_seen DESC
                    """)
                    
                    users = []
                    for row in cur.fetchall():
                        users.append({
                            'user_id': row[0],
                            'username': row[1] or 'N/A',
                            'name': f"{row[2]} {row[3] or ''}".strip(),
                            'is_active': row[4],
                            'first_seen': row[5],
                            'last_seen': row[6]
                        })
                    return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    # ========================================================================
    # Usage Logging
    # ========================================================================
    
    def log_query(self, user_id: int, query_type: str, query_text: str,
                  response_time_ms: int, success: bool = True, 
                  error_message: str = None, username: str = None) -> bool:
        """
        Log user query for analytics
        
        Args:
            user_id: Telegram user ID
            query_type: Type of query ('screen', 'analyze', 'chat', 'market')
            query_text: The query text
            response_time_ms: Response time in milliseconds
            success: Whether query succeeded
            error_message: Error message if failed
            username: Telegram username (optional)
            
        Returns:
            True if logged successfully
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_queries 
                            (user_id, query_type, query_text, response_time_ms, 
                             success, error_message, username)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, query_type, query_text, response_time_ms, 
                          success, error_message, username))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error logging query: {e}")
            return False
    
    # ========================================================================
    # Analytics
    # ========================================================================
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """
        Get user statistics
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user stats or None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Refresh materialized view first
                    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats")
                    
                    cur.execute("""
                        SELECT 
                            total_queries,
                            screen_queries,
                            analyze_queries,
                            chat_queries,
                            avg_response_time,
                            failed_queries,
                            last_query_time
                        FROM user_stats
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    row = cur.fetchone()
                    if row:
                        return {
                            'total_queries': row[0],
                            'screen_queries': row[1],
                            'analyze_queries': row[2],
                            'chat_queries': row[3],
                            'avg_response_time': row[4],
                            'failed_queries': row[5],
                            'last_query_time': row[6]
                        }
                    return None
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None
    
    def get_daily_active_users(self, days: int = 1) -> int:
        """
        Get count of active users in last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Count of active users
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT get_daily_active_users(%s)
                    """, (days,))
                    
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting daily active users: {e}")
            return 0
    
    def check_rate_limit(self, user_id: int, max_per_hour: int = 20) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: Telegram user ID
            max_per_hour: Maximum queries per hour
            
        Returns:
            True if user is within rate limit
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT get_user_hourly_queries(%s)
                    """, (user_id,))
                    
                    count = cur.fetchone()[0]
                    return count < max_per_hour
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """
        Get user information
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user info or None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            user_id,
                            username,
                            first_name,
                            last_name,
                            is_active,
                            first_seen,
                            last_seen
                        FROM telegram_users
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    row = cur.fetchone()
                    if row:
                        return {
                            'user_id': row[0],
                            'username': row[1],
                            'first_name': row[2],
                            'last_name': row[3],
                            'is_active': row[4],
                            'first_seen': row[5],
                            'last_seen': row[6]
                        }
                    return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
