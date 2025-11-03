"""
Database models for the Event Planning Agent system.
Enhanced schema with LangGraph state management and monitoring capabilities.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, 
    ForeignKey, JSON, UUID, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

Base = declarative_base()


class Venue(Base):
    """Venue vendor model"""
    __tablename__ = "venues"
    
    vendor_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    area_name = Column(String(255))
    area_type = Column(String(100))
    location_city = Column(String(100))
    location_full = Column(Text)
    ideal_capacity = Column(Integer)
    max_seating_capacity = Column(Integer)
    rental_cost = Column(Integer)
    min_veg_price = Column(Integer)
    policies = Column(JSONB)
    room_count = Column(Integer)
    room_cost = Column(Integer)
    decor_options = Column(JSONB)
    attributes = Column(JSONB)
    embedding = Column(Text)  # Will be vector(384) if pgvector available
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_venues_city', 'location_city'),
        Index('idx_venues_capacity', 'ideal_capacity'),
        Index('idx_venues_cost', 'rental_cost'),
    )


class Caterer(Base):
    """Caterer vendor model"""
    __tablename__ = "caterers"
    
    vendor_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location_city = Column(String(100))
    location_full = Column(Text)
    veg_only = Column(Boolean)
    min_veg_price = Column(Integer)
    min_non_veg_price = Column(Integer)
    max_guest_capacity = Column(Integer, default=10000)
    attributes = Column(JSONB)
    embedding = Column(Text)  # Will be vector(384) if pgvector available
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_caterers_city', 'location_city'),
        Index('idx_caterers_veg_price', 'min_veg_price'),
        Index('idx_caterers_capacity', 'max_guest_capacity'),
    )


class Photographer(Base):
    """Photographer vendor model"""
    __tablename__ = "photographers"
    
    vendor_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location_city = Column(String(100))
    location_full = Column(Text)
    photo_package_price = Column(Integer)
    video_available = Column(Boolean, default=True)
    attributes = Column(JSONB)
    embedding = Column(Text)  # Will be vector(384) if pgvector available
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_photographers_city', 'location_city'),
        Index('idx_photographers_price', 'photo_package_price'),
    )


class MakeupArtist(Base):
    """Makeup artist vendor model"""
    __tablename__ = "makeup_artists"
    
    vendor_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location_city = Column(String(100))
    location_full = Column(Text)
    bridal_makeup_price = Column(Integer)
    on_site_service = Column(Boolean, default=True)
    attributes = Column(JSONB)
    embedding = Column(Text)  # Will be vector(384) if pgvector available
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_makeup_artists_city', 'location_city'),
        Index('idx_makeup_artists_price', 'bridal_makeup_price'),
    )


class EventPlan(Base):
    """
    Enhanced event plans table with LangGraph state and beam search history.
    Supports workflow state management and monitoring.
    """
    __tablename__ = "event_plans"
    
    plan_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255))
    status = Column(String(50), nullable=False, default='initialized')
    plan_data = Column(JSONB)  # Original client request and plan data
    
    # New: LangGraph workflow state management
    workflow_state = Column(JSONB)  # Current LangGraph state
    beam_history = Column(JSONB)    # Beam search iteration history
    agent_logs = Column(JSONB)      # Agent interaction logs
    
    # Final outputs
    final_blueprint = Column(Text)
    selected_combination = Column(JSONB)  # Final selected vendor combination
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    performance_metrics = relationship("AgentPerformance", back_populates="event_plan")
    workflow_metrics = relationship("WorkflowMetrics", back_populates="event_plan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_event_plans_client', 'client_id'),
        Index('idx_event_plans_status', 'status'),
        Index('idx_event_plans_created', 'created_at'),
    )


class AgentPerformance(Base):
    """
    Agent performance tracking for monitoring and optimization.
    Tracks individual agent task execution metrics.
    """
    __tablename__ = "agent_performance"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey('event_plans.plan_id'), nullable=False)
    agent_name = Column(String(100), nullable=False)
    task_name = Column(String(100), nullable=False)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    input_data = Column(JSONB)   # Task input for debugging
    output_data = Column(JSONB)  # Task output for analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    event_plan = relationship("EventPlan", back_populates="performance_metrics")
    
    # Indexes for performance monitoring queries
    __table_args__ = (
        Index('idx_agent_perf_plan', 'plan_id'),
        Index('idx_agent_perf_agent', 'agent_name'),
        Index('idx_agent_perf_success', 'success'),
        Index('idx_agent_perf_time', 'execution_time_ms'),
        Index('idx_agent_perf_created', 'created_at'),
    )


class WorkflowMetrics(Base):
    """
    Workflow-level metrics for overall system performance monitoring.
    Tracks end-to-end workflow execution statistics.
    """
    __tablename__ = "workflow_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey('event_plans.plan_id'), nullable=False)
    total_iterations = Column(Integer)
    total_execution_time_ms = Column(Integer)
    combinations_evaluated = Column(Integer)
    final_score = Column(Float)
    beam_width_used = Column(Integer, default=3)
    convergence_iteration = Column(Integer)  # Iteration where beam search converged
    error_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    event_plan = relationship("EventPlan", back_populates="workflow_metrics")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_workflow_metrics_plan', 'plan_id'),
        Index('idx_workflow_metrics_score', 'final_score'),
        Index('idx_workflow_metrics_time', 'total_execution_time_ms'),
        Index('idx_workflow_metrics_created', 'created_at'),
    )


class SystemHealth(Base):
    """
    System health monitoring table for tracking overall system status.
    Used by monitoring MCP server for health checks.
    """
    __tablename__ = "system_health"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False)  # e.g., 'database', 'ollama', 'mcp_server'
    status = Column(String(20), nullable=False)  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    health_metadata = Column(JSONB)  # Additional health check data
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for health monitoring
    __table_args__ = (
        Index('idx_system_health_component', 'component_name'),
        Index('idx_system_health_status', 'status'),
        Index('idx_system_health_checked', 'checked_at'),
    )