"""
Background task handlers for Azure Functions queue processing.
Extracted from the monolithic function_app.py for clean separation of concerns.
"""
import azure.functions as func
import logging
import json
import asyncio
from typing import Dict, Any

# Import services
from services.project_service import ProjectService
from services.helioscope_service import HelioscoperService
from services.battery_service import BatteryService

logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()
helioscope_service = HelioscoperService()
battery_service = BatteryService()

def helioscope_design_engine_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for Helioscope design processing.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing Helioscope design for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(helioscope_service.design_engine(project_id))
            logger.info(f"Completed Helioscope design for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in Helioscope design handler: {str(e)}")
        raise

def battery_sizing_engine_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for battery sizing processing.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing battery sizing for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(battery_service.sizing_engine(project_id))
            logger.info(f"Completed battery sizing for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in battery sizing handler: {str(e)}")
        raise

def interconnection_scorer_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for interconnection scoring.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing interconnection scoring for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # For now, use project service until we create interconnection service
            result = loop.run_until_complete(project_service.process_interconnection_scoring(project_id))
            logger.info(f"Completed interconnection scoring for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in interconnection scoring handler: {str(e)}")
        raise

def permit_matrix_engine_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for permit matrix generation.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing permit matrix for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.generate_permit_matrix(project_id))
            logger.info(f"Completed permit matrix for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in permit matrix handler: {str(e)}")
        raise

def feasibility_and_site_control_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for feasibility analysis and site control document generation.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing feasibility and site control for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.process_feasibility_and_site_control(project_id))
            logger.info(f"Completed feasibility and site control for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in feasibility and site control handler: {str(e)}")
        raise

def capital_stack_generator_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for capital stack generation.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing capital stack for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.generate_capital_stack(project_id))
            logger.info(f"Completed capital stack for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in capital stack handler: {str(e)}")
        raise

def project_packager_and_scorer_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for project packaging and scoring.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing project packaging and scoring for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.package_and_score_project(project_id))
            logger.info(f"Completed project packaging and scoring for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in project packaging and scoring handler: {str(e)}")
        raise

def pro_forma_generator_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for pro forma generation.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing pro forma for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.generate_pro_forma(project_id))
            logger.info(f"Completed pro forma for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in pro forma handler: {str(e)}")
        raise

def site_control_document_generator_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for site control document generation.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing site control documents for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.generate_site_control_documents(project_id))
            logger.info(f"Completed site control documents for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in site control document handler: {str(e)}")
        raise

def eligibility_screener_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for eligibility screening.
    """
    try:
        project_id = msg.get_body().decode('utf-8')
        logger.info(f"Processing eligibility screening for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(project_service.perform_eligibility_screening(project_id))
            logger.info(f"Completed eligibility screening for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in eligibility screening handler: {str(e)}")
        raise

def helioscope_parser_handler(msg: func.QueueMessage) -> None:
    """
    Background handler for parsing Helioscope responses.
    """
    try:
        message_data = json.loads(msg.get_body().decode('utf-8'))
        project_id = message_data.get('project_id')
        helioscope_data = message_data.get('data', {})
        
        logger.info(f"Processing Helioscope parser for project {project_id}")
        
        # Run async service method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                helioscope_service.parse_helioscope_response(project_id, helioscope_data)
            )
            logger.info(f"Completed Helioscope parsing for project {project_id}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in Helioscope parser handler: {str(e)}")
        raise

# Utility functions for handlers

def safe_decode_message(msg: func.QueueMessage) -> Dict[str, Any]:
    """Safely decode queue message to dict."""
    try:
        message_body = msg.get_body().decode('utf-8')
        if message_body.startswith('{'):
            return json.loads(message_body)
        else:
            return {"project_id": message_body}
    except Exception as e:
        logger.error(f"Error decoding message: {str(e)}")
        return {}

def run_async_task(coro):
    """Helper to run async coroutines in sync Azure Functions context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def handle_task_error(task_name: str, project_id: str, error: Exception):
    """Standardized error handling for background tasks."""
    logger.error(f"Error in {task_name} for project {project_id}: {str(error)}")
    
    # Could implement retry logic, error notifications, etc.
    # For now, just log and re-raise
    raise error 