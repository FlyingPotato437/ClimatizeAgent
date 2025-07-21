#!/bin/bash

# 🎬 CLIMATIZE AI PERMIT GENERATOR DEMO
# One command to rule them all!

echo "🎬 Starting Climatize AI Permit Generator Demo..."
echo "Perfect for screen recording and live presentations!"
echo ""

# Check if we're in the right directory
if [ ! -f "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf" ]; then
    echo "❌ Error: Please run this from the project root directory"
    echo "   Make sure you can see the 'agents' folder"
    exit 1
fi

# Activate virtual environment and run demo
source venv/bin/activate
python3 demo.py

# Check if demo was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Demo completed successfully!"
    echo "✅ Perfect for recording and presentations"
    echo "📁 Check the output/permits/ folder for results"
else
    echo ""
    echo "❌ Demo encountered an issue"
    echo "💡 Make sure all dependencies are installed"
fi
