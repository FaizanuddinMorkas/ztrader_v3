#!/usr/bin/env python3
"""
Test User Tracker Module
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chat.user_tracker import UserTracker


def test_user_tracker():
    """Test user tracker functionality"""
    
    print("=" * 60)
    print("Testing User Tracker Module")
    print("=" * 60)
    
    tracker = UserTracker()
    
    # Test 1: Register test user
    print("\n1. Testing user registration...")
    test_user_id = 999999999
    success = tracker.register_user(
        user_id=test_user_id,
        username="test_user",
        first_name="Test",
        last_name="User",
        is_active=False
    )
    print(f"   ✅ User registered: {success}")
    
    # Test 2: Check if user is active
    print("\n2. Testing user status check...")
    is_active = tracker.is_user_active(test_user_id)
    print(f"   User active: {is_active} (should be False)")
    
    # Test 3: Activate user
    print("\n3. Testing user activation...")
    success = tracker.activate_user(test_user_id)
    print(f"   ✅ User activated: {success}")
    
    # Test 4: Check if user is active now
    print("\n4. Testing user status after activation...")
    is_active = tracker.is_user_active(test_user_id)
    print(f"   User active: {is_active} (should be True)")
    
    # Test 5: Log a query
    print("\n5. Testing query logging...")
    success = tracker.log_query(
        user_id=test_user_id,
        query_type='screen',
        query_text='oversold stocks',
        response_time_ms=1500,
        success=True
    )
    print(f"   ✅ Query logged: {success}")
    
    # Test 6: Get user stats
    print("\n6. Testing user statistics...")
    stats = tracker.get_user_stats(test_user_id)
    if stats:
        print(f"   Total queries: {stats['total_queries']}")
        print(f"   Screen queries: {stats['screen_queries']}")
        print(f"   Avg response time: {stats['avg_response_time']:.0f}ms")
    else:
        print("   No stats yet (materialized view may need refresh)")
    
    # Test 7: Check rate limit
    print("\n7. Testing rate limit check...")
    within_limit = tracker.check_rate_limit(test_user_id, max_per_hour=20)
    print(f"   Within rate limit: {within_limit}")
    
    # Test 8: Get user info
    print("\n8. Testing get user info...")
    user_info = tracker.get_user_info(test_user_id)
    if user_info:
        print(f"   Username: @{user_info['username']}")
        print(f"   Name: {user_info['first_name']} {user_info['last_name']}")
        print(f"   Active: {user_info['is_active']}")
    
    # Test 9: Deactivate user
    print("\n9. Testing user deactivation...")
    success = tracker.deactivate_user(test_user_id)
    print(f"   ✅ User deactivated: {success}")
    
    # Test 10: Get pending users
    print("\n10. Testing get pending users...")
    pending = tracker.get_pending_users()
    print(f"   Pending users count: {len(pending)}")
    if pending:
        print(f"   First pending user: {pending[0]['name']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_user_tracker()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
