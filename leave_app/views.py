from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User, LeaveRequest, LeaveTransition
from .serializers import UserSerializer, LeaveRequestSerializer, LeaveTransitionSerializer
from .permissions import IsOwnerOrReadOnly, IsManagerOfEmployee, IsHR, IsManager, IsEmployee
# from .throttles import LeaveRequestRateThrottle  # Removed for now

# Create your views here.

@extend_schema_view(
    list=extend_schema(
        summary="List all users",
        description="Retrieve a list of all users in the system. Access is restricted to authenticated users.",
        responses={200: UserSerializer(many=True)},
        tags=["Users"]
    ),
    retrieve=extend_schema(
        summary="Get user details",
        description="Retrieve detailed information about a specific user.",
        responses={200: UserSerializer},
        tags=["Users"]
    )
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user information.
    
    Provides read-only access to user data including their role and manager information.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

@extend_schema_view(
    list=extend_schema(
        summary="List leave requests",
        description="Retrieve leave requests based on user role. Employees see their own requests, managers see their team's requests, and HR sees all requests.",
        responses={200: LeaveRequestSerializer(many=True)},
        tags=["Leave Requests"]
    ),
    create=extend_schema(
        summary="Create leave request",
        description="Create a new leave request. The request will be created in 'draft' status.",
        request=LeaveRequestSerializer,
        responses={201: LeaveRequestSerializer},
        examples=[
            OpenApiExample(
                "Casual Leave Request",
                value={
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-16",
                    "leave_type": "CL",
                    "reason": "Personal appointment"
                },
                description="Example of a casual leave request"
            ),
            OpenApiExample(
                "Sick Leave Request",
                value={
                    "start_date": "2024-01-20",
                    "end_date": "2024-01-22",
                    "leave_type": "SL",
                    "reason": "Not feeling well, need rest"
                },
                description="Example of a sick leave request"
            )
        ],
        tags=["Leave Requests"]
    ),
    retrieve=extend_schema(
        summary="Get leave request details",
        description="Retrieve detailed information about a specific leave request including all transitions.",
        responses={200: LeaveRequestSerializer},
        tags=["Leave Requests"]
    ),
    update=extend_schema(
        summary="Update leave request",
        description="Update an existing leave request. Only the owner can update their own requests.",
        request=LeaveRequestSerializer,
        responses={200: LeaveRequestSerializer},
        tags=["Leave Requests"]
    ),
    partial_update=extend_schema(
        summary="Partially update leave request",
        description="Partially update an existing leave request. Only the owner can update their own requests.",
        request=LeaveRequestSerializer,
        responses={200: LeaveRequestSerializer},
        tags=["Leave Requests"]
    ),
    destroy=extend_schema(
        summary="Delete leave request",
        description="Delete a leave request. Only the owner can delete their own requests.",
        responses={204: None},
        tags=["Leave Requests"]
    )
)
class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leave requests.
    
    Provides full CRUD operations for leave requests with role-based access control.
    Employees can only access their own requests, managers can access their team's requests,
    and HR can access all requests.
    """
    queryset = LeaveRequest.objects.all().select_related('employee').prefetch_related('transitions')
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    # throttle_classes = [LeaveRequestRateThrottle]  # Disabled for now

    def get_queryset(self):
        user = self.request.user
        if user.role == 'hr':
            return LeaveRequest.objects.all()
        elif user.role == 'manager':
            return LeaveRequest.objects.filter(Q(employee__manager=user) | Q(employee=user))
        return LeaveRequest.objects.filter(employee=user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    def get_permissions(self):
        user = getattr(self.request, 'user', None)
        role = getattr(user, 'role', None)
        if self.action in ['update', 'partial_update', 'destroy', 'cancel']:
            return [IsOwnerOrReadOnly()]
        if self.action in ['approve', 'reject']:
            if role == 'manager':
                return [IsManagerOfEmployee()]
            elif role == 'hr':
                return [IsHR()]
            else:
                return [IsAuthenticated()]  # fallback for schema generation
        return super().get_permissions()

    # def get_throttles(self):
    #     if self.action == 'create':
    #         return [LeaveRequestRateThrottle()]
    #     return super().get_throttles()

    @extend_schema(
        summary="Submit leave request",
        description="Submit a draft leave request for approval. Only draft requests can be submitted.",
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Success Response",
                value={"detail": "Leave request submitted successfully"},
                description="Leave request submitted successfully"
            ),
            OpenApiExample(
                "Error Response",
                value={"detail": "Can only submit draft requests."},
                description="Error when trying to submit non-draft request"
            )
        ],
        tags=["Leave Requests"]
    )
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit a draft leave request for approval.
        
        Changes the status from 'draft' to 'submitted' and creates a transition record.
        """
        leave = self.get_object()
        if leave.status != 'draft':
            return Response({'detail': 'Can only submit draft requests.'}, status=400)
        leave.status = 'submitted'
        leave.save()
        LeaveTransition.objects.create(leave_request=leave, action='submitted', by=request.user)
        return Response(self.get_serializer(leave).data)

    @extend_schema(
        summary="Approve leave request",
        description="Approve a leave request. Managers can approve requests from their team members. HR can approve any request.",
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Manager Approval",
                value={"detail": "Leave request approved by manager"},
                description="Manager approves team member's request"
            ),
            OpenApiExample(
                "HR Approval",
                value={"detail": "Leave request approved by HR"},
                description="HR approves the final request"
            ),
            OpenApiExample(
                "Permission Error",
                value={"detail": "Not allowed."},
                description="User doesn't have permission to approve"
            )
        ],
        tags=["Leave Requests"]
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a leave request.
        
        Managers can approve requests from their team members (status: submitted -> approved_manager).
        HR can approve any submitted request or requests already approved by managers (status: approved_manager -> approved_hr).
        """
        leave = self.get_object()
        if leave.status == 'submitted':
            if request.user.role == 'manager' and leave.employee.manager == request.user:
                leave.status = 'approved_manager'
                leave.save()
                LeaveTransition.objects.create(leave_request=leave, action='approved by manager', by=request.user)
                return Response(self.get_serializer(leave).data)
            elif request.user.role == 'hr':
                leave.status = 'approved_hr'
                leave.save()
                LeaveTransition.objects.create(leave_request=leave, action='approved by HR', by=request.user)
                return Response(self.get_serializer(leave).data)
            else:
                return Response({'detail': 'Not allowed.'}, status=403)
        elif leave.status == 'approved_manager' and request.user.role == 'hr':
            leave.status = 'approved_hr'
            leave.save()
            LeaveTransition.objects.create(leave_request=leave, action='approved by HR', by=request.user)
            return Response(self.get_serializer(leave).data)
        return Response({'detail': 'Invalid status for approval.'}, status=400)

    @extend_schema(
        summary="Reject leave request",
        description="Reject a leave request. Managers and HR can reject submitted or manager-approved requests.",
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Rejection Success",
                value={"detail": "Leave request rejected"},
                description="Leave request successfully rejected"
            ),
            OpenApiExample(
                "Invalid Status",
                value={"detail": "Invalid status or permission for rejection."},
                description="Cannot reject request in current status"
            )
        ],
        tags=["Leave Requests"]
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a leave request.
        
        Managers and HR can reject requests that are in 'submitted' or 'approved_manager' status.
        Changes the status to 'rejected' and creates a transition record.
        """
        leave = self.get_object()
        if leave.status in ['submitted', 'approved_manager']:
            if request.user.role in ['manager', 'hr']:
                leave.status = 'rejected'
                leave.save()
                LeaveTransition.objects.create(leave_request=leave, action='rejected', by=request.user)
                return Response(self.get_serializer(leave).data)
        return Response({'detail': 'Invalid status or permission for rejection.'}, status=400)

    @extend_schema(
        summary="Cancel leave request",
        description="Cancel a leave request. Only the employee who created the request can cancel it.",
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Cancellation Success",
                value={"detail": "Leave request cancelled"},
                description="Leave request successfully cancelled"
            ),
            OpenApiExample(
                "Cannot Cancel",
                value={"detail": "Cannot cancel this request."},
                description="Request cannot be cancelled in current status"
            )
        ],
        tags=["Leave Requests"]
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a leave request.
        
        Employees can cancel their own requests that are not in 'approved_hr', 'rejected', or 'cancelled' status.
        Changes the status to 'cancelled' and creates a transition record.
        """
        leave = self.get_object()
        if leave.status not in ['approved_hr', 'rejected', 'cancelled'] and leave.employee == request.user:
            leave.status = 'cancelled'
            leave.save()
            LeaveTransition.objects.create(leave_request=leave, action='cancelled', by=request.user)
            return Response(self.get_serializer(leave).data)
        return Response({'detail': 'Cannot cancel this request.'}, status=400)

@extend_schema_view(
    list=extend_schema(
        summary="List leave transitions",
        description="Retrieve audit log of all leave request transitions. Access restricted to HR users.",
        responses={200: LeaveTransitionSerializer(many=True)},
        tags=["Audit Log"]
    ),
    retrieve=extend_schema(
        summary="Get transition details",
        description="Retrieve detailed information about a specific leave transition.",
        responses={200: LeaveTransitionSerializer},
        tags=["Audit Log"]
    )
)
class LeaveTransitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing leave transition audit logs.
    
    Provides read-only access to the audit trail of all leave request status changes.
    Access is restricted to HR users only.
    """
    queryset = LeaveTransition.objects.all().select_related('leave_request', 'by')
    serializer_class = LeaveTransitionSerializer
    permission_classes = [IsAuthenticated, IsHR]
