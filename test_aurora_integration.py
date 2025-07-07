#!/usr/bin/env python3
"""
Test script to demonstrate Aurora integration in Enhanced Research Agent.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import the services
sys.path.append(str(Path(__file__).parent / "backend"))

from services.ai_service import AIService
from services.enhanced_research_agent import EnhancedResearchAgent

async def test_aurora_integration():
    """Test the Aurora integration in the Enhanced Research Agent."""
    
    print("🧪 Testing Aurora Integration in Enhanced Research Agent")
    print("=" * 60)
    
    # Initialize AI service and research agent
    ai_service = AIService()
    research_agent = EnhancedResearchAgent(ai_service)
    
    # Test Aurora project path
    aurora_project_path = "./agents/aurora_projects/1520_Mission_Blvd_Selman"
    
    print(f"📁 Testing with Aurora project: {aurora_project_path}")
    
    # Test 1: Load Aurora data
    print("\n1️⃣ Testing Aurora data loading...")
    try:
        aurora_data = research_agent.load_aurora_project_data(aurora_project_path)
        if aurora_data:
            print("✅ Aurora data loaded successfully!")
            print(f"   Project: {aurora_data.get('project_description', '').split('Project: ')[1].split('\n')[0] if 'Project: ' in aurora_data.get('project_description', '') else 'Unknown'}")
            print(f"   Address: {aurora_data.get('project_address', 'Unknown')}")
            print(f"   System Size: {aurora_data.get('system_size_ac', 0):.2f} MWac")
        else:
            print("❌ Failed to load Aurora data")
            return
    except Exception as e:
        print(f"❌ Error loading Aurora data: {e}")
        return
    
    # Test 2: Run feasibility screening with Aurora data
    print("\n2️⃣ Testing Aurora-based feasibility screening...")
    try:
        result = await research_agent.run_feasibility_screening_with_aurora(aurora_project_path)
        
        if result.get("status") == "completed_fallback":
            print("⚠️  Analysis completed with fallback (no AI service)")
        else:
            print("✅ Aurora-based feasibility screening completed!")
        
        print(f"   Feasibility Score: {result.get('feasibility_score', 0):.1%}")
        print(f"   Project Name: {result.get('project_name', 'Unknown')}")
        print(f"   System Size: {result.get('system_size_mwac', 0):.2f} MWac")
        print(f"   Executive Summary: {result.get('executive_summary', 'N/A')}")
        
        # Show Aurora-specific data
        aurora_summary = result.get('aurora_data_summary', {})
        if aurora_summary:
            print(f"   Aurora Data Keys: {aurora_summary.get('raw_data_keys', [])}")
        
        # Show recommendations
        recommendations = result.get('development_recommendations', [])
        if recommendations:
            print(f"   Recommendations: {len(recommendations)} items")
            for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                print(f"     {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Error in Aurora-based feasibility screening: {e}")
    
    # Test 3: Compare with regular feasibility screening
    print("\n3️⃣ Comparing with regular feasibility screening...")
    try:
        regular_result = await research_agent.run_feasibility_screening(
            project_name="Test Project",
            address="123 Test St, Test City, CA",
            system_size_kw=1000
        )
        
        print(f"   Regular Score: {regular_result.get('feasibility_score', 0):.1%}")
        print(f"   Aurora Score: {result.get('feasibility_score', 0):.1%}")
        
        if result.get('feasibility_score', 0) > regular_result.get('feasibility_score', 0):
            print("   ✅ Aurora analysis provides more detailed scoring")
        else:
            print("   ℹ️  Both analyses provide similar scoring")
            
    except Exception as e:
        print(f"❌ Error in regular feasibility screening: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Aurora integration test completed!")
    print("\nKey Benefits of Aurora Integration:")
    print("• Detailed technical specifications from Aurora design data")
    print("• Real system sizing and equipment information")
    print("• Energy production estimates")
    print("• Enhanced risk assessment based on actual equipment")
    print("• More accurate feasibility scoring")

if __name__ == "__main__":
    asyncio.run(test_aurora_integration()) 