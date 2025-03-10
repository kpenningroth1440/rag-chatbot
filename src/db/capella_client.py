from datetime import timedelta
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions,
                               QueryOptions)

class CapellaClient:
    """Client for connecting to Couchbase Capella."""
    
    def __init__(self, endpoint, username, password, bucket_name):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.bucket_name = bucket_name
        self.cluster = None
        self.bucket = None
        
    def connect(self, timeout_seconds=10, apply_wan_profile=True):
        """
        Connect to the Couchbase Capella cluster.
        
        Args:
            timeout_seconds (int): Connection timeout in seconds
            apply_wan_profile (bool): Whether to apply the WAN development profile
            
        Returns:
            CapellaClient: Self for method chaining
        """
        # Set up authentication
        auth = PasswordAuthenticator(self.username, self.password)
        
        # Configure cluster options
        options = ClusterOptions(auth)
        
        # Configure comprehensive timeout options
        timeout_opts = ClusterTimeoutOptions(
            kv_timeout=timedelta(seconds=timeout_seconds),
            connect_timeout=timedelta(seconds=timeout_seconds + 5),
            query_timeout=timedelta(seconds=timeout_seconds + 10)
        )
        options.timeout_options = timeout_opts
        
        # Apply WAN development profile for Capella
        if apply_wan_profile:
            options.apply_profile('wan_development')
        
        # Connect to the cluster with proper connection string format
        connection_string = f'couchbases://{self.endpoint}'
        self.cluster = Cluster(connection_string, options)
        
        # Wait until the cluster is ready
        self.cluster.wait_until_ready(timedelta(seconds=timeout_seconds))
        
        # Get a reference to our bucket
        self.bucket = self.cluster.bucket(self.bucket_name)
        
        # Get a reference to the default collection
        self.default_collection = self.bucket.default_collection()
        
        return self
    
    def query(self, statement, *args, **kwargs):
        """Execute a N1QL query.
        
        Args:
            statement (str): The N1QL query statement
            *args: Additional positional arguments for the query
            **kwargs: Additional keyword arguments for the query
            
        Returns:
            QueryResult: The query result
        """
        if not self.cluster:
            raise RuntimeError("Not connected to Couchbase. Call connect() first.")
            
        return self.cluster.query(statement, *args, **kwargs)
    
    def get_collection(self, scope_name, collection_name):
        """
        Get a reference to a collection within a scope.
        
        Args:
            scope_name (str): Name of the scope
            collection_name (str): Name of the collection
            
        Returns:
            Collection: The requested collection
        """
        if not self.bucket:
            raise ValueError("Not connected to a bucket. Call connect() first.")
        
        return self.bucket.scope(scope_name).collection(collection_name)
    
    def get_default_collection(self):
        """
        Get a reference to the default collection.
        """
        if not self.bucket:
            raise ValueError("Not connected to a bucket. Call connect() first.")
        
        return self.bucket.default_collection()
    
    def scope_query(self, scope_name, query_string, *args, **kwargs):
        if not self.bucket:
            raise ValueError("Not connected to a bucket. Call connect() first.")
        
        scope = self.bucket.scope(scope_name)
        return scope.query(query_string, *args, **kwargs)

    def create_collection(self, scope_name, collection_name):
        """
        Create a new collection if it doesn't exist.
        
        Args:
            scope_name (str): Name of the scope
            collection_name (str): Name of the collection
            
        Returns:
            bool: True if created or already exists
        """
        try:
            # Check if collection exists first
            try:
                self.bucket.scope(scope_name).collection(collection_name)
                print(f"Collection {scope_name}.{collection_name} already exists")
                return True
            except Exception:
                # Collection doesn't exist, create it
                query = f"""
                CREATE COLLECTION `{self.bucket_name}`.`{scope_name}`.`{collection_name}`
                """
                self.cluster.query(query)
                print(f"Created collection {scope_name}.{collection_name}")
                return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False

