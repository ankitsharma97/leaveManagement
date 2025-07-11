from rest_framework.throttling import UserRateThrottle

# class LeaveRequestRateThrottle(UserRateThrottle):
#     scope = 'leave_request'
#     rate = '3/day'

# Throttling is disabled for development/testing. 