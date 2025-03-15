from datetime import timedelta
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions)

class CapellaClient:
    """
    Client for connecting and managing Couchbase Capella Cluster.
    """
    
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
        # Apply WAN development profile for Capella
        if apply_wan_profile:
            options.apply_profile('wan_development')
        # Configure comprehensive timeout options
        timeout_opts = ClusterTimeoutOptions(
            kv_timeout=timedelta(seconds=timeout_seconds),
            connect_timeout=timedelta(seconds=timeout_seconds + 5),
            query_timeout=timedelta(seconds=timeout_seconds + 10)
        )
        options.timeout_options = timeout_opts
        # Connect to the cluster with proper connection string format
        connection_string = f'couchbases://{self.endpoint}'
        self.cluster = Cluster(connection_string, options)
        # Wait until the cluster is ready
        self.cluster.wait_until_ready(timedelta(seconds=timeout_seconds))
        # Get a reference to our bucket
        self.bucket = self.cluster.bucket(self.bucket_name)

        return self

    def execute_query(self, statement, *args, **kwargs):
        if not self.cluster:
            raise RuntimeError("Not connected to Couchbase. Call connect() first.")
        
        # Execute the query
        result = self.cluster.query(statement, *args, **kwargs)
        
        # Force execution by accessing metadata
        rows = []
        for row in result:
            rows.append(row)
        
        return rows

    def create_embedding_collection(self, scope_name, collection_name):
        """
        Create a new collection to store vector embeddings.
        """
        try:
            create_query = f"""
            CREATE COLLECTION `{self.bucket_name}`.`{scope_name}`.`{collection_name}`
            """
            self.execute_query(create_query)
            print(f"Collection {scope_name}.{collection_name} created or already exists")
            return True
        except Exception as e:
            print(f"Collection was not created, collection may already exist.", e)
            return False
