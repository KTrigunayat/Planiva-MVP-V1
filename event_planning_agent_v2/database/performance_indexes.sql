-- Performance optimization indexes for Event Planning Agent v2
-- These indexes are designed to optimize the most common query patterns

-- ============================================================================
-- VENUE INDEXES
-- ============================================================================

-- Primary search indexes for venues
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_location_city_lower 
ON venues(LOWER(location_city));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_capacity_range 
ON venues(ideal_capacity, max_seating_capacity);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_cost_capacity 
ON venues(rental_cost, ideal_capacity);

-- Composite index for common venue search patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_search_composite 
ON venues(location_city, rental_cost, ideal_capacity) 
WHERE rental_cost IS NOT NULL AND ideal_capacity IS NOT NULL;

-- Area type search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_area_type_lower 
ON venues(LOWER(area_type)) 
WHERE area_type IS NOT NULL;

-- JSONB indexes for flexible attribute searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_attributes_gin 
ON venues USING GIN (attributes);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_decor_options_gin 
ON venues USING GIN (decor_options);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_policies_gin 
ON venues USING GIN (policies);

-- ============================================================================
-- CATERER INDEXES
-- ============================================================================

-- Primary search indexes for caterers
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_location_city_lower 
ON caterers(LOWER(location_city));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_price_range 
ON caterers(min_veg_price, min_non_veg_price);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_capacity 
ON caterers(max_guest_capacity) 
WHERE max_guest_capacity IS NOT NULL;

-- Composite index for common caterer search patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_search_composite 
ON caterers(location_city, min_veg_price, max_guest_capacity) 
WHERE min_veg_price IS NOT NULL;

-- Vegetarian-only filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_veg_only 
ON caterers(veg_only, min_veg_price) 
WHERE veg_only IS NOT NULL;

-- JSONB index for cuisine and attribute searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_attributes_gin 
ON caterers USING GIN (attributes);

-- Specific index for cuisine searches (most common JSONB query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_cuisines 
ON caterers USING GIN ((attributes->'cuisines'));

-- ============================================================================
-- PHOTOGRAPHER INDEXES
-- ============================================================================

-- Primary search indexes for photographers
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_location_city_lower 
ON photographers(LOWER(location_city));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_price 
ON photographers(photo_package_price) 
WHERE photo_package_price IS NOT NULL;

-- Video availability filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_video_price 
ON photographers(video_available, photo_package_price) 
WHERE video_available IS NOT NULL;

-- Composite index for common photographer searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_search_composite 
ON photographers(location_city, photo_package_price, video_available);

-- JSONB index for style and attribute searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_attributes_gin 
ON photographers USING GIN (attributes);

-- Specific index for style searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_styles 
ON photographers USING GIN ((attributes->'styles'));

-- ============================================================================
-- MAKEUP ARTIST INDEXES
-- ============================================================================

-- Primary search indexes for makeup artists
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_makeup_artists_location_city_lower 
ON makeup_artists(LOWER(location_city));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_makeup_artists_price 
ON makeup_artists(bridal_makeup_price) 
WHERE bridal_makeup_price IS NOT NULL;

-- On-site service filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_makeup_artists_onsite_price 
ON makeup_artists(on_site_service, bridal_makeup_price) 
WHERE on_site_service IS NOT NULL;

-- Composite index for common makeup artist searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_makeup_artists_search_composite 
ON makeup_artists(location_city, bridal_makeup_price, on_site_service);

-- JSONB index for style and attribute searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_makeup_artists_attributes_gin 
ON makeup_artists USING GIN (attributes);

-- ============================================================================
-- EVENT PLANS INDEXES (Enhanced)
-- ============================================================================

-- Primary operational indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_client_status 
ON event_plans(client_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_status_created 
ON event_plans(status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_updated_desc 
ON event_plans(updated_at DESC);

-- Workflow state management indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_workflow_state_gin 
ON event_plans USING GIN (workflow_state);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_beam_history_gin 
ON event_plans USING GIN (beam_history);

-- Plan data searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_plan_data_gin 
ON event_plans USING GIN (plan_data);

-- Agent logs for monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_agent_logs_gin 
ON event_plans USING GIN (agent_logs);

-- ============================================================================
-- AGENT PERFORMANCE INDEXES
-- ============================================================================

-- Performance monitoring indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_plan_agent 
ON agent_performance(plan_id, agent_name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_agent_success 
ON agent_performance(agent_name, success, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_execution_time 
ON agent_performance(execution_time_ms DESC) 
WHERE execution_time_ms IS NOT NULL;

-- Time-based performance analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_created_desc 
ON agent_performance(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_task_time 
ON agent_performance(task_name, execution_time_ms);

-- ============================================================================
-- WORKFLOW METRICS INDEXES
-- ============================================================================

-- Workflow performance analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_plan 
ON workflow_metrics(plan_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_score_time 
ON workflow_metrics(final_score DESC, total_execution_time_ms ASC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_iterations 
ON workflow_metrics(total_iterations, combinations_evaluated);

-- Time-based workflow analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_created_desc 
ON workflow_metrics(created_at DESC);

-- Performance optimization analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_performance 
ON workflow_metrics(total_execution_time_ms, final_score, beam_width_used);

-- ============================================================================
-- SYSTEM HEALTH INDEXES
-- ============================================================================

-- System monitoring indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_health_component_status 
ON system_health(component_name, status, checked_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_health_status_time 
ON system_health(status, checked_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_health_response_time 
ON system_health(component_name, response_time_ms) 
WHERE response_time_ms IS NOT NULL;

-- ============================================================================
-- PARTIAL INDEXES FOR COMMON FILTERS
-- ============================================================================

-- Active event plans only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_active 
ON event_plans(client_id, updated_at DESC) 
WHERE status IN ('initialized', 'running', 'vendor_sourcing', 'beam_search', 'client_selection');

-- Failed workflows for debugging
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_failed 
ON event_plans(created_at DESC, client_id) 
WHERE status = 'failed';

-- Successful agent executions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_successful 
ON agent_performance(agent_name, execution_time_ms, created_at DESC) 
WHERE success = true;

-- High-performing workflows
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_metrics_high_performance 
ON workflow_metrics(created_at DESC, total_execution_time_ms) 
WHERE final_score >= 0.8;

-- ============================================================================
-- EXPRESSION INDEXES FOR COMPUTED VALUES
-- ============================================================================

-- Cost per guest calculations for venues
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_cost_per_guest 
ON venues((rental_cost::float / NULLIF(ideal_capacity, 0))) 
WHERE rental_cost IS NOT NULL AND ideal_capacity > 0;

-- Cost efficiency for caterers
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_cost_efficiency 
ON caterers((min_veg_price::float / NULLIF(max_guest_capacity, 0))) 
WHERE min_veg_price IS NOT NULL AND max_guest_capacity > 0;

-- ============================================================================
-- MAINTENANCE COMMANDS
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE venues;
ANALYZE caterers;
ANALYZE photographers;
ANALYZE makeup_artists;
ANALYZE event_plans;
ANALYZE agent_performance;
ANALYZE workflow_metrics;
ANALYZE system_health;

-- ============================================================================
-- INDEX USAGE MONITORING QUERIES
-- ============================================================================

-- Query to monitor index usage (run periodically)
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/

-- Query to find unused indexes (run periodically)
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
  AND idx_scan = 0
ORDER BY tablename, indexname;
*/

-- Query to monitor table sizes and index sizes
/*
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size,
    pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size,
    pg_size_pretty(pg_indexes_size(tablename::regclass)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
*/