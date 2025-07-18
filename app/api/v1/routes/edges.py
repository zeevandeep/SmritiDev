"""
Edge management routes for API v1.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import edge_repository, node_repository, user_repository, session_repository
from app.services.edge_processor import process_edges_batch
from app.services.edge_chain_processor import process_chain_linked_edges
from app.schemas.schemas import Edge as EdgeSchema, EdgeCreate

router = APIRouter()


@router.get("/", response_model=List[EdgeSchema])
def read_edges(
    user_id: UUID = Query(..., description="ID of the user"),
    skip: int = Query(0, description="Number of edges to skip"),
    limit: int = Query(100, description="Maximum number of edges to return"), 
    db: Session = Depends(get_db)
):
    """
    Get edges for a user.
    
    Args:
        user_id: ID of the user.
        skip: Number of edges to skip.
        limit: Maximum number of edges to return.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return edge_repository.get_user_edges(db, user_id=user_id, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=List[EdgeSchema])
def read_user_edges(
    user_id: UUID,
    skip: int = Query(0, description="Number of edges to skip"),
    limit: int = Query(100, description="Maximum number of edges to return"), 
    db: Session = Depends(get_db)
):
    """
    Get edges for a user using path parameter.
    
    Args:
        user_id: ID of the user.
        skip: Number of edges to skip.
        limit: Maximum number of edges to return.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return edge_repository.get_user_edges(db, user_id=user_id, skip=skip, limit=limit)


@router.get("/node/{node_id}", response_model=List[EdgeSchema])
def read_node_edges(node_id: UUID, db: Session = Depends(get_db)):
    """
    Get edges for a node (both incoming and outgoing).
    
    Args:
        node_id: ID of the node.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the node is not found.
    """
    # Verify that the node exists
    db_node = node_repository.get_node(db, node_id=node_id)
    if db_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return edge_repository.get_node_edges(db, node_id=node_id)


@router.get("/node/{node_id}/from", response_model=List[EdgeSchema])
def read_from_edges(node_id: UUID, db: Session = Depends(get_db)):
    """
    Get edges where the node is the source.
    
    Args:
        node_id: ID of the node.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the node is not found.
    """
    # Verify that the node exists
    db_node = node_repository.get_node(db, node_id=node_id)
    if db_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return edge_repository.get_from_edges(db, node_id=node_id)


@router.get("/node/{node_id}/to", response_model=List[EdgeSchema])
def read_to_edges(node_id: UUID, db: Session = Depends(get_db)):
    """
    Get edges where the node is the target.
    
    Args:
        node_id: ID of the node.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the node is not found.
    """
    # Verify that the node exists
    db_node = node_repository.get_node(db, node_id=node_id)
    if db_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return edge_repository.get_to_edges(db, node_id=node_id)


@router.get("/session/{session_id}", response_model=List[EdgeSchema])
def read_session_edges(session_id: UUID, db: Session = Depends(get_db)):
    """
    Get edges connected to nodes in a session.
    
    Args:
        session_id: ID of the session.
        db: Database session.
        
    Returns:
        List[Edge]: List of edges.
        
    Raises:
        HTTPException: If the session is not found.
    """
    # Verify that the session exists
    db_session = session_repository.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return edge_repository.get_session_edges(db, session_id=session_id)


@router.get("/{edge_id}", response_model=EdgeSchema)
def read_edge(edge_id: UUID, db: Session = Depends(get_db)):
    """
    Get an edge by ID.
    
    Args:
        edge_id: ID of the edge to retrieve.
        db: Database session.
        
    Returns:
        Edge: Edge data.
        
    Raises:
        HTTPException: If the edge is not found.
    """
    db_edge = edge_repository.get_edge(db, edge_id=edge_id)
    if db_edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found"
        )
    return db_edge


@router.post("/", response_model=EdgeSchema, status_code=status.HTTP_201_CREATED)
def create_edge(edge: EdgeCreate, db: Session = Depends(get_db)):
    """
    Create a new edge manually.
    
    This endpoint is primarily for testing/admin purposes.
    In normal operation, edges are created through batch processing.
    
    Args:
        edge: Edge data.
        db: Database session.
        
    Returns:
        Edge: Created edge data.
    """
    # Verify that the nodes exist
    from_node = node_repository.get_node(db, node_id=edge.from_node)
    if from_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source node not found"
        )
    
    to_node = node_repository.get_node(db, node_id=edge.to_node)
    if to_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target node not found"
        )
    
    # Check if the edge already exists
    if edge_repository.check_edge_exists(db, edge.from_node, edge.to_node):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edge already exists between these nodes"
        )
    
    return edge_repository.create_edge(db=db, edge=edge)


@router.post("/process/{user_id}", response_model=Dict[str, Any])
def process_edges(
    user_id: UUID,
    batch_size: int = Query(default=1, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Process a batch of nodes to create edges.
    
    This endpoint finds suitable nodes and creates edges between them
    based on semantic similarity and other criteria.
    
    Args:
        user_id: ID of the user whose nodes will be processed.
        batch_size: Number of source nodes to process in this batch.
        db: Database session.
        
    Returns:
        Dict: Processing statistics.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return process_edges_batch(db, user_id, batch_size)


@router.post("/chain_process/{user_id}", response_model=Dict[str, Any])
def process_chain_linked_edges_endpoint(
    user_id: UUID,
    batch_size: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Process chain-linked edges for a user (Phase 3.25).
    
    This endpoint identifies edges where the 'to_node' of one edge
    is also the 'from_node' of another edge, and marks them as processed.
    This helps identify potential chains of connected thoughts.
    
    Args:
        user_id: ID of the user whose edges will be processed.
        batch_size: Maximum number of user records to process.
        db: Database session.
        
    Returns:
        Dict: Processing statistics.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return process_chain_linked_edges(db, user_id, batch_size)


@router.post("/chain_process", response_model=Dict[str, Any])
def process_all_chain_linked_edges(
    batch_size: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Process chain-linked edges for all users (Phase 3.25).
    
    This endpoint identifies edges where the 'to_node' of one edge
    is also the 'from_node' of another edge, and marks them as processed.
    This helps identify potential chains of connected thoughts.
    
    Args:
        batch_size: Maximum number of user records to process.
        db: Database session.
        
    Returns:
        Dict: Processing statistics.
    """
    return process_chain_linked_edges(db, user_id=None, batch_size=batch_size)