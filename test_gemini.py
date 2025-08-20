#!/usr/bin/env python3
"""
Test script for Gemini AI integration in FOB Test Analysis Dashboard
"""

import google.generativeai as genai
import pandas as pd

def test_gemini_connection(api_key):
    """Test Gemini AI connection"""
    try:
        genai.configure(api_key=api_key)
        
        # Try different models with fallback
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
        except:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test prompt
        test_prompt = "Hello! Please respond with 'Gemini AI is working correctly' if you can see this message."
        response = model.generate_content(test_prompt)
        
        print("✅ Gemini AI connection successful!")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {str(e)}")
        return False

def test_fob_analysis_prompt(api_key):
    """Test FOB analysis prompt"""
    try:
        genai.configure(api_key=api_key)
        
        # Try different models with fallback
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
        except:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Sample FOB data
        sample_data = pd.DataFrame({
            'Group': ['Control', 'Treatment 1', 'Treatment 2'],
            'Weight_Change_g': [-2.1, -3.5, -1.8],
            'Percent_Change': [-4.2, -7.0, -3.6],
            'Status': ['Weight Loss', 'Weight Loss', 'Weight Loss']
        })
        
        prompt = f"""
        As a professional animal experiment data analyst, please provide a brief analysis of this FOB test data:
        
        {sample_data.to_string()}
        
        Please provide a 2-3 sentence summary of the weight changes observed.
        """
        
        response = model.generate_content(prompt)
        
        print("✅ FOB analysis prompt test successful!")
        print(f"AI Analysis: {response.text}")
        return True
    except Exception as e:
        print(f"❌ FOB analysis prompt test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini AI Integration for FOB Dashboard")
    print("=" * 50)
    
    # Use stored API key
    api_key = "AIzaSyBkw6dqrouC-Jl8Xe3QiyP83lOQTPdWYmQ"
    
    # Test basic connection
    print("\n1. Testing basic Gemini AI connection...")
    if test_gemini_connection(api_key):
        print("\n2. Testing FOB analysis prompt...")
        test_fob_analysis_prompt(api_key)
    else:
        print("❌ Basic connection failed. Please check your API key.")
    
    print("\n" + "=" * 50)
    print("Test completed!")
