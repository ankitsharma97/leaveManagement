from rest_framework import serializers
from .models import User, LeaveRequest, LeaveTransition

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Provides user information including role and manager details.
    """
    manager = serializers.StringRelatedField(help_text="Username of the user's manager")
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'manager']
        read_only_fields = ['id', 'username', 'email', 'role', 'manager']

class LeaveTransitionSerializer(serializers.ModelSerializer):
    """
    Serializer for LeaveTransition model.
    
    Provides audit trail information for leave request status changes.
    """
    by = serializers.StringRelatedField(help_text="Username of the user who performed the action")
    
    class Meta:
        model = LeaveTransition
        fields = ['id', 'action', 'by', 'timestamp']
        read_only_fields = ['id', 'action', 'by', 'timestamp']

class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for LeaveRequest model.
    
    Provides comprehensive leave request information including employee details and transition history.
    """
    employee = UserSerializer(read_only=True, help_text="Employee who created the leave request")
    transitions = LeaveTransitionSerializer(many=True, read_only=True, help_text="Audit trail of status changes")
    
    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'start_date', 'end_date', 'leave_type', 'reason', 'status', 'created_at', 'updated_at', 'transitions']
        read_only_fields = ['id', 'employee', 'status', 'created_at', 'updated_at', 'transitions']
    
    def validate(self, data):
        """
        Validate leave request data.
        
        Ensures end_date is not before start_date and validates date ranges.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        
        return data
    
    def validate_start_date(self, value):
        """
        Validate start date is not in the past.
        """
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value 