"""
Enhanced database connection utilities with async support and connection pooling.
Provides both sync and async database connections for the Event Planning Agent system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    Enhanced database connection manager with async support and connection pooling.
    Handles both synchronous and asynchronous database operations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.settings = get_settings()
        self.database_url = database_url or self.settings.get_database_url()
        
        # Optimized connection pool settings from enhanced configuration
        self.pool_size = self.settings.database.pool_size
        self.max_overflow = self.settings.database.max_overflow
        self.pool_timeout = self.settings.database.pool_timeout
        self.pool_recycle = self.settings.database.pool_recycle
        self.pool_pre_ping = self.settings.database.pool_pre_ping
        
        # Initialize engines
        self._sync_engine = None
        self._async_engine = None
        self._sync_session_factory = None
        self._async_session_factory = None
        
        # Enhanced connection health tracking
        self._connection_errors = 0
        self._max_connection_errors = self.settings.database.max_connection_errors
        self._connection_retry_delay = self.settings.database.connection_retry_delay
        
        # Query caching
        self._query_cache = {} if self.settings.database.enable_query_cache else None
        self._query_cache_size = self.settings.database.query_cache_size
        self._query_cache_ttl = self.settings.database.query_cache_ttl
    
    @property
    def sync_engine(self):
        """Get or create synchronous database engine"""
        if self._sync_engine is None:
            self._sync_engine = self._create_sync_engine()
        return self._sync_engine
    
    @property
    def async_engine(self):
        """Get or create asynchronous database engine"""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        return self._async_engine
    
    @property
    def sync_session_factory(self):
        """Get or create synchronous session factory"""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._sync_session_factory
    
    @property
    def async_session_factory(self):
        """Get or create asynchronous session factory"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    def _create_sync_engine(self):
        """Create optimized synchronous database engine with enhanced connection pooling"""
        engine_kwargs = {
            'echo': self.settings.database.echo,
            'echo_pool': self.settings.database.echo_pool,
            'poolclass': QueuePool,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            # Performance optimizations
            'connect_args': {
                'options': f'-c statement_timeout={self.settings.database.statement_timeout}ms '
                          f'-c lock_timeout={self.settings.database.lock_timeout}ms '
                          f'-c idle_in_transaction_session_timeout={self.settings.database.idle_in_transaction_session_timeout}ms',
                'application_name': 'event_planning_agent_v2'
            }
        }
        
        # Use NullPool for SQLite (if used in testing)
        if 'sqlite' in self.database_url:
            engine_kwargs['poolclass'] = NullPool
            engine_kwargs.pop('pool_size', None)
            engine_kwargs.pop('max_overflow', None)
            engine_kwargs.pop('pool_timeout', None)
            engine_kwargs.pop('connect_args', None)
        
        engine = create_engine(self.database_url, **engine_kwargs)
        
        # Add connection event listeners
        self._add_connection_listeners(engine)
        
        logger.info(f"Created optimized sync database engine with pool_size={self.pool_size}, max_overflow={self.max_overflow}")
        return engine
    
    def _create_async_engine(self):
        """Create optimized asynchronous database engine with enhanced connection pooling"""
        # Convert sync URL to async URL
        async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        engine_kwargs = {
            'echo': self.settings.database.echo,
            'echo_pool': self.settings.database.echo_pool,
            'poolclass': QueuePool,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            # Async-specific optimizations
            'connect_args': {
                'server_settings': {
                    'statement_timeout': f'{self.settings.database.statement_timeout}ms',
                    'lock_timeout': f'{self.settings.database.lock_timeout}ms',
                    'idle_in_transaction_session_timeout': f'{self.settings.database.idle_in_transaction_session_timeout}ms',
                    'application_name': 'event_planning_agent_v2_async'
                }
            }
        }
        
        # Use NullPool for SQLite (if used in testing)
        if 'sqlite' in async_url:
            async_url = async_url.replace('postgresql+asyncpg://', 'sqlite+aiosqlite://')
            engine_kwargs['poolclass'] = NullPool
            engine_kwargs.pop('pool_size', None)
            engine_kwargs.pop('max_overflow', None)
            engine_kwargs.pop('pool_timeout', None)
            engine_kwargs.pop('connect_args', None)
        
        engine = create_async_engine(async_url, **engine_kwargs)
        
        logger.info(f"Created optimized async database engine with pool_size={self.pool_size}, max_overflow={self.max_overflow}")
        return engine
    
    def _add_connection_listeners(self, engine):
        """Add connection event listeners for monitoring and health tracking"""
        
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")
            self._connection_errors = 0  # Reset error count on successful connection
        
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("Database connection returned to pool")
        
        @event.listens_for(engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            logger.warning(f"Database connection invalidated: {exception}")
            self._connection_errors += 1
            
            if self._connection_errors >= self._max_connection_errors:
                logger.error(f"Too many connection errors ({self._connection_errors}), may need intervention")
    
    @contextmanager
    def get_sync_session(self) -> Generator[Session, None, None]:
        """
        Get synchronous database session with proper cleanup and error handling
        
        Usage:
            with db_manager.get_sync_session() as session:
                # Use session here
                pass
        """
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get asynchronous database session with proper cleanup and error handling
        
        Usage:
            async with db_manager.get_async_session() as session:
                # Use session here
                pass
        """
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        status = {
            'sync_connection': False,
            'async_connection': False,
            'pool_status': {},
            'error': None
        }
        
        try:
            # Test sync connection
            with self.get_sync_session() as session:
                session.execute("SELECT 1")
                status['sync_connection'] = True
            
            # Get pool status
            pool = self.sync_engine.pool
            status['pool_status'] = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
        except Exception as e:
            status['error'] = str(e)
            logger.error(f"Sync connection test failed: {e}")
        
        try:
            # Test async connection
            async def test_async():
                async with self.get_async_session() as session:
                    await session.execute("SELECT 1")
                return True
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(test_async())
                status['async_connection'] = True
            finally:
                loop.close()
                
        except Exception as e:
            if not status['error']:
                status['error'] = str(e)
            logger.error(f"Async connection test failed: {e}")
        
        return status
    
    def close_connections(self):
        """Close all database connections and dispose engines"""
        try:
            if self._sync_engine:
                self._sync_engine.dispose()
                logger.info("Disposed sync database engine")
            
            if self._async_engine:
                # Async engine disposal needs to be awaited
                async def dispose_async():
                    await self._async_engine.dispose()
                
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(dispose_async())
                except RuntimeError:
                    # No event loop running, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(dispose_async())
                    finally:
                        loop.close()
                
                logger.info("Disposed async database engine")
                
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get detailed connection pool statistics"""
        stats = {
            'connection_errors': self._connection_errors,
            'max_connection_errors': self._max_connection_errors,
            'pool_config': {
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'pool_timeout': self.pool_timeout,
                'pool_recycle': self.pool_recycle
            }
        }
        
        if self._sync_engine:
            pool = self._sync_engine.pool
            stats['sync_pool'] = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
        
        return stats


# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None


def get_connection_manager() -> DatabaseConnectionManager:
    """Get global database connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = DatabaseConnectionManager()
    return _connection_manager


def get_sync_session() -> Generator[Session, None, None]:
    """Convenience function to get sync database session"""
    return get_connection_manager().get_sync_session()


def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Convenience function to get async database session"""
    return get_connection_manager().get_async_session()


def test_database_connection() -> Dict[str, Any]:
    """Test database connection and return status"""
    return get_connection_manager().test_connection()


def close_database_connections():
    """Close all database connections"""
    global _connection_manager
    if _connection_manager:
        _connection_manager.close_connections()
        _connection_manager = None


# Context manager for database operations
@contextmanager
def database_transaction():
    """
    Context manager for database transactions with automatic rollback on error
    
    Usage:
        with database_transaction() as session:
            # Database operations here
            pass
    """
    with get_sync_session() as session:
        yield session


@asynccontextmanager
async def async_database_transaction():
    """
    Async context manager for database transactions with automatic rollback on error
    
    Usage:
        async with async_database_transaction() as session:
            # Database operations here
            pass
    """
    async with get_async_session() as session:
        yield session